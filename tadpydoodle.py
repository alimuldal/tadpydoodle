import wx
import multiprocessing
from ConfigParser import SafeConfigParser
import os,copy,imp,inspect
import time

import glcanvases as glc; reload(glc)
import gui_elements as gui; reload(gui)

# class DummyTask(object):
# 	scan_hz = 5.
# 	finishtime = 740./5
# 	dt = 89.13
# 	currentframe = 445

__version__ = "0.9a"

class AppThread(multiprocessing.Process):

	# default configuration
	template = {
	# [section]	variable = value
	'window':	{'x_resolution':800,'y_resolution':600,'fullscreen':False,'on_top':True},
	'photodiode':	{'show_photodiode':True,'p_xpos':300.,'p_ypos':100. ,'p_scale':20.},
	'crosshairs':	{'show_crosshairs':True,'c_xpos':300.,'c_ypos':600.,'c_scale':145.},
	'stimulus':	{'show_preview':True,'preview_frequency':5,'log_framerate':False,
			'log_nframes':10000,'run_loop':True,'wait_for_vsync':False,'min_delta_t':1,
			'framerate_window':100}
			}

	# configuration file
	configpath = '~/.tadpydoodlerc'

	# tasks
	taskdir = './tasks'
	run_task = False
	current_task = None
	taskdict = None


	def run(self):
		print "Starting TadPyDoodle v%s" %__version__
		app = wx.PySimpleApp()

		print "Loading configuration..."
		self.loadConfig()

		# setting this environment variable forces vsync on/off (on my
		# Acer laptop that runs Optimus...)
		os.environ.update({'vblank_mode':str(int(self.wait_for_vsync))})

		print "Initialising stimulus window..."
		# we need to pause here, or for some reason the thread stalls
		# when creating the stimulus frame (but only on the
		# workstation?!)
		time.sleep(0.1)
		self.stimframe = wx.Frame(None,-1,size=(self.x_resolution,self.y_resolution),title='Stimulus window')
		self.stimframe.Bind(wx.EVT_CLOSE, self.onClose)
		self.stimcanvas = glc.StimCanvas(self.stimframe,self)
		self.stimframe.Show()

		print "Loading tasks..."
		self.loadTasks()

		print "Initialising controls ..."
		self.controlwindow = gui.ControlWindow(None,self,title='TadPyDoodle')
		self.controlwindow.Bind(wx.EVT_CLOSE, self.onClose)
		self.controlwindow.Show()
		self.controlwindow.SetFocus()

		print "Done"
		app.MainLoop()

	def resetConfig(self,event=None):
		"""
		Resets the configuration to the hard-coded defaults specified in
		'self.template'
		"""
		config = self.template
		for subsect in config.itervalues():
			for option,value in subsect.iteritems():
				self.__setattr__(option,value)

	def loadConfig(self,event=None):
		"""
		Load configuration from a '.tadpydoodlerc' file specified in
		'self.configpath'
		"""

		# create a configparser instance
		parser = SafeConfigParser()

		path = self.configpath.replace('~',os.getenv('HOME'))
		try:
			# try and read read the config file
			parser.readfp(open(path,'r'))
		except IOError:
			# the file probably doesn't exist, never mind
			pass

		# we will use any values that the parser got to update a copy of
		# our dictionary of default values. this way, any values that
		# are missing from the rc file are filled in by the hard-coded
		# template
		config = copy.copy(self.template)
		for sect,subsect in self.template.iteritems():
			if parser.has_section(sect):
				for option,value in subsect.iteritems():
					if parser.has_option(sect,option):
		# use the type of the default value in order to determine how to
		# convert the string that the parser returns
						opt_type = type(value)
						newstr = parser.get(sect,option)
						if opt_type == bool:
							newval = newstr == str(True)
						else:
							newval = opt_type(newstr)
						config[sect][option] = newval

		# since the names of the options in the dictionary are the same
		# as the names of the attributes we need to set, we can just
		# loop through and use self.__setattr__
		for subsect in config.itervalues():
			for option,value in subsect.iteritems():
				self.__setattr__(option,value)

		# force a re-draw of the canvas if it already exists - the
		# display config may have changed
		if hasattr(self,'stimcanvas'):
			self.stimcanvas.recalc_stim_bounds()
			self.stimcanvas.recalc_photo_bounds()
			self.stimcanvas.do_refresh_everything = True

	def saveConfig(self,event=None):
		"""
		Save the current configuration to a '.tadpydoodlerc' file
		specified in 'self.configpath'
		"""
		parser = SafeConfigParser()
		template = self.template

		# update the parser according to the current configuration - use
		# the template to grab the section and option names
		for sect,subsect in template.iteritems():
			parser.add_section(sect)
			for option in subsect.iterkeys():
				newval = self.__getattribute__(option)
				parser.set(sect,option,str(newval))

		# write the new configuration out
		path = self.configpath.replace('~',os.getenv('HOME'))
		parser.write(open(path,'w'))

	def loadTasks(self,event=None):
		"""
		Recursively compile and  load all tasks in 'self.taskdir' and
		its subdirectories. Tasks may be defined in any source file, but
		each must have the '.taskname' attribute in order to be
		recognised. Duplicate tasknames are skipped with a warning.
		"""

		def istask(obj):
			return hasattr(obj,'taskname')

		names = []
		objects = []
		for relpath,_,fullnames in os.walk(self.taskdir):
			for fullname in fullnames:
				fname,ext = os.path.splitext(fullname)
				if ext.lower() == '.py':
					# print os.path.join(relpath,fullname)
					mod = imp.load_source(fname,os.path.join(relpath,fullname))
				# # we don't want to do this if we've made changes to the source files
				# elif ext.lower() == '.pyc':
				# 	mod = imp.load_compiled(fname,os.path.join(relpath,fullname))
				else:
					continue

				for name,obj in inspect.getmembers(mod,predicate=istask):

					if obj.taskname in names:
						print 'Ignoring duplicate of task "%s" in %s' %(obj.taskname,fullname)
					else:
						names.append(obj.taskname)
						objects.append(obj)
				del mod
				
		self.current_task = None
		self.taskdict = dict(zip(names,objects))

	def onClose(self,event):
		if self.stimframe:
			self.stimframe.Destroy()
		if self.controlwindow:
			self.controlwindow.Destroy()
			
if __name__ == '__main__':
	t = AppThread()
	t.run()