import wx
import os
from wx.lib.mixins import listctrl as listmix
import cPickle
import glcanvases as glc; reload(glc)

def seconds2human(secs):
	mins, secs = divmod(secs, 60)
	return '%02d:%05.2f' % (mins, secs)

def get_onsets_and_offsets(boolvec):
	""" get the onset and offset indices for a boolean vector"""
	import numpy as np
	if not np.any(boolvec):
		return np.array([]),np.array([])
	diff = np.diff(boolvec)
	if not np.any(diff > 0):
		onsets = np.array([0])
	else:
		onsets = np.where(diff > 0)[0]
		if boolvec[0]:
			onsets = np.concatenate((np.atleast_1d(0),np.atleast_1d(onsets)))
	if not np.any(diff < 0):
		offsets = np.array([0])
	else:
		offsets = np.where(diff < 0)[0]
		if boolvec[-1]:
			offsets = np.concatenate((np.atleast_1d(offsets),np.atleast_1d(len(boolvec)-1)))
	assert len(onsets) == len(offsets)
	return onsets,offsets

def window_iter(X,win):
	n = X.shape[0]
	for ii in xrange(n):
		start = max((0,ii-(win/2)))
		stop = min((n-1,ii+(win/2)))
		yield X[start:stop]

class AttributeRef(object):
	def __init__(self,masterobj,attrname):
		self.master = masterobj
		self.attrname = attrname

	def get(self):
		return self.master.__getattribute__(self.attrname)

	def set(self,value):
		self.master.__setattr__(self.attrname,value)

class CheckListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, *args, **kwargs):
		wx.ListCtrl.__init__(self, *args, **kwargs)
		listmix.CheckListCtrlMixin.__init__(self)
		listmix.ListCtrlAutoWidthMixin.__init__(self)
		self.setResizeColumn(3)
		self.current_selection = 0

	def SetCurrent(self,index):
		self.current_selection = index
		self.update_selections()

	def update_selections(self):
		for ii in xrange(self.GetItemCount()):
			self.SetItemImage(ii,ii==self.current_selection)

class PlaylistPanel(wx.Panel):

	def __init__(self,parent,master,**kwargs):
		super(PlaylistPanel,self).__init__(parent,**kwargs)

		self.master = master
		self.parent = parent

		# --------------------------------------------------------------
		# task box
		taskbox = wx.StaticBox(self,wx.VERTICAL,label='Tasks')

		# a tree menu of available tasks
		self.task_tree = wx.TreeCtrl(self,-1,style=wx.TR_DEFAULT_STYLE|wx.TR_MULTIPLE|wx.TR_HIDE_ROOT)
		self.populate_tree()
		self.task_tree.Bind(wx.EVT_TREE_SEL_CHANGING,self.onSelectChange)
		self.task_tree.Bind(wx.EVT_LEFT_DCLICK,self.onTreeDoubleClick)

		# playlist controls
		self.startbutton = wx.ToggleButton(self,-1)
		self.startbutton.start = ('Start task',wx.Colour(100,255,100,255))
		self.startbutton.stop = ('Stop task',wx.Colour(255,100,100,255))
		ref = AttributeRef(self.master,'run_task')
		if ref.get():
			l,c = self.startbutton.stop
		else:
			l,c = self.startbutton.start
		self.startbutton.SetLabel(l)
		self.startbutton.SetBackgroundColour(c)
		self.startbutton.SetValue(not ref.get())
		self.startbutton.ref = ref
		self.startbutton.Bind(wx.EVT_TOGGLEBUTTON,self.onRunTask)
		self.nextbutton = wx.Button(self,-1,label='Next')
		self.nextbutton.Bind(wx.EVT_BUTTON,self.Next)
		self.prevbutton = wx.Button(self,-1,label='Previous')
		self.prevbutton.Bind(wx.EVT_BUTTON,self.Previous)

		self.importbutton = wx.Button(self,-1,label='Re-import tasks')
		self.importbutton.Bind(wx.EVT_BUTTON,self.onReload)

		top_sizer = wx.BoxSizer(wx.HORIZONTAL)
		top_sizer.AddMany([(button,1,wx.EXPAND) for button in [self.prevbutton,self.startbutton,self.nextbutton]])

		taskbox_sizer = wx.StaticBoxSizer(taskbox,wx.VERTICAL)
		taskbox_sizer.Add(top_sizer,0,wx.EXPAND|wx.ALL,5)
		taskbox_sizer.Add(self.task_tree,1,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
		taskbox_sizer.Add(self.importbutton,0,wx.EXPAND|wx.ALL,5)

		# --------------------------------------------------------------
		# playlist box

		playbox = wx.StaticBox(self,wx.VERTICAL,label='Playlist')

		# a checklistctrl that contains the playlist
		self.playlist = CheckListCtrl(self,-1,style=wx.LC_SINGLE_SEL|wx.LC_REPORT)
		self.playlist.InsertColumn(0,'')
		self.playlist.InsertColumn(1,'Name')
		self.playlist.InsertColumn(2,'Subclass')
		self.items = []
		self.playlist.Arrange()
		# bind to CheckListCtrl 'event'
		self.playlist.OnCheckItem = self.on_check

		# playlist editing buttons and checkbox controls
		self.clearbutton = wx.Button(self,-1,label='Clear')
		self.clearbutton.Bind(wx.EVT_BUTTON,self.Clear)
		self.loadbutton = wx.Button(self,-1,label='Load')
		self.loadbutton.Bind(wx.EVT_BUTTON,self.Load)
		self.savebutton = wx.Button(self,-1,label='Save')
		self.savebutton.Bind(wx.EVT_BUTTON,self.Save)
		self.loopcheck = wx.CheckBox(self,-1,label='Repeat playlist')
		ref = AttributeRef(self.master,'repeat_playlist')
		self.loopcheck.SetValue(ref.get())
		self.loopcheck.ref = ref
		self.loopcheck.Bind(wx.EVT_CHECKBOX,self.on_loop_check)
		self.autocheck = wx.CheckBox(self,-1,label='Auto start')
		ref = AttributeRef(self.master,'auto_start_tasks')
		self.autocheck.SetValue(ref.get())
		self.autocheck.ref = ref
		self.autocheck.Bind(wx.EVT_CHECKBOX,self.on_auto_check)

		self.upbutton = wx.Button(self,-1,label='Move up')
		self.upbutton.Bind(wx.EVT_BUTTON,self.Up)
		self.downbutton = wx.Button(self,-1,label='Move down')
		self.downbutton.Bind(wx.EVT_BUTTON,self.Down)
		self.rembutton = wx.Button(self,-1,label='Remove task')
		self.rembutton.Bind(wx.EVT_BUTTON,self.Remove)

		edit_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
		buttons = [self.clearbutton,self.loadbutton,self.savebutton]
		edit_sizer1.AddMany([(button,1,wx.EXPAND) for button in buttons])

		edit_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		buttons = [self.loopcheck,self.autocheck]
		edit_sizer2.AddMany([(button,1,wx.EXPAND) for button in buttons])

		edit_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
		buttons = [self.upbutton,self.downbutton,self.rembutton]
		edit_sizer3.AddMany([(button,1,wx.EXPAND) for button in buttons])

		playbox_sizer = wx.StaticBoxSizer(playbox,wx.VERTICAL)
		playbox_sizer.Add(edit_sizer1,0,wx.EXPAND|wx.ALL,5)
		playbox_sizer.Add(self.playlist,1,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
		playbox_sizer.Add(edit_sizer2,0,wx.EXPAND)
		playbox_sizer.Add(edit_sizer3,0,wx.EXPAND|wx.ALL,5)

		master_sizer = wx.BoxSizer(wx.VERTICAL)
		master_sizer.Add(taskbox_sizer,1,wx.EXPAND)
		master_sizer.Add((0,0),0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
		master_sizer.Add(playbox_sizer,1,wx.EXPAND)

		self.SetSizerAndFit(master_sizer)

	#-----------------------------------------------------------------------
	# tree

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

	def onTreeDoubleClick(self,event):
		point = event.GetPosition()
		item = self.task_tree.HitTest(point)[0]
		if not self.task_tree.ItemHasChildren(item):
			taskname = self.task_tree.GetItemText(item)
			if taskname:
				task = self.master.taskdict[taskname]
				self.Append(task)

	def onSelectChange(self,event=None):
		tree = event.GetEventObject()
		newsel = event.GetItem()
		# only allowed to select tasks, not subclasses
		if tree.ItemHasChildren(newsel):
			event.Veto()

	#-----------------------------------------------------------------------
	# playlist

	def onRunTask(self,event=False):
		obj = self.startbutton
		if self.master.current_task is not None:
			running = obj.ref.get()
			# NB the value of toggle changes AFTER this callback executes!
			if running:
				l,c = obj.start
				self.master.stimcanvas.drawcount = 0
				self.master.current_task._reinit()
				# enable the photodiode checkbox while the task is not running
				self.parent.optionpanel.checkboxes['show_photodiode'].Enable(True)

			else:
				l,c = obj.stop
				# grey out the photodiode checkbox while the task is running
				self.parent.optionpanel.checkboxes['show_photodiode'].Enable(False)

			self.master.controlwindow.statuspanel.onUpdate()
			obj.SetValue(not running)
			obj.SetLabel(l)
			obj.SetBackgroundColour(c)
			obj.ref.set(not running)
		else:
			obj.SetValue(True)

		# force a full re-draw
		self.master.stimcanvas.do_refresh_everything = True

	def onReload(self,event):
		if self.master.run_task:
			self.onRunTask()
		self.master.loadTasks()
		self.populate_tree()

	def Append(self,task):
		index = self.playlist.Append(['',task.taskname,task.subclass])
		self.items.append(task)
		if index == 0:
			self.on_check(index)
		auto_resize_cols(self.playlist)

	def Next(self,event=None):
		if not len(self.items): return
		index = self.playlist.current_selection
		n_items = self.playlist.GetItemCount()
		if (index + 1) == n_items:
			if self.master.repeat_playlist:
				index = 0
		else:
			index += 1
		self.on_check(index)

	def Previous(self,event=None):
		if not len(self.items): return
		index = self.playlist.current_selection
		n_items = self.playlist.GetItemCount()
		if index == 0:
			if self.master.repeat_playlist:
				index = (n_items - 1)
		else:
			index -= 1
		self.on_check(index)

	def Remove(self,event=None):
		if not len(self.items): return
		index = self.playlist.GetFirstSelected()
		playing = self.playlist.current_selection
		if index == playing:
			playing = max(0,playing-1)
		elif index < playing:
			playing -= 1

		self.playlist.DeleteItem(index)
		self.items.pop(index)
		if len(self.items):
			self.playlist.Select(0)
			self.on_check(playing)
		else:
			self.master.current_task = None

	def Up(self,event=None):
		if not len(self.items): return
		old = self.playlist.GetFirstSelected()
		n_items = self.playlist.GetItemCount()
		if old == 0:
			if self.master.repeat_playlist:
				new = (n_items - 1)
		else:
			new = old - 1

		playing = self.playlist.current_selection
		if playing == old:
			self.playlist.SetCurrent(new)
		elif playing == new:
			self.playlist.SetCurrent(old)


		self.items[old],self.items[new] = self.items[new],self.items[old]
		self.redraw_playlist()
		self.playlist.Select(new)
		# print self.master.current_task.taskname

	def Down(self,event=None):
		if not len(self.items): return
		old = self.playlist.GetFirstSelected()
		n_items = self.playlist.GetItemCount()
		if (old + 1) == n_items:
			if self.master.repeat_playlist:
				new = 0
		else:
			new = old + 1

		playing = self.playlist.current_selection
		if playing == old:
			self.playlist.SetCurrent(new)
		elif playing == new:
			self.playlist.SetCurrent(old)

		self.items[old],self.items[new] = self.items[new],self.items[old]
		self.redraw_playlist()
		self.playlist.Select(new)
		# print self.master.current_task.taskname

	def Clear(self,event=None):
		self.items = []
		self.redraw_playlist()

	def Load(self,event=None):
		rootdir = self.master.configroot.replace('~',os.getenv('HOME'))
		playlist_dir = os.path.join(rootdir,self.master.playlist_directory)
		if not os.path.exists(playlist_dir):
			os.makedirs(playlist_dir)

		dialog = wx.FileDialog(	None,
					message='Load playlist from path',
					defaultDir=playlist_dir,
					wildcard='*.tadplay',
					style=wx.OPEN
					)
		if dialog.ShowModal() == wx.ID_OK:
			path = dialog.GetPath()
			tadplay = open(path,'r')
			tasks = cPickle.load(tadplay)
			self.items = tasks
			self.playlist.current_selection = 0
			self.redraw_playlist()
			tadplay.close()

	def Save(self,event=None):
		rootdir = self.master.configroot.replace('~',os.getenv('HOME'))
		playlist_dir = os.path.join(rootdir,self.master.playlist_directory)
		if not os.path.exists(playlist_dir):
			os.makedirs(playlist_dir)

		dialog = wx.FileDialog(	None,
					message='Save playlist to path',
					defaultDir=playlist_dir,
					wildcard='*.tadplay',
					style=wx.SAVE
					)
		if dialog.ShowModal() == wx.ID_OK:
			path = dialog.GetPath()
			if path[-8:] != '.tadplay':
				path += '.tadplay'
			tadplay = open(path,'w')
			cPickle.dump(self.items,tadplay)
			tadplay.close()

	def redraw_playlist(self):
		self.playlist.DeleteAllItems()
		for task in self.items:
			self.playlist.Append(['',task.taskname,task.subclass])
		self.playlist.update_selections()

	def on_check(self,index,flag=True):
		if flag:
			task = self.items[index]
			self.set_current_task(task)
		self.playlist.SetCurrent(index)

	def on_loop_check(self,event=None):
		obj = event.GetEventObject()
		obj.ref.set(event.GetSelection())

	def on_auto_check(self,event=None):
		obj = event.GetEventObject()
		obj.ref.set(event.GetSelection())

	def set_current_task(self,task):
		self.master.current_task = task(self.master.stimcanvas)
		self.parent.statuspanel.setTask()
		# force a full re-draw
		self.master.stimcanvas.recalc_stim_bounds()
		self.master.stimcanvas.do_refresh_everything = True
		# print "playing current task: %s" %task.taskname

def auto_resize_cols(listctrl):
	ncols = listctrl.GetColumnCount()
	[listctrl.SetColumnWidth(ii,wx.LIST_AUTOSIZE) for ii in xrange(ncols)]

def walk_branches(tree,root,includeroot=True):
	""" a generator that recursively yields child nodes of a wx.TreeCtrl """
	if includeroot:
		yield root
	item, cookie = tree.GetFirstChild(root)
	while item.IsOk():
		yield item
		if tree.ItemHasChildren(item):
			walk_branches(tree,item)
		item,cookie = tree.GetNextChild(root,cookie)

class StatusPanel(wx.Panel):

	framerate = 0
	totalframes = 0
	finishtime = 0

	def __init__(self,parent,master):
		super(StatusPanel,self).__init__(parent)

		self.master = master
		self.parent = parent

		statbox = wx.StaticBox(self,wx.HORIZONTAL,label='Task status')
		self.progressbar = wx.Gauge(self,-1,range=100)
		timelabel = wx.StaticText(self,-1,'Remaining:',size=(80,-1),style=wx.ALIGN_RIGHT)
		self.time = wx.StaticText(self,-1,'',size=(60,-1),style=wx.ALIGN_LEFT)
		framelabel = wx.StaticText(self,-1,'Scan:',size=(80,-1),style=wx.ALIGN_RIGHT)
		self.frame = wx.StaticText(self,-1,'',size=(60,-1),style=wx.ALIGN_LEFT)
		fpslabel = wx.StaticText(self,-1,'Min FPS:',size=(80,-1),style=wx.ALIGN_RIGHT)
		self.fps = wx.StaticText(self,-1,'',size=(60,-1),style=wx.ALIGN_LEFT)

		txth1 = wx.BoxSizer(wx.HORIZONTAL)
		txth1.Add(timelabel,0,wx.EXPAND|wx.RIGHT,border=5)
		txth1.Add(self.time,0,wx.EXPAND,border=0)

		txth2 = wx.BoxSizer(wx.HORIZONTAL)
		txth2.Add(framelabel,0,wx.EXPAND|wx.RIGHT,border=5)
		txth2.Add(self.frame,0,wx.EXPAND,border=0)

		txth3 = wx.BoxSizer(wx.HORIZONTAL)
		txth3.Add(fpslabel,0,wx.EXPAND|wx.RIGHT,border=5)
		txth3.Add(self.fps,0,wx.EXPAND,border=0)

		vsizer = wx.BoxSizer(wx.VERTICAL)
		vsizer.Add(txth1,1,wx.EXPAND)
		vsizer.Add(txth2,1,wx.EXPAND)
		vsizer.Add(txth3,1,wx.EXPAND)

		hsizer = wx.StaticBoxSizer(statbox,wx.HORIZONTAL)
		hsizer.Add(self.progressbar,1,wx.EXPAND|wx.ALL|wx.CENTER,5)
		hsizer.Add(vsizer,0,wx.ALL|wx.CENTER,5)

		self.setTask()
		self.SetSizerAndFit(hsizer)

	def setTask(self):
		task = self.master.current_task
		if task:
			self.framerate = task.scan_hz
			self.finishtime = task.finishtime
			self.totalframes = task.finishtime*task.scan_hz
			self.onUpdate()

	def onUpdate(self):
		minfps = 1./self.master.stimcanvas.slowestframe
		self.fps.SetLabel("%.2f" %minfps)

		task = self.master.current_task
		if task:
			frame,time = task.currentframe,task.dt
			self.progressbar.SetValue(100*float(frame+1)/self.totalframes)
			self.frame.SetLabel("%i/%i" %(frame+1,self.totalframes))
			self.time.SetLabel(seconds2human(self.finishtime - time))

class AdjustPanel(wx.Panel):

	moveinc = 10
	scaleinc = 5

	def __init__(self,parent,master):
		super(AdjustPanel,self).__init__(parent)

		self.master = master
		self.parent = parent
		# button position controls -------------------------------------
		# button_box = wx.StaticBox(self,wx.VERTICAL,'Position && scale')

		# translation
		names = ['UP','LEFT','RIGHT','DOWN']
		buttons = [wx.Button(self,-1,name,size=(60,-1)) for name in names]
		[bb.Bind(wx.EVT_BUTTON,self.onButton) for bb in buttons]

		# shove them all in a GridBagSizer
		movebag = wx.GridBagSizer(vgap=0,hgap=0)
		u,l,r,d = buttons
		movebag.Add(u,pos=(0,1),span=(1,2),flag=wx.EXPAND)
		movebag.Add(l,pos=(1,0),span=(1,2),flag=wx.EXPAND)
		movebag.Add(r,pos=(1,2),span=(1,2),flag=wx.EXPAND)
		movebag.Add(d,pos=(2,1),span=(1,2),flag=wx.EXPAND)
		# [movebag.AddGrowableRow(rr) for rr in xrange(3)]
		# [movebag.AddGrowableCol(cc) for cc in xrange(4)]
		self.buttons = dict(zip(names,buttons))

		move_vsizer = wx.BoxSizer(wx.VERTICAL)
		move_vsizer.Add((0,0),1,wx.EXPAND)
		move_vsizer.Add(movebag,0)
		move_vsizer.Add((0,0),1,wx.EXPAND)

		# scaling
		names = ['+','-']
		buttons = [wx.Button(self,-1,name,size=(30,-1)) for name in names]
		[bb.Bind(wx.EVT_LEFT_DOWN,self.onButton) for bb in buttons]
		self.buttons.update(dict(zip(names,buttons)))

		# shove them all in a FlexGridSizer
		scaleflex = wx.FlexGridSizer(rows=2,cols=1,vgap=0,hgap=0)
		scaleflex.AddMany([(button,1,wx.EXPAND) for button in buttons])
		# [scaleflex.AddGrowableRow(rr,1) for rr in xrange(2)]

		scale_vsizer = wx.BoxSizer(wx.VERTICAL)
		scale_vsizer.Add((0,0),1,wx.EXPAND)
		scale_vsizer.Add(scaleflex,0)
		scale_vsizer.Add((0,0),1,wx.EXPAND)

		# button_hsizer = wx.StaticBoxSizer(button_box,wx.HORIZONTAL)
		button_hsizer = wx.BoxSizer(wx.HORIZONTAL)
		button_hsizer.Add((0,0),1,wx.EXPAND)
		button_hsizer.Add(move_vsizer,0,wx.ALIGN_CENTER|wx.RIGHT,5)
		button_hsizer.Add(scale_vsizer,0,wx.ALIGN_CENTER|wx.LEFT,5)
		button_hsizer.Add((0,0),1,wx.EXPAND)
		
		# photodiode controls ------------------------------------------
		p_box = wx.StaticBox(self,wx.VERTICAL,label='Photodiode')

		labels = ['X','Y','Scale']
		stext = [wx.StaticText(self,-1,label,size=(60,-1)) for label in labels]

		# radiobutton (select either photodiode or crosshair to be
		# adjusted by the buttons)
		self.p_rb = wx.RadioButton(self,size=(20,-1),style=wx.RB_GROUP)

		# text controls, so you can type in values directly
		attrnames = ['p_xpos','p_ypos','p_scale']
		p_textctls = []
		for nn in attrnames:
			ref = AttributeRef(self.master,nn)
			ctrl = wx.TextCtrl(self,size=(60,-1),value=str(ref.get()),style=wx.TE_PROCESS_ENTER)
			ctrl.Bind(wx.EVT_TEXT_ENTER,self.onText)
			ctrl.ref = ref
			p_textctls.append(ctrl)
		self.p_textctls = dict(zip(attrnames,p_textctls))

		# shove them all in a FlexGridSizer
		p_flex = wx.FlexGridSizer(rows=2,cols=4,vgap=0,hgap=5)
		p_flex.Add((0,0),1,wx.EXPAND)
		p_flex.AddMany([(ll,1,wx.EXPAND) for ll in stext])
		controls = [self.p_rb,] + p_textctls
		p_flex.AddMany([(cc,1,wx.EXPAND) for cc in controls])
		[p_flex.AddGrowableCol(cc,1) for cc in xrange(1,4)]

		# set the static box sizer
		p_box_sizer = wx.StaticBoxSizer(p_box,wx.VERTICAL)
		p_box_sizer.Add(p_flex,1,wx.EXPAND|wx.ALIGN_CENTER|wx.ALL,5)

		# crosshair controls -------------------------------------------
		c_box = wx.StaticBox(self,wx.VERTICAL,label='Crosshairs')

		stext = [wx.StaticText(self,-1,label,size=(60,-1)) for label in labels]

		# radiobutton (select either photodiode or crosshair to be
		# adjusted by the buttons)
		self.c_rb = wx.RadioButton(self,size=(20,-1))

		# text controls, so you can type in values directly
		attrnames = ['c_xpos','c_ypos','c_scale']
		c_textctls = []
		for nn in attrnames:
			ref = AttributeRef(self.master,nn)
			ctrl = wx.TextCtrl(self,size=(60,-1),value=str(ref.get()),style=wx.TE_PROCESS_ENTER)
			ctrl.Bind(wx.EVT_TEXT_ENTER,self.onText)
			ctrl.ref = ref
			c_textctls.append(ctrl)
		self.c_textctls = (dict(zip(attrnames,c_textctls)))

		# shove them all in a FlexGridSizer
		c_flex = wx.FlexGridSizer(rows=2,cols=4,vgap=0,hgap=5)
		c_flex.Add((0,0),1,wx.EXPAND)
		c_flex.AddMany([(ll,1,wx.EXPAND) for ll in stext])
		controls = [self.c_rb,] + c_textctls
		c_flex.AddMany([(cc,1,wx.EXPAND) for cc in controls])
		[c_flex.AddGrowableCol(cc,1) for cc in xrange(1,4)]

		# set the static box sizer
		c_box_sizer = wx.StaticBoxSizer(c_box,wx.VERTICAL)
		c_box_sizer.Add(c_flex,1,wx.EXPAND|wx.ALIGN_CENTER|wx.ALL,5)

		# save/load configuration --------------------------------------
		# names = ['Save Config','Load Config','Default Config']
		names = ['Save Config','Load Config']
		buttons = [wx.Button(self,-1,name) for name in names]
		# save,load,reset = buttons
		save,load = buttons
		save.Bind(wx.EVT_BUTTON,self.master.saveConfig)
		load.Bind(wx.EVT_BUTTON,self.master.loadConfig)
		# reset.Bind(wx.EVT_BUTTON,self.master.resetConfig)

		s_sizer = wx.BoxSizer(wx.HORIZONTAL)
		s_sizer.AddMany([(button,1,wx.EXPAND) for button in buttons])

		# shove everything together ------------------------------------
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.Add(button_hsizer,0,wx.EXPAND|wx.ALL,20)
		sizer.Add((0,0),1,wx.EXPAND)
		sizer.Add(p_box_sizer,0,wx.EXPAND|wx.ALL,5)
		sizer.Add(c_box_sizer,0,wx.EXPAND|wx.ALL,5)
		sizer.Add(s_sizer,0,wx.EXPAND|wx.ALL,5)

		self.SetSizerAndFit(sizer)

	def onButton(self,event):
		caller = event.GetEventObject()

		# which button was pressed?
		for label,button in self.buttons.iteritems():
			if caller.Id == button.Id:
				break

		# are we changing the photodiode or the crosshairs?
		if self.p_rb.GetValue():
			group = self.p_textctls
			prefix = 'p_'
			# recalculate the photodiode bounding box
			recalc = self.master.stimcanvas.recalc_photo_bounds
		else:
			group = self.c_textctls
			prefix = 'c_'
			# recalculate the stimulus area bounding box
			recalc = self.master.stimcanvas.recalc_stim_bounds

		# which direction? how far?
		if label == 'UP':
			control = group[prefix+'ypos']
			delta = self.moveinc
		elif label == 'DOWN':
			control = group[prefix+'ypos']
			delta = -self.moveinc
		elif label == 'LEFT':
			control = group[prefix+'xpos']
			delta = -self.moveinc
		elif label == 'RIGHT':
			control = group[prefix+'xpos']
			delta = +self.moveinc
		elif label == '+':
			control = group[prefix+'scale']
			delta = self.scaleinc
		elif label == '-':
			control = group[prefix+'scale']
			delta = -self.scaleinc

		# reference to the attribute of self.master that we change
		val = control.ref.get()
		val += delta

		# this changes the necessary attribute of self.master
		control.ref.set(val)

		# update the text box string
		control.SetValue(str(val))

		# recalculate bounding box and force a full re-draw
		recalc()
		self.master.stimcanvas.do_refresh_everything = True


	def keyboardNudge(self,event):
		
		if wx.GetKeyState(wx.WXK_F1):
			group = self.p_textctls
			prefix = 'p_'

			# recalculate the photodiode bounding box
			recalc = self.master.stimcanvas.recalc_photo_bounds

		elif wx.GetKeyState(wx.WXK_F2):
			group = self.c_textctls
			prefix = 'c_'

			# recalculate the stimulus area bounding box
			recalc = self.master.stimcanvas.recalc_stim_bounds
		else:
			return

		if wx.GetKeyState(wx.WXK_UP):
			control = group[prefix+'ypos']
			delta = self.moveinc
		elif wx.GetKeyState(wx.WXK_DOWN):
			control = group[prefix+'ypos']
			delta = -self.moveinc
		elif wx.GetKeyState(wx.WXK_LEFT):
			control = group[prefix+'xpos']
			delta = -self.moveinc
		elif wx.GetKeyState(wx.WXK_RIGHT):
			control = group[prefix+'xpos']
			delta = self.moveinc
		elif wx.GetKeyState(wx.WXK_PAGEUP):
			control = group[prefix+'scale']
			delta = self.scaleinc
		elif wx.GetKeyState(wx.WXK_PAGEDOWN):
			control = group[prefix+'scale']
			delta = -self.scaleinc
		else:
			return

		val = control.ref.get()
		val += delta
		control.ref.set(val)
		control.SetValue(str(val))

		# recalculate bounding box and force a full re-draw
		recalc()
		self.master.stimcanvas.do_refresh_everything = True

	def onText(self,event):
		string = event.GetString()
		caller = event.GetEventObject()

		try:
			newval = float(string)
			caller.ref.set(newval)

		except ValueError:
			pass

		caller.SetValue(str(caller.ref.get()))

		# recalculate the bounding boxes & re-draw
		self.master.stimcanvas.recalc_photo_bounds()
		self.master.stimcanvas.recalc_stim_bounds()
		self.master.stimcanvas.do_refresh_everything = True

class LogPanel(wx.Panel):

	def __init__(self,parent,master):
		super(LogPanel,self).__init__(parent)

		self.master = master

		statbox = wx.StaticBox(self,wx.VERTICAL,label='Logging options')

		self.logging_on = wx.CheckBox(self,-1,label='Enable frame logging')
		self.logging_on.Bind(wx.EVT_CHECKBOX,self.onLogging)
		self.logging_on.SetValue(self.master.log_framerate)

		self.plot_button = wx.Button(self,-1,label='Diagnostic plots')
		self.plot_button.Bind(wx.EVT_BUTTON,self.onDiagnosticPlot)

		self.clear_logs = wx.Button(self,-1,label='Clear frame log')
		self.clear_logs.Bind(wx.EVT_BUTTON,self.onClearLogs)

		button_hsizer = wx.BoxSizer(wx.HORIZONTAL)
		button_hsizer.AddMany([(but,1,wx.EXPAND) for but in [self.plot_button,self.clear_logs]])

		statbox_vsizer = wx.StaticBoxSizer(statbox,wx.VERTICAL)
		statbox_vsizer.Add(self.logging_on,0,wx.EXPAND|wx.ALL,5)
		statbox_vsizer.Add(button_hsizer,0,wx.EXPAND|wx.ALL,5)

		self.SetSizerAndFit(statbox_vsizer)

	def onLogging(self,event=None):
		""" toggle logging on and off """
		newval = not(self.master.log_framerate)
		self.master.log_framerate = newval
		self.logging_on.SetValue(newval)

	def onClearLogs(self,event=None):
		""" clear the frame time logs """
		self.master.stimcanvas.frametimes.clear()
		self.master.stimcanvas.stimdraws.clear()
		self.master.stimcanvas.alldraws.clear()

	def onDiagnosticPlot(self,event=None):

		#--------------------------------------------------------------------------------------
		# plot frame times
		import matplotlib
		matplotlib.use('wxagg')
		from matplotlib import pyplot as pp
		from matplotlib import pylab as pl
		import numpy as np
		pl.ion()

		fig1,ax1 = pp.subplots(1,1)
		ax1.hold(True)
		frametimes = np.array(self.master.stimcanvas.frametimes)
		nframes = len(frametimes)
		# ax1.fill_between(range(nframes),[0]*nframes,self.master.stimcanvas.frametimes)
		# ax1.plot(range(nframes),self.master.stimcanvas.frametimes,'-k')
		mean_ft = []
		min_ft = []
		max_ft = []
		win = self.master.framerate_window
		for frames in window_iter(frametimes,win):
			mean_ft.append(np.mean(frames))
			min_ft.append(np.min(frames))
			max_ft.append(np.max(frames))
		mean_ft = np.array(mean_ft)
		min_ft = np.array(min_ft)
		max_ft = np.array(max_ft)


		stimon,stimoff = get_onsets_and_offsets(self.master.stimcanvas.stimdraws)
		if any(stimon) and any(stimoff):
			for ii in xrange(stimon.size):
				if ii == 0:
					ax1.axvspan(stimon[ii],stimoff[ii],alpha=0.5,color='g',label='Stimulus draws')
				else:
					ax1.axvspan(stimon[ii],stimoff[ii],alpha=0.5,color='g',label='__nolegend__')
		photoon,photooff = get_onsets_and_offsets(self.master.stimcanvas.photodraws)			
		if any(photoon) and any(photooff):
			for ii in xrange(photoon.size):
				if ii == 0:
					ax1.axvspan(photoon[ii],photooff[ii],alpha=0.5,color='b',label='Photodiode draws')
				else:
					ax1.axvspan(photoon[ii],photooff[ii],alpha=0.5,color='b',label='__nolegend__')

		alldrawon,alldrawoff = get_onsets_and_offsets(self.master.stimcanvas.alldraws)
		if any(alldrawon) and any(alldrawoff):
			for ii in xrange(alldrawon.size):
				if ii == 0:
					ax1.axvspan(alldrawon[ii],alldrawoff[ii],alpha=0.5,color='r',label='Full-frame draws')
				else:
					ax1.axvspan(alldrawon[ii],alldrawoff[ii],alpha=0.5,color='r',label='__nolegend__')

		ax1.fill_between(np.arange(nframes),min_ft,max_ft,alpha=0.1,facecolor='k',edgecolor='None')
		ax1.plot(np.arange(nframes),frametimes,'-k',alpha=0.3,label='Frame drawtime')
		ax1.plot(np.arange(nframes),mean_ft,'-k',alpha=0.75,label='Mean drawtime',lw=2)
		ax1.axhline(y=self.master.min_delta_t*1E-3,ls='--',c='k',alpha=0.75,label='Minimum drawtime')

		ax1.set_ylim(0,0.02)
		ax1.set_xlabel('Frame #')
		ax1.legend()

		fig1.tight_layout()

		fig2,ax2 = pp.subplots(1,1)

		ax2.hist(frametimes,bins=10**np.linspace(-3.5,-1.5,50))
		ax2.set_xscale('log')
		ax2.set_xlabel('Draw time (sec)')
		ax2.set_ylabel('Frequency')

		pp.show(block=True)
		pl.ioff()

		#--------------------------------------------------------------------------------------


class OptionPanel(wx.Panel):

	def __init__(self,parent,master):
		super(OptionPanel,self).__init__(parent)

		self.parent = parent
		self.master = master

		self.stimframestyle = self.master.stimframe.GetWindowStyle()
		self.controlwindowstyle = self.parent.GetWindowStyle()

		# make sure the initial state of the windows is set
		if self.master.on_top:
			self.master.stimframe.SetWindowStyle(self.stimframestyle|wx.STAY_ON_TOP)
			self.parent.SetWindowStyle(self.controlwindowstyle|wx.STAY_ON_TOP)
		if self.master.fullscreen:
			self.master.stimframe.ShowFullScreen(True,style=wx.FULLSCREEN_ALL)

		check_statbox = wx.StaticBox(self,wx.VERTICAL,label='Display options')

		attrnames = [	'show_photodiode','show_crosshairs',
				'show_preview','fullscreen','on_top',
				'run_loop']#,'wait_for_vsync']
		names = [	'Show photodiode','Show crosshairs',
				'Show preview','Fullscreen','Always on top',
				'Display loop']#,'Wait for vsync']
		events = [self.onPhoto,self.onCross,self.onPreview,self.onFullscreen,self.onTop,self.onDisplayloop]#,self.onVSync]
		checkboxes = []
		for ii in xrange(len(attrnames)):
			ref = AttributeRef(self.master,attrnames[ii])
			ctrl = wx.CheckBox(self,-1,label=names[ii])
			ctrl.ref = ref
			ctrl.Bind(wx.EVT_CHECKBOX,events[ii])
			ctrl.SetValue(ref.get())
			checkboxes.append(ctrl)
		self.checkboxes = dict(zip(attrnames,checkboxes))

		check_sizer = wx.StaticBoxSizer(check_statbox,wx.VERTICAL)
		check_sizer.AddMany([(cc,0,wx.EXPAND|wx.ALL,5) for cc in checkboxes])
		self.SetSizerAndFit(check_sizer)

	def onPhoto(self,event=None):
		caller = self.checkboxes['show_photodiode']
		caller.ref.set(not caller.ref.get())
		caller.SetValue(caller.ref.get())

		# force a full re-draw
		self.master.stimcanvas.do_refresh_everything = True

	def onCross(self,event=None):
		caller = self.checkboxes['show_crosshairs']
		caller.ref.set(not caller.ref.get())
		caller.SetValue(caller.ref.get())

		# force a full re-draw
		self.master.stimcanvas.do_refresh_everything = True

	def onPreview(self,event=None):
		caller = self.checkboxes['show_preview']
		caller.ref.set(not caller.ref.get())
		caller.SetValue(caller.ref.get())

	def onFullscreen(self,event=None):
		caller = self.checkboxes['fullscreen']
		caller.ref.set(not caller.ref.get())
		caller.SetValue(caller.ref.get())
		self.master.stimframe.ShowFullScreen(caller.ref.get(),style=wx.FULLSCREEN_ALL)

	def onTop(self,event=None):
		caller = self.checkboxes['on_top']
		ontop = not caller.ref.get()
		caller.ref.set(ontop)
		caller.SetValue(caller.ref.get())
		if ontop:
			self.master.stimframe.SetWindowStyle(self.stimframestyle|wx.STAY_ON_TOP)
			self.parent.SetWindowStyle(self.controlwindowstyle|wx.STAY_ON_TOP)
		else:
			self.master.stimframe.SetWindowStyle(self.stimframestyle)
			self.parent.SetWindowStyle(self.controlwindowstyle)

	def onDisplayloop(self,event=None):
		caller = self.checkboxes['run_loop']
		caller.ref.set(not caller.ref.get())
		caller.SetValue(caller.ref.get())
		# kick-start the rendering loop by forcing a draw event
		self.master.stimcanvas.onDraw()

class ControlWindow(wx.Frame):
	def __init__(self,parent,master,**kwargs):
		super(ControlWindow,self).__init__(parent,**kwargs)

		self.master = master

		self.previewcanvas = glc.PreviewCanvas(self,self.master.stimcanvas,size=(420,560))
		# self.taskpanel = TaskPanel(self,master)
		self.playlistpanel = PlaylistPanel(self,master)
		self.statuspanel = StatusPanel(self,master)
		self.adjustpanel = AdjustPanel(self,master)
		self.optionpanel = OptionPanel(self,master)
		self.logpanel = LogPanel(self,master)

		left = wx.BoxSizer(wx.VERTICAL)
		left.Add(self.playlistpanel,1,wx.EXPAND)

		right = wx.BoxSizer(wx.VERTICAL)
		right.Add(self.adjustpanel,1,wx.EXPAND)
		right.Add(self.optionpanel,0,wx.EXPAND)
		right.Add(self.logpanel,0,wx.EXPAND)

		middle = wx.BoxSizer(wx.VERTICAL)
		middle.Add(self.previewcanvas,1,wx.SHAPED|wx.ALL|wx.ALIGN_TOP|wx.ALIGN_CENTER_HORIZONTAL ,border=2)
		middle.Add(self.statuspanel,0,wx.EXPAND)

		main = wx.BoxSizer(wx.HORIZONTAL)
		main.Add(left,0,wx.EXPAND)
		main.Add(middle,1,wx.EXPAND)
		main.Add(right,0,wx.EXPAND)

		self.SetSizerAndFit(main)

		# here we create some hotkeys
		# --------------------------------------------------------------
		# generate unqiue IDs for events
		eventnames = 	['run','display','cross','photo','full',
				'nudge','save','load','exit']
		ids = [wx.NewId() for _ in xrange(len(eventnames))]
		eventIDs = dict(zip(eventnames,ids))

		# keyboard shortcuts
		self.Bind(wx.EVT_MENU,self.master.onClose,id=eventIDs['exit'])
		self.Bind(wx.EVT_MENU,self.master.saveConfig,id=eventIDs['save'])
		self.Bind(wx.EVT_MENU,self.master.loadConfig,id=eventIDs['load'])
		self.Bind(wx.EVT_MENU,self.playlistpanel.onRunTask,id=eventIDs['run'])
		self.Bind(wx.EVT_MENU,self.adjustpanel.keyboardNudge,id=eventIDs['nudge'])
		self.Bind(wx.EVT_MENU,self.optionpanel.onDisplayloop,id=eventIDs['display'])
		self.Bind(wx.EVT_MENU,self.optionpanel.onFullscreen,id=eventIDs['full'])
		self.Bind(wx.EVT_MENU,self.optionpanel.onCross,id=eventIDs['cross'])
		self.Bind(wx.EVT_MENU,self.optionpanel.onPhoto,id=eventIDs['photo'])

		accel_tbl = wx.AcceleratorTable([
			(wx.ACCEL_NORMAL,wx.WXK_SPACE,eventIDs['run']),
			(wx.ACCEL_NORMAL,wx.WXK_PAUSE,eventIDs['display']),
			(wx.ACCEL_NORMAL,ord('C'),eventIDs['cross']),
			(wx.ACCEL_NORMAL,ord('P'),eventIDs['photo']),
			(wx.ACCEL_NORMAL,ord('F'),eventIDs['full']),
			(wx.ACCEL_NORMAL,wx.WXK_UP,eventIDs['nudge']),
			(wx.ACCEL_NORMAL,wx.WXK_DOWN,eventIDs['nudge']),
			(wx.ACCEL_NORMAL,wx.WXK_LEFT,eventIDs['nudge']),
			(wx.ACCEL_NORMAL,wx.WXK_RIGHT,eventIDs['nudge']),
			(wx.ACCEL_NORMAL,wx.WXK_PAGEUP,eventIDs['nudge']),
			(wx.ACCEL_NORMAL,wx.WXK_PAGEDOWN,eventIDs['nudge']),
			(wx.ACCEL_CTRL,ord('S'),eventIDs['save']),
			(wx.ACCEL_CTRL,ord('L'),eventIDs['load']),
			(wx.ACCEL_CTRL,ord('Q'),eventIDs['exit'])	])

		self.SetAcceleratorTable(accel_tbl)