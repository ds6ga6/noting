import re

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

