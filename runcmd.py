
import os

def runcmd(command, context, line_in_block, attr):
	context_new = os.popen(command).read()
	return context_new, 0