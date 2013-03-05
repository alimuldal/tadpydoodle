import numpy as np
import time

import OpenGL
# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
import OpenGL.GL as gl

################################################################################
# stimulus primitives

class Bar(object):
	"""
	A simple rectangular bar.

	Parameters:
		width
		height
		color

	Methods:
		draw(self,x,y,z,angle)
	"""

	def __init__(self,width,height,color):
		""" Create the display list """
		self.barlist = gl.glGenLists(1)

		gl.glNewList(self.barlist,gl.GL_COMPILE)

		gl.glColor4f(*color)
		gl.glBegin(gl.GL_QUADS)
		gl.glVertex2f(-width/2., height/2 )
		gl.glVertex2f( width/2., height/2 )
		gl.glVertex2f( width/2.,-height/2 )
		gl.glVertex2f(-width/2.,-height/2 )
		gl.glEnd()
		gl.glEndList()

	def draw(self,x=0.,y=0.,z=0.,angle=0.):
		""" Locally translate/rotate and draw the bar """
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glRotate(angle,0.,0.,1.)
		gl.glCallList(self.barlist)
		gl.glPopMatrix()

class Dot(object):
	"""
	A simple circular dot.

	Parameters:
		radius
		nvertices
		color

	Methods:
		draw(self,x,y,z)
	"""
	def __init__(self,radius,nvertices,color):
		""" Create the display list """
		self.dotlist = gl.glGenLists(1)
		gl.glNewList(self.dotlist,gl.GL_COMPILE)
		gl.glColor4f(*color)
		gl.glBegin(gl.GL_POLYGON)
		for angle in np.linspace(0.,2*np.pi,nvertices,endpoint=False):
			gl.glVertex2f(np.sin(angle)*radius,np.cos(angle)*radius)
		gl.glEnd()
		gl.glEndList()

	def draw(self,x=0.,y=0.,z=0.):
		""" Locally translate and draw the dot """
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glCallList(self.dotlist)
		gl.glPopMatrix()

class CircularStencil(object):
	"""
	A circular stencil with a hard edge. If 'polarity' is 1, the stimulus
	will be drawn only inside the circle, whereas if it is 0 the circle will
	occlude the stimulus.

	N.B. GL_STENCIL_TEST must be enabled in order for it to do anything!

	Parameters:
		radius
		nvertices
		polarity

	Methods:
		draw(self,x=0.,y=0.,z=0.)
	"""
	def __init__(self,radius=1,nvertices=256,polarity=1):

		self.stencillist = gl.glGenLists(1)
		gl.glNewList(self.stencillist,gl.GL_COMPILE)

		# don't write to pixel RGBA values
		gl.glColorMask(0,0,0,0)
		gl.glDisable(gl.GL_DEPTH_TEST)

		# set the stencil buffer to 1 wherever the aperture gets drawn
		# (regardless of what the previous buffer value was)
		gl.glStencilFunc(gl.GL_ALWAYS,1,1)
		gl.glStencilOp(gl.GL_REPLACE,gl.GL_REPLACE,gl.GL_REPLACE)

		gl.glBegin(gl.GL_POLYGON)
		for angle in np.linspace(0.,2*np.pi,nvertices,endpoint=False):
			gl.glVertex2f(np.sin(angle)*radius,np.cos(angle)*radius)
		gl.glEnd()

		# re-enable writing to RGBA values
		gl.glColorMask(1,1,1,1)

		# we will draw our current stimulus only where the stencil
		# buffer is equal to 1
		gl.glStencilFunc(gl.GL_EQUAL,polarity,1)
		gl.glStencilOp(gl.GL_KEEP,gl.GL_KEEP,gl.GL_KEEP)

		gl.glEndList()

	def draw(self,x=0,y=0,z=0):
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glCallList(self.stencillist)
		gl.glPopMatrix()

class RectangularStencil(object):
	"""
	A rectangular stencil with a hard edge. If 'polarity' is 1, the stimulus
	will be drawn only inside the rectangle, whereas if it is 0 the
	rectangle will occlude the stimulus.

	N.B. GL_STENCIL_TEST must be enabled in order for it to do anything!

	Parameters:
		rect (x0,y0,w,h)
		polarity

	Methods:
		draw(self,x=0.,y=0.,z=0.,angle=0)
	"""

	def __init__(self,rect=(0,0,0.5,0.5),polarity=1):

		self.stencillist = gl.glGenLists(1)
		gl.glNewList(self.stencillist,gl.GL_COMPILE)

		# don't write to pixel RGBA values
		gl.glColorMask(0,0,0,0)
		gl.glDisable(gl.GL_DEPTH_TEST)

		# set the stencil buffer to 1 wherever the aperture gets drawn
		# (regardless of what the previous buffer value was)
		gl.glStencilFunc(gl.GL_ALWAYS,1,1)
		gl.glStencilOp(gl.GL_REPLACE,gl.GL_REPLACE,gl.GL_REPLACE)

		x0,y0,w,h = rect
		gl.glBegin(gl.GL_QUADS)
		gl.glVertex2f(x0  ,y0  )
		gl.glVertex2f(x0  ,y0+h)
		gl.glVertex2f(x0+w,y0+h)
		gl.glVertex2f(x0+w,y0  )
		gl.glEnd()

		# re-enable writing to RGBA values
		gl.glColorMask(1,1,1,1)

		# we will draw our current stimulus only where the stencil
		# buffer is equal to 1
		gl.glStencilFunc(gl.GL_EQUAL,polarity,1)
		gl.glStencilOp(gl.GL_KEEP,gl.GL_KEEP,gl.GL_KEEP)

		gl.glEndList()

	def draw(self,x=0,y=0,z=0,angle=0):
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glRotate(angle,0,0,1)
		gl.glCallList(self.stencillist)
		gl.glPopMatrix()

class GratingTextureQuad(object):
	"""
	A 1D luminance-format textured quad with wrapping, ideal for displaying
	repetative contrast gratings.

	Parameters:
		texdata
		color
		rect

	Methods:
		draw(self,translation,rotation)
	"""
	def __init__(self,texdata,color=(1.,1.,1.,1.),rect=(-1.,-1.,1.,1.)):

		# build the texture
		self.texture = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_1D,self.texture)
		gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
		gl.glTexParameterf( gl.GL_TEXTURE_1D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT )
		gl.glTexParameterf( gl.GL_TEXTURE_1D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT )
		gl.glTexParameterf( gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
		gl.glTexParameterf( gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )

		gl.glTexImage1D(gl.GL_TEXTURE_1D,0,gl.GL_LUMINANCE16,len(texdata),
				0,gl.GL_LUMINANCE,gl.GL_FLOAT,texdata)

		# display list for the texture
		# --------------------------------------------------------------
		texlist = gl.glGenLists(1)
		gl.glNewList(texlist, gl.GL_COMPILE)

		# we use blending so that the opacity of the grating varies
		# sinusoidally
		gl.glEnable(gl.GL_BLEND)
		gl.glBlendFunc(gl.GL_SRC_ALPHA,gl.GL_DST_ALPHA)
		gl.glEnable(gl.GL_TEXTURE_1D)

		x0,y0,x1,y1 = rect

		gl.glColor4f(*color)
		gl.glBegin( gl.GL_QUADS )
		gl.glTexCoord2f( 0, 1 );	gl.glVertex2f( x0, y1 )
		gl.glTexCoord2f( 0, 0 );	gl.glVertex2f( x0, y0 )
		gl.glTexCoord2f( 1, 0 );	gl.glVertex2f( x1, y0 )
		gl.glTexCoord2f( 1, 1 );	gl.glVertex2f( x1, y1 )
		gl.glEnd()

		gl.glDisable(gl.GL_TEXTURE_1D)
		gl.glDisable(gl.GL_BLEND)

		gl.glEndList()
		# --------------------------------------------------------------

		self.texlist = texlist

	def draw(self,offset=0.,angle=0.):
		"""
		Translate/rotate within texture coordinates, then draw the
		texture
		"""

		# we work on the texture matrix for now
		gl.glMatrixMode(gl.GL_TEXTURE)

		gl.glBindTexture(gl.GL_TEXTURE_1D,self.texture)
		gl.glLoadIdentity()
		gl.glTranslate(offset,0,0)
		gl.glRotatef(angle,0,0,1)
		gl.glCallList(self.texlist)

		# we go BACK to the modelview matrix for safety!!!
		gl.glMatrixMode(gl.GL_MODELVIEW)

################################################################################
# base class
class Task(object):
	"""
	Base class for all tasks.

	Implements:
		__init__
		reinit
		_buildtimes
		_buildparamsdict
		display
	"""

	currentframe = -1
	dt = -1
	background_color = (0.,0.,0.,0.)

	# this determines the ratio of width:height for the stimulus box
	area_aspect = 1.

	def __init__(self,canvas=None):
		self.canvas = canvas
		self.starttime = -1
		self._buildtimes()
		self._buildstim()
		pass

	def reinit(self):
		"""
		return the stimulus to its initialised state
		"""
		self.starttime = -1
		self._buildtimes()
		self._buildstim()

	def _buildtimes(self):
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
		# theoretical scan times
		self.frametimes = np.arange(0.,self.finishtime,1./self.scan_hz)
		self.nframes = self.frametimes.size


		self.actualstimtimes = -1.*np.ones(self.nstim)
		self.finished = False
		self.dt = -1.
		self.currentframe = 0
		self.currentstim = -1
		self.on_flag = False
		self.off_flag = False
		self.stim_on_last_frame = False
		pass

	def _buildparamsdict(self):
		"""
		build the 'paramsdict' by introspection
		"""
		pd = {}
		for name in dir(self):
			if not name.startswith('_'):
				pd.update({name:self.__getattr__(name)})
		self.paramsdict = pd

	def display(self):
		"""
		draw the current stimulus state to the glcanvas
		"""

		# we haven't started yet
		if self.starttime == -1:
			self.starttime = time.time()

		# we've started
		else:
			# time since we started
			dt = time.time() - self.starttime

			# if we haven't displayed all of the frames yet...
			if self.currentframe < (self.nframes -1):
				# ...and if it's after the start time of the next frame...
				if dt > self.frametimes[self.currentframe+1]:
					# ...increment the current frame
					self.currentframe += 1

			# if it's before the end of the photodiode on period,
			# set the photodiode trigger on
			new_photodiode_state = (
				dt < (self.frametimes[self.currentframe] + self.photodiodeontime)
				)

			if self.canvas.master.show_photodiode != new_photodiode_state:
				self.canvas.do_refresh_photodiode = True

			self.canvas.master.show_photodiode = new_photodiode_state
	
			timeafterinitblank = dt - self.initblanktime

			# check if we're still in the initial blank period
			if timeafterinitblank > 0.:

				# if we haven't displayed all of the stimuli yet...
				if self.currentstim < (self.nstim -1):
					# ...and if it's after the start time of the next stimulus...
					if timeafterinitblank > self.ontimes[self.currentstim+1]:
						# ...increment the current stimulus
						self.currentstim += 1
						self.on_flag = False

				# are we in the "ON" period of this stimulus?
				if timeafterinitblank < self.offtimes[self.currentstim]:

					# do the actual drawing
					#-------------------------------
					self.drawstim()
					#-------------------------------

					# force a re-draw of the stimulus area
					self.canvas.do_refresh_stimbox = True

					# make sure we re-draw one more time after the stimulus has
					# finished
					self.stim_on_last_frame = True

					# get the actual ON time for this stimulus
					if not self.on_flag:
						recalcdt = time.time() - self.starttime
						self.actualstimtimes[self.currentstim] = recalcdt
						self.on_flag = True

				elif self.stim_on_last_frame:
					self.canvas.do_refresh_stimbox = True
					self.stim_on_last_frame = False

				if dt > self.finishtime and not self.finished:
					self.finished = True

					print 	"Task '%s' finished: %s" %(self.taskname,time.asctime())
					print 	"Absolute difference between " \
						"theoretical and actual stimulus times:"
					print np.abs(self.actualstimtimes - self.theoreticalstimtimes)

					if not self.canvas.master.auto_start_tasks:
						self.canvas.master.controlwindow.playlistpanel.onRunTask()
					self.canvas.master.controlwindow.playlistpanel.Next()

			self.dt = dt

################################################################################
# stimulus subtypes

class DotFlash(Task):
	"""
	Base class for flashing dot stimuli

	Implements:
		_buildstim
		drawstim
	"""

	# the name of the stimulus subclass
	subclass = 'dot_flash'

	def _buildstim(self):
		"""
		construct a generic flashing dot stimulus
		"""
		# generate a random permutation of x,y coordinates
		nx,ny = self.gridshape
		x_vals = np.linspace(-1,1,nx)*self.gridlim[0]
		y_vals = np.linspace(-1,1,ny)*self.gridlim[1]*self.area_aspect
		x, y = np.meshgrid(x_vals,y_vals)
		self.xpos = x.flatten()[self.permutation]
		self.ypos = y.flatten()[self.permutation]

		# create the dot
		self.dot = Dot(self.radius,self.nvertices,self.dot_color)
		pass

	def drawstim(self):
		# draw the dot in the current position
		self.dot.draw(self.xpos[self.currentstim],self.ypos[self.currentstim],0.)


class DriftingBar(Task):
	"""
	Base class for drifting bar stimuli

	Implements:
		_make_orientations
		_buildstim
		_drawstim

	"""

	subclass = 'drifting_bar'

	def _make_orientations(self):
		# start/stop positions and angles for each bar sweep - these are
		# all good!
		angle = np.linspace(0.,360.,len(self.fullpermutation),endpoint=False)

		# do the shuffling
		angle = angle[self.permutation]
		self.angle = angle
		self.startx = np.array([np.cos(np.deg2rad(aa)) for aa in self.angle])
		self.starty = np.array([np.sin(np.deg2rad(aa)) for aa in self.angle])
		self.stopx = np.array([np.cos(np.deg2rad(aa)+np.pi) for aa in self.angle])
		self.stopy = np.array([np.sin(np.deg2rad(aa)+np.pi) for aa in self.angle])

	def _buildstim(self):
		self._make_orientations()
		self.bar = Bar(				width=self.bar_width,
							height=self.bar_height,
							color=self.bar_color)


		self.aperture = CircularStencil(	radius=self.aperture_radius,
							nvertices=self.aperture_nvertices,
							polarity=1)

	def drawstim(self):

		# get the current bar position
		bar_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
		frac = bar_dt/(self.offtimes[self.currentstim] - self.ontimes[self.currentstim])
		x = self.startx[self.currentstim] + frac*(self.stopx[self.currentstim]-self.startx[self.currentstim])
		y = self.starty[self.currentstim] + frac*(self.stopy[self.currentstim]-self.starty[self.currentstim])

		# enable stencil test, draw the aperture to the stencil buffer
		gl.glEnable(gl.GL_STENCIL_TEST)
		self.aperture.draw()

		# draw the bar, disable stencil test
		self.bar.draw(x,y,0,self.angle[self.currentstim])
		gl.glDisable(gl.GL_STENCIL_TEST)

		pass

class OccludedDriftingBar(DriftingBar):
	"""
	Drifting bar with a rectangular 'occluded' region

	Implements:
		_make_orientations
		_buildstim
	"""
	subclass = 'occluded_drifting_bar'

	def _make_orientations(self):
		angle = np.repeat(self.angles,self.full_nstim//2)
		self.angle = angle[self.permutation]
		self.startx = np.array([np.cos(np.deg2rad(aa)) for aa in self.angle])
		self.starty = np.array([np.sin(np.deg2rad(aa)) for aa in self.angle])*self.area_aspect
		self.stopx = np.array([np.cos(np.deg2rad(aa)+np.pi) for aa in self.angle])
		self.stopy = np.array([np.sin(np.deg2rad(aa)+np.pi) for aa in self.angle])*self.area_aspect

	def _buildstim(self):
		self._make_orientations()
		self.bar = Bar(				width=self.bar_width,
							height=self.bar_height,
							color=self.bar_color)

		self.aperture = RectangularStencil(	rect=self.rect_occlusion,
							polarity=0)

class DriftingGrating(Task):
	"""
	Base class for drifting texture stimuli

	Implements:
		_make_orientations
		_buildstim
		_drawstim
	"""

	def _make_orientations(self):

		# orientations copied from drifting bar stimuli
		orientation = np.linspace(0.,360.,len(self.fullpermutation),endpoint=False)

		# do the shuffling
		orientation = orientation[self.permutation]
		self.orientation = orientation

		pass

	def _buildstim(self):
		self._make_orientations()
		self._make_grating()
		self._texture = GratingTextureQuad(	texdata=self._texdata,
							color=self.grating_color,
							rect=(-1,-1,1,1))

		self._aperture = CircularStencil(	radius=self.aperture_radius,
							nvertices=self.aperture_nvertices,
							polarity=1)

		pass

	def drawstim(self):

		# update the current phase angle
		on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
		self._phase = on_dt*self.grating_speed

		# enable stencil test, draw the aperture to the stencil buffer
		gl.glEnable(gl.GL_STENCIL_TEST)
		self._aperture.draw()

		# draw the texture, disable stencil test
		self._texture.draw(	offset=self._phase,
					angle=self.orientation[self.currentstim])
		gl.glDisable(gl.GL_STENCIL_TEST)

		pass

class DriftingSinusoid(DriftingGrating):
	"""
	Base class for drifting bar stimuli

	Implements:
		_make_grating
	"""

	subclass = 'drifting_sinusoid'

	def _make_grating(self):

		phaseangle = np.linspace(0,2*np.pi*self.n_cycles,self.grating_nsamples)

		# the texture values should be float32, range [0.,1.]
		sinusoid = self.grating_amplitude*np.float32((np.sin(phaseangle)+1.)/2.)

		self._texdata = sinusoid
		self._phase = 0

class DriftingSquarewave(DriftingGrating):
	"""
	Base class for drifting bar stimuli

	Implements:
		_make_grating
	"""

	subclass = 'drifting_squarewave'

	def _make_grating(self):

		t = np.arange(self.grating_nsamples)
		period =  self.grating_nsamples // self.n_cycles
		squarewave = np.float32(rectwave(t,period,self.duty_cycle))
		squarewave = (squarewave-0.5)*self.grating_amplitude + 0.5
		self._texdata = squarewave
		self._phase = 0

def rectwave(t,period=10,duty_cycle=0.5):
	return (t % period) <= period*duty_cycle