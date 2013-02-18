import wx

from wx.lib.agw import ultimatelistctrl as ULC
# from wx.lib.mixins import listctrl as listmix

class PlaylistPanel(wx.Panel):

	def __init__(self,parent,master,**kwargs):
		super(PlaylistPanel,self).__init__(parent,**kwargs)

		self.master = master

		# a tree menu of available tasks
		self.task_tree = wx.TreeCtrl(self,-1,style=wx.TR_DEFAULT_STYLE|wx.TR_MULTIPLE|wx.TR_HIDE_ROOT)
		self.populate_tree()
		self.task_tree.Bind(wx.EVT_TREE_SEL_CHANGING,self.onSelectChange)
		self.task_tree.Bind(wx.EVT_LEFT_DCLICK,self.onTreeDoubleClick)

		# a list box that contains the selected tasks
		# self.playlist_box = wx.ListCtrl(self,-1,style=wx.LC_SINGLE_SEL|wx.LC_REPORT)
		self.playlist_box = ULC.UltimateListCtrl(self,-1,agwStyle=ULC.ULC_REPORT|ULC.ULC_HAS_VARIABLE_ROW_HEIGHT|ULC.ULC_MASK_CHECK)

		# for ii,paramname in enumerate(['Name','Subclass','']):
		# 	self.playlist_box.InsertColumn(ii,paramname,width=wx.LIST_AUTOSIZE)


		entry = ULC.UltimateListItem()
		entry._mask = ULC.ULC_MASK_CHECK
		entry._kind = 2
		entry._text = ''

		entry = ULC.UltimateListItem()
		entry._mask = ULC.ULC_MASK_CHECK
		entry._kind = 2
		entry._text = 'Playing?'


		self.playlist_box.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.onPlaylistActivated)
		self.playlist_box.Bind(wx.EVT_LEFT_DOWN,self.onPlaylistClick)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.task_tree,1,wx.EXPAND)
		sizer.Add(self.playlist_box,1,wx.EXPAND)

		self.SetSizerAndFit(sizer)

	def populate_tree(self):
		taskdict = self.master.taskdict

		# clear any existing items from the tree
		self.task_tree.DeleteAllItems()

		# we hide this
		root = self.task_tree.AddRoot('tasks')

		# arrange the task names according to their 'subclasses'. we use a dict
		# to keep track of the existing branches.
		hierarchy = {}
		for name,obj in taskdict.iteritems():

			# if it's a new subclass, create a new tree branch
			if not hierarchy.has_key(obj.subclass):
				newbranch = self.task_tree.AppendItem(root,obj.subclass)
				hierarchy.update({obj.subclass:newbranch})

			# add the task name to an existing branch
			self.task_tree.AppendItem(hierarchy[obj.subclass],name)

		# sort each tree branch recursively
		for item in walk_branches(self.task_tree,root):
			self.task_tree.SortChildren(item)

	def append_to_playlist(self,task):

		item_no = self.playlist_box.GetItemCount()

		self.playlist_box.InsertStringItem(item_no,task.taskname)
		self.playlist_box.SetStringItem(item_no,1,task.subclass)
		# self.playlist_box.SetItemWindow(item_no,col=2,wnd=rb,expand=True)

		auto_resize_cols(self.playlist_box)
		self.master.task_queue.append(task)

		if self.master.current_task is None:
			self.set_current_task(task)

	def set_current_task(self,task):
		self.master.current_task = task

	def onTreeDoubleClick(self,event):
		point = event.GetPosition()
		item = self.task_tree.HitTest(point)[0]
		if not self.task_tree.ItemHasChildren(item):
			taskname = self.task_tree.GetItemText(item)
			task = self.master.taskdict[taskname]
			self.append_to_playlist(task)

	def onPlaylistActivated(self,event=None):
		taskname = event.GetText()
		idx = event.GetIndex()
		task = self.master.taskdict[taskname]
		self.set_current_task(task)

	def onPlaylistClick(self,event):
		"""
		we intercept single left clicks so that we can select items
		either by doubleclick or programatically
		"""
		pass
		# point = event.GetPosition()
		# item = self.playlist_box.HitTest(point)[0]
		# print self.playlist_box.GetItemText(item)


	def onSelectChange(self,event=None):
		tree = event.GetEventObject()
		newsel = event.GetItem()
		# only allowed to select tasks, not subclasses
		if tree.ItemHasChildren(newsel):
			event.Veto()

def auto_resize_cols(listctrl):
	ncols = listctrl.GetColumnCount()
	[listctrl.SetColumnWidth(ii,wx.LIST_AUTOSIZE) for ii in xrange(ncols)]

def walk_branches(tree,root):
	""" a generator that recursively yields child nodes of a wx.TreeCtrl """
	item, cookie = tree.GetFirstChild(root)
	while item.IsOk():
		yield item
		if tree.ItemHasChildren(item):
			walk_branches(tree,item)
		item,cookie = tree.GetNextChild(root,cookie)

class FakeMaster(object):

	def __init__(self):

		tasknames = ['dotflash1','dotflash2','grating1','grating2']
		subclasses = ['flashing_dot','flashing_dot','drifting_grating','drifting_grating']

		self.taskdict = {}
		for ii in xrange(len(tasknames)):
			faketask = FakeTask(tasknames[ii],subclasses[ii])
			self.taskdict.update({tasknames[ii]:faketask})

		self.task_queue = []
		self.current_task = None

class FakeTask(object):
	def __init__(self,name,subclass):
		self.taskname = name
		self.subclass = subclass

def run():
	app = wx.App()
	fakemaster = FakeMaster()
	fr = wx.Frame(None)
	playlist = PlaylistPanel(fr,fakemaster)
	fr.Show()
	app.MainLoop()

if __name__ == '__main__':
	run()