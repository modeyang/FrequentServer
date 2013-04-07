# import time
import time, datetime

# mapping to database
class userData(object):
	def __init__(self, name, action, content, updated):
		super(userData, self).__init__()
		self.name = name
		self.modify = False
		self.New = False
		self.updated = updated
		self.action = action
		self.content = content
		self.counts = 1

	def __str__(self):
		return '%s: %s : %s : %s : %s'%(datetime.datetime.fromtimestamp(self.updated),\
		 		self.name, self.action, self.content, self.counts)
