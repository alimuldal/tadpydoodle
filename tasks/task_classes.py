import numpy as np
import time

import OpenGL
# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False

import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut

################################################################################
# base classes
class Task(object):
	currentframe = -1
	dt = -1
	background_color = (0.,0.,0.,0.)

	"""
	Base class for all tasks.

	Implements:
		__init__
		reinit
		buildtimes
	"""

	def __init__(self,canvas):
		self.canvas = canvas
		self.starttime = -1
		self.buildtimes()
		self.buildstim()
		pass

	def reinit(self):
		"""
		return the stimulus to its initialised state
		"""
		self.starttime = -1
		self.buildtimes()
		self.buildstim()

	def buildtimes(self):
		""" 
		get the theoretical stimulus and photodiode times, initialise
		the actual times
		"""

		# theoretical stimulus times
		self.ontimes = self.interval*np.arange(self.nstim)
		self.offtimes = self.ontimes + self.on_duration
		self.theoreticalstimtimes = (self.initblanktime + self.ontimes)
		self.finishtime = 	  self.initblanktime \
					+ self.finalblanktime \
					+ self.ontimes[-1] 
		self.actualstimtimes = -1.*np.ones(self.nstim)
		self.stimflags = np.zeros(self.nstim)
		self.finished = False
		self.dt = -1.

		# theoretical scan times
		self.frametimes = np.arange(0.,self.finishtime,1./self.scan_hz)
		self.nframes = self.frametimes.size
		self.currentframe = 0
		pass

################################################################################
# stimulus subtypes

class DotFlashTask(Task):

	"""
	Base class for flashing dot stimuli

	Inherited from Task:
		__init__
		reinit
		buildtimes

	Implements:
		buildstim
		buildparamsdict
		display
	"""

	# the name of the stimulus subclass
	subclass = 'dot_flash'

	def buildstim(self):
		"""
		construct a generic 6x6 flashing dot stimulus
		"""
		# generate a random permutation of x,y coordinates
		nx,ny = self.gridshape
		x_vals = np.linspace(-1,1,nx)*self.gridlim[0]
		y_vals = np.linspace(-1,1,ny)*self.gridlim[1]
		x, y = np.meshgrid(x_vals,y_vals)
		self.xpos = x.flatten()[self.permutation]
		self.ypos = y.flatten()[self.permutation]

		# build an OpenGL display list for the dot
		self.dot = gl.glGenLists(1)
		gl.glNewList(self.dot,gl.GL_COMPILE)
		gl.glColor4f(*self.dot_color)
		gl.glBegin(gl.GL_POLYGON)
		for angle in np.linspace(0.,2*np.pi,self.nvertices,endpoint=False):
			gl.glVertex3f(np.sin(angle)*self.radius,np.cos(angle)*self.radius,0.)
		gl.glEnd()
		gl.glEndList()
		pass

	def buildparamsdict(self):

		pd = {}
		
		# do the standard stuff first:
		pd.update({'taskname':self.taskname})
		pd.update({'subclass':self.subclass})
		pd.update({'initblanktime':self.initblanktime})
		pd.update({'finalblanktime':self.finalblanktime})
		pd.update({'ontimes':self.ontimes})
		pd.update({'stimtimes':self.theoreticalstimtimes})
		pd.update({'finishtime':self.finishtime})
		pd.update({'scan_hz':self.scan_hz})

		# stim specific stuff
		pd.update({'offtimes':self.offtimes})
		pd.update({'radius':self.radius})
		pd.update({'dot_color':self.dot_color})
		pd.update({'permutation':self.permutation})
		pd.update({'xpos':self.xpos})
		pd.update({'ypos':self.ypos})

		self.paramsdict = pd
	def display(self):
		"""
		draw the current frame to the glcanvas
		"""

		# we haven't started yet
		if self.starttime == -1:
			self.starttime = time.time()

		# we've started
		else:
			dt = time.time() - self.starttime

			if self.currentframe < self.nframes -1:
				if dt > self.frametimes[self.currentframe+1]:
					self.currentframe += 1

			self.canvas.master.show_photodiode = (
				(dt > self.frametimes[self.currentframe]) and \
				(dt < self.frametimes[self.currentframe] + self.photodiodeontime)
			)
	
			timeafterinitblank = dt - self.initblanktime

			# check if we're in init blank
			if timeafterinitblank >= 0.:

				stimidx = np.where(self.ontimes < timeafterinitblank)[0]

				# have we reached a stimulus on time yet?
				if stimidx.size:

					stimidx = stimidx[-1]

					# are we done showing this stimulus yet?
					if timeafterinitblank < self.offtimes[stimidx]:

						# draw the dot
						gl.glTranslate(self.xpos[stimidx],self.ypos[stimidx],0.)
						gl.glCallList(self.dot)
					else:
						pass

					if not self.stimflags[stimidx]:
						recalcdt = time.time() - self.starttime
						self.actualstimtimes[stimidx] = recalcdt
						self.stimflags[stimidx] = 1.

				# we're still in init blank mode
				else:
					pass

			if dt > self.finishtime and not self.finished:
				self.finished = True

				print 	"Task '%s' finished: %s" %(self.taskname,time.asctime())
				print 	"Absolute difference between" \
					"theoretical and actual stimulus times:"
				print np.abs(self.actualstimtimes - self.theoreticalstimtimes)

			self.dt = dt


################################################################################
# derived stimulus classes

# 	NB: stimuli that are actually displayed in td2 must have a 'taskname'

class dotflash1(DotFlashTask):
	"""
	This stimulus should be identical to the original in
	oldtasks/dotflash1.py
	"""

	# this is how the stimulus will appear in td2's menu
	taskname = 'dotflash1'

	# stimulus-specific parameters
	gridshape = (6,6)
	gridlim = (0.9,0.9)
	dot_color = (1.,1.,1.,1.)
	radius = 0.075
	nvertices = 64

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 10.
	interval = 8
	on_duration = 1.

	# photodiode triggering parameters
	scan_hz = 5.
	photodiodeontime = 0.075

	#-----------------------------------------------------------------------
	# random permutation of all positions copied directly from an instance
	# of the original dotflash1.task
	fullpermutation = np.array([
		31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28,
		32,  8, 13,  5, 17, 14,  7, 26,  1, 12, 25, 24,  6, 23,
		 4, 18, 21, 19,  9, 34,  3,  0])
	#-----------------------------------------------------------------------

	# take the first 18 of the full 36 positions
	nstim = 18
	permutation = fullpermutation[:nstim]

class dotflash2(dotflash1):
	"""
	This stimulus should be identical to the original in
	oldtasks/dotflash2.py
	"""
	taskname = 'dotflash2'
	permutation = dotflash1.fullpermutation[dotflash1.nstim:]

class dotflash1_2hz(dotflash1):
	"""
	This stimulus should be identical to the original in
	oldtasks/dotflash1_2hz.py
	"""
	taskname = 'dotflash1_2hz'
	scan_hz = 2.

class dotflash2_2hz(dotflash2):
	"""
	This stimulus should be identical to the original in
	oldtasks/dotflash2_2hz.py
	"""
	taskname = 'dotflash2_2hz'
	scan_hz = 2.

class dotflash1_inverted(dotflash1):
	background_color = (1.,1.,1.,1.)
	dot_color = (0.,0.,0.,1.)

class dotflash2_inverted(dotflash2):
	background_color = (1.,1.,1.,1.)
	dot_color = (0.,0.,0.,1.)
