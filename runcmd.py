
import os

def runcmd(command, context, attr):
	context_new = os.popen(command).read()
	return context_new