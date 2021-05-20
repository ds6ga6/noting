import os
import sys
import json
import re
import importlib

#region
# import re

"""
describ: match nest regex
example: 
match_nest("123(((())))456", '(', ')') return 2, (3, 11)
match_nest("(()", '(', ')') return 1, (0, 1)
match_nest("))", '(', ')') return 0, None

sp: 为了配合 noting，对较标准的 match_nest 做了一些对应的修改
"""
def sp_match_nest(pattern_beg, pattern_end, string, sp_pattern_beg=None):
	if(sp_pattern_beg==None):
		sp_pattern_beg = pattern_beg
	# match pattern_beg
	match = re.search(sp_pattern_beg, string)
	if(not match):
		return 0, None
	pos_beg = match.start()
	pos_end = match.end()
	# match pattern_end
	pattern_beg_or_end = '(' + pattern_beg + ')|(' + pattern_end + ')'
	pos = pos_end
	while(True):
		match = re.search(pattern_beg_or_end, string[pos:])
		if(match == None): # 意味着没有 end
			sign = 1
			break
		temp = match.string[match.start():match.end()]
		if(re.match(pattern_beg, temp)): # 意味着遇到了嵌套结构
			nu, pos_temp = sp_match_nest(pattern_beg, pattern_end, string[pos:]) # nu 只是占位用
			pos += pos_temp[1]
		else:  # 意味找到了 end
			assert re.match(pattern_end, temp)
			pos_end = pos + match.end()
			sign = 2
			break
	return sign, (pos_beg, pos_end)



def printInColor(text, color):
	colorDict = {
		'black'		: '30',
		'red'		: '31',
		'green'		: '32',
		'yellow'	: '33',
		'blue'		: '34',
		'purple'	: '35',
		'white'		: '37',
		'default'	: '38'
	}
	print("\033[" + colorDict[color] + "m" + text + "\033[0m")

def writeSecure(text, filepath, backupload="noting\\temp\\"):
	with open(filepath, 'rb') as f:
		data = f.read()
	with open(backupload + filepath.split('\\')[-1], 'wb') as f:
		f.write(data)
	with open(filepath, 'w', encoding='utf-8') as f:
		f.write(text)
#endregion

COMMAND_DICT = "noting\\modedict.json"

sp_pattern_beg = "\n<!-- #region --> #(.*) (!{1,2})(.*)"
pattern_beg = "\n<!-- #region -->"
string_end = "\n<!-- #endregion -->"

# get args of where you are when launch
assert len(sys.argv) == 13
args = {
	"workspaceFolder"			: sys.argv[1],	#	/home/your-username/your-project
	"workspaceFolderBasename"	: sys.argv[2],	#	your-project
	"file"						: sys.argv[3],	#	/home/your-username/your-project/folder/file.ext
	"fileWorkspaceFolder"		: sys.argv[4],	#	/home/your-username/your-project
	"relativeFile"				: sys.argv[5],	#	folder/file.ext
	"relativeFileDirname"		: sys.argv[6],	#	folder
	"fileBasename"				: sys.argv[7],	#	file.ext
	"fileBasenameNoExtension"	: sys.argv[8],	#	file
	"fileDirname"				: sys.argv[9],	#	/home/your-username/your-project/folder
	"fileExtname"				: sys.argv[10],	#	.ext
	"lineNumber"				: int(sys.argv[11]),
	"pathSeparator"				: sys.argv[12]	#	/ on macOS or linux, \\ on Windows
}

# get modedict from COMMAND_DICT
with open(COMMAND_DICT, 'r', encoding='utf-8') as f:
	modedict = json.load(f)


def exec_block(block, sign=2, line_in_block=-1):
	assert re.match(sp_pattern_beg, block)
	# get mode, command, iscontinued
	match = re.search(sp_pattern_beg, block)
	mode, iscontinued, command = match.groups()
	if(iscontinued=='!'):
		iscontinued = False
	else:
		assert iscontinued == '!!'
		iscontinued = True
	# get context
	context = block[match.end():-len(string_end)]
	if(context[0]=='\n'):
		context = context[:-1]
	# get attributes
	attr = {}
	if(sign==2): # block 中有参数
		pos = match.end() + 1
		pattern_attr = "^@([^\n:]*):([^\n]*)\n"
		while(True):
			match = re.search(pattern_attr, block[pos:])
			if(match==None):
				break
			attr[match.groups()[0]] = match.groups()[1]
			pos += match.end()
	# traverse mode->command
	if(mode not in modedict.keys()):
		text = 'Error: "' + mode + '" isnot a mode in modedict.json'
		printInColor(text, "red")
		exit(1)
	cmddict = modedict[mode]
	isrun = False
	for key in cmddict.keys():
		if(re.match(key, command)):
			file = cmddict[key]["file"]
			func_name = cmddict[key]["func"]
			lib = importlib.import_module(file)
			func = getattr(lib, func_name)
			context_new, line_in_block_new = func(command, context, line_in_block, attr)
			isrun = True
			break
	if(not isrun):
		if("default" in cmddict.keys()):
			lib = importlib.import_module(cmddict["default"]["file"])
			func = getattr(lib, cmddict["default"]["func"])
			context_new, line_in_block_new = func(command, context, line_in_block, attr)
		else:
			text = 'Error: "' + command + '" is not a command in "' + mode + '" mode'
			printInColor(text, "red")
			exit(1)
	# turn context into block
	block_new = "\n<!-- #region --> #" + mode + " "
	if(iscontinued):
		block_new += '!!'
	block_new += command
	for key in attr.keys():
		block_new += "\n@" + key + ": " + attr[key]
	block_new += '\n' + context_new + string_end
	return block_new, line_in_block_new


if(__name__=="__main__"):
	line_current = args["lineNumber"] # number of line where user is editting
	with open("main.md", "r", encoding='utf-8') as f:
		data_new = ""
		data_old = f.read()
	
	while(True):
		sign, pos = sp_match_nest(pattern_beg, string_end, data_old, sp_pattern_beg=sp_pattern_beg)
		if(sign==0): # 没有需要执行的命令了
			data_new += data_old
			break
		else:
			# 确定 line_in_block
			line_num1 = data_new.count('\n') + data_old.count('\n', 0, pos[0])
			line_num2 = line_num1 + data_old.count('\n', pos[0], pos[1])
			if(line_num1 < line_current < line_num2):
				line_in_block = line_current - line_num1
			else:
				line_in_block = -1
			# run exec_block
			block_new, line_in_block_new = exec_block(data_old[pos[0]:pos[1]], sign=1, line_in_block=line_in_block)
			# 这里虽然 block 大部分还在 data_old 中，但开头的 '\n' 给 data_new 了，开头的 block 也就不会再被匹配了
			data_new += data_old[:pos[0]] + '\n'
			data_old = block_new[1:] + data_old[pos[1]:]
			# 计算新的 line_current
			if(line_in_block == -1): # line_current 
				line_current = line_num1 + line_in_block_new
			elif(line_current >= line_num2):
				line_current += block_new.count('\n') - (line_num2 - line_num1)
	
	# 修改 main.md，并打开到 line_current 行
	writeSecure(data_new, "main.md")
	with open("main.md", 'w', encoding='utf-8') as f:
		f.write(data_new)
	os.system("code main.md:" + str(line_current))
