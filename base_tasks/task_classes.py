"""
Copyright 2013 Alistair Muldal & Timothy Lillicrap

Tadpydoodle is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Tadpydoodle is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Tadpydoodle.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import time

import OpenGL
# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
import OpenGL.GL as gl

"""
################################################################################
Conventions for stimulus orientation
################################################################################

1) Since the projector is oriented vertically, the main stimulus canvas (and the
   framebuffer) are rotated 90deg clockwise relative to the preview canvas.

      - When you are designing a stimulus, x and y coordinates should correspond
	to what you see on the preview canvas (and to what actually gets
	projected onto the screen), rather than as they appear on the stimulus
	canvas.

      - Transforming the coordinates from preview --> stimulus canvas should be
	handled within the _drawstim() method of the stimulus and *nowhere
	else*.

2) It is important to bear in mind that what the animal *actually* sees is a 
   mirror image of what the projector displays (i.e. flipped in x), because the 
   animal sees the 'back' surface of the translucent screen.

      - This should be corrected for at the point of analysis, *not* in the
	stimulus class itself - all coordinates, orientations etc. should look
	'correct' on the preview canvas.
"""

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

	def __init__(self,width,height):
		""" Create the display list """
		self.barlist = gl.glGenLists(1)

		gl.glNewList(self.barlist,gl.GL_COMPILE)
		gl.glBegin(gl.GL_QUADS)
		gl.glVertex2f(-width/2., height/2 )
		gl.glVertex2f( width/2., height/2 )
		gl.glVertex2f( width/2.,-height/2 )
		gl.glVertex2f(-width/2.,-height/2 )
		gl.glEnd()
		gl.glEndList()

	def draw(self,x=0.,y=0.,z=0.,angle=0.,color=(1.,1.,1.,1.)):
		""" Locally translate/rotate and draw the bar """
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glRotate(angle,0.,0.,1.)
		gl.glColor4f(*color)
		gl.glCallList(self.barlist)
		gl.glPopMatrix()

def get_current_bar_xy(frac,angle,radius=1,origin=(0,0)):
	"""
	Convenience function to get the current x/y position based on the
	fraction of the sweep completed and the angle of the sweep.

	The optional 'radius' and 'origin' parameters control the length of the
	sweep and the centre point that it passes through respectively.
	"""
	x0,y0 = origin
	rads = np.deg2rad(angle)
	sx = x0+radius*np.cos(rads+np.pi)
	sy = y0+radius*np.sin(rads+np.pi)
	ex = x0+radius*np.cos(rads)
	ey = y0+radius*np.sin(rads)
	return sx + frac*(ex-sx),sy + frac*(ey-sy)

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
	def __init__(self,radius,nvertices):
		""" Create the display list """
		self.dotlist = gl.glGenLists(1)
		gl.glNewList(self.dotlist,gl.GL_COMPILE)
		gl.glBegin(gl.GL_POLYGON)
		for angle in np.linspace(0.,2*np.pi,nvertices,endpoint=False):
			gl.glVertex2f(np.sin(angle)*radius,np.cos(angle)*radius)
		gl.glEnd()
		gl.glEndList()

	def draw(self,x=0.,y=0.,z=0.,color=(1.,1.,1.,1.)):
		""" Locally translate and draw the dot """
		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glPushMatrix()
		gl.glTranslate(x,y,z)
		gl.glColor4f(*color)
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

	def __init__(self,width,height,polarity=1):

		self.stencillist = gl.glGenLists(1)
		gl.glNewList(self.stencillist,gl.GL_COMPILE)

		# don't write to pixel RGBA values
		gl.glColorMask(0,0,0,0)
		gl.glDisable(gl.GL_DEPTH_TEST)

		# set the stencil buffer to 1 wherever the aperture gets drawn
		# (regardless of what the previous buffer value was)
		gl.glStencilFunc(gl.GL_ALWAYS,1,1)
		gl.glStencilOp(gl.GL_REPLACE,gl.GL_REPLACE,gl.GL_REPLACE)

		gl.glBegin(gl.GL_QUADS)
		gl.glVertex2f(-width/2.      ,-height/2.       )
		gl.glVertex2f(-width/2.      ,-height/2.+height)
		gl.glVertex2f(-width/2.+width,-height/2.+height)
		gl.glVertex2f(-width/2.+width,-height/2.       )
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
	def __init__(self,texdata,rect=(-1.,-1.,1.,1.)):

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

	def draw(self,offset=0.,angle=0.,color=(1.,1.,1.,1.)):
		"""
		Translate/rotate within texture coordinates, then draw the
		texture
		"""

		# we work on the texture matrix for now
		gl.glMatrixMode(gl.GL_TEXTURE)
		gl.glPushMatrix()
		gl.glLoadIdentity()

		gl.glBindTexture(gl.GL_TEXTURE_1D,self.texture)

		# we move in the opposite direction in texture coords
		gl.glTranslate(-offset,0,0)
		gl.glRotatef(-angle,0,0,1)
		gl.glColor4f(*color)
		gl.glCallList(self.texlist)

		# we pop and go BACK to the modelview matrix for safety!!!
		gl.glPopMatrix()
		gl.glMatrixMode(gl.GL_MODELVIEW)

################################################################################
# base class
class Task(object):
	"""
	Base class for all tasks.

	Implements:
		__init__
		_reinit
		_buildtimes
		_buildparamsdict
		_display
	"""

	currentframe = -1
	dt = -1
	background_color = (0.,0.,0.,0.)

	# this determines the ratio of width:height for the stimulus box
	area_aspect = 1.

	def __init__(self,canvas=None):
		self._canvas = canvas
		self.starttime = -1
		self._buildtimes()
		self._buildstim()
		self._buildparamsdict()
		pass

	def _reinit(self):
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
					+ self.offtimes[-1] 
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
				pd.update({name:self.__getattribute__(name)})
		self.paramsdict = pd

	def _display(self):
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
			if self.currentframe < (self.nframes - 1):
				# ...and if it's after the start time of the next frame...
				if dt > self.frametimes[self.currentframe + 1]:
					# ...increment the current frame
					self.currentframe += 1

			# if it's before the end of the photodiode on period,
			# set the photodiode trigger on
			new_photodiode_state = (
				dt < (self.frametimes[self.currentframe] + self.photodiodeontime)
				)
			self._canvas.do_refresh_photodiode = (self._canvas.master.show_photodiode != new_photodiode_state)
			self._canvas.master.show_photodiode = new_photodiode_state
	
			timeafterinitblank = dt - self.initblanktime

			# check if we're still in the initial blank period
			if timeafterinitblank > 0.:

				# if we haven't displayed all of the stimuli yet...
				if self.currentstim < (self.nstim - 1):
					# ...and if it's after the start time of the next stimulus...
					if timeafterinitblank > self.ontimes[self.currentstim + 1]:
						# ...increment the current stimulus
						self.currentstim += 1
						self.on_flag = False

				# are we in the "ON" period of this stimulus?
				if timeafterinitblank < self.offtimes[self.currentstim]:

					# do the actual drawing
					#-------------------------------
					self._drawstim()
					#-------------------------------

					# force a re-draw of the stimulus area
					self._canvas.do_refresh_stimbox = True

					# make sure we re-draw one more time
					# after the stimulus has finished
					self.stim_on_last_frame = True

					# get the actual ON time for this
					# stimulus
					if not self.on_flag:
						recalcdt = time.time() - self.starttime
						self.actualstimtimes[self.currentstim] = recalcdt
						self.on_flag = True

				elif self.stim_on_last_frame:
					self._canvas.do_refresh_stimbox = True
					self.stim_on_last_frame = False

				if dt > self.finishtime and not self.finished:
					self.finished = True

					print 	"Task '%s' finished: %s" %(self.taskname,time.asctime())
					print 	"Absolute difference between " \
						"theoretical and actual stimulus times:"
					print np.abs(self.actualstimtimes - self.theoreticalstimtimes)

					if not self._canvas.master.auto_start_tasks:
						self._canvas.master.controlwindow.playlistpanel.onRunTask()
					self._canvas.master.controlwindow.playlistpanel.Next()

			self.dt = dt

################################################################################
# stimulus subtypes

class DotFlash(Task):
	"""
	Base class for flashing dot stimuli

	Implements:
		_make_positions
		_buildstim
		_drawstim
	"""

	# the name of the stimulus subclass
	subclass = 'dot_flash'

	def _make_positions(self):

		assert len(self.permutation) == self.nstim
		
		# generate a random permutation of x,y coordinates
		nx,ny = self.gridshape
		x_vals = np.linspace(-1,1,nx)*self.gridlim[0]*self.area_aspect
		y_vals = np.linspace(-1,1,ny)*self.gridlim[1]
		x, y = np.meshgrid(x_vals,y_vals)
		self.xpos = x.ravel()[self.permutation]
		self.ypos = y.ravel()[self.permutation]

	def _buildstim(self):
		"""
		construct a generic flashing dot stimulus
		"""
		self._make_positions()

		# create the dot
		self._dot = Dot(self.radius,self.nvertices)
		pass

	def _drawstim(self):
		# draw the dot in the current position
		self._dot.draw(	self.xpos[self.currentstim],
				self.ypos[self.currentstim],
				0.,
				self.dot_color
				)

class WeberDotFlash(DotFlash):
	"""
	Flashing dots with pseudorandom positions and luminance values.
	Luminance values are distributed on a log scale.
	"""

	subclass = 'weber_dot_flash'

	def _make_positions(self):

		assert len(self.permutation) == self.nstim

		# generate a random permutation of x,y coordinates and
		# luminances
		nx,ny = self.gridshape		
		x_vals = np.linspace(-1,1,nx)*self.gridlim[0]*self.area_aspect
		y_vals = np.linspace(-1,1,ny)*self.gridlim[1]

		nl = self.n_luminances
		lmin,lmax = self.luminance_range
		l_vals = np.linspace(lmin,lmax,nl)**self.gamma

		x, y, l = np.meshgrid(x_vals, y_vals, l_vals)
		self.xpos = x.ravel()[self.permutation]
		self.ypos = y.ravel()[self.permutation]
		l = l.ravel()[self.permutation]

		self.dot_color = l[:,np.newaxis]*np.ones(4)
		self.dot_color[:,3] = 1.

	def _drawstim(self):
		# draw the dot in the current position
		self._dot.draw(	self.xpos[self.currentstim],
				self.ypos[self.currentstim],
				0.,
				self.dot_color[self.currentstim]
				)

class BarFlash(Task):
	"""
	Base class for flashing bar stimuli

	Implements:
		_buildstim
		_drawstim
	"""

	subclass = 'bar_flash'

	def _make_positions(self):

		assert len(self.permutation) == self.nstim
		
		nx,ny = self.nx, self.ny
		x_vals = np.zeros((nx+ny),dtype=np.float32)
		y_vals = np.zeros((nx+ny),dtype=np.float32)
		orientations = np.zeros((nx+ny),dtype=np.float32)

		x_vals[:nx] = np.linspace(-1,1,nx)*self.gridlim[0]*self.area_aspect
		orientations[nx:] = 90.
		y_vals[nx:] = np.linspace(-1,1,ny)*self.gridlim[1]

		self.xpos = x_vals[self.permutation]
		self.ypos = y_vals[self.permutation]
		self.orientation = orientations[self.permutation]


	def _buildstim(self):
		self._make_positions()
		self._bar = Bar(	width=self.bar_width,
					height=self.bar_height
					)

	def _drawstim(self):
		# draw the bar in the current position/orientation
		self._bar.draw(	self.xpos[self.currentstim],
				self.ypos[self.currentstim],
				angle=self.orientation[self.currentstim],
				color=self.bar_color)


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
		
		assert len(self.permutation) == self.nstim

		# direction for each bar sweep
		orientation = np.linspace(0.,360.,len(self.fullpermutation),endpoint=False)

		# do the shuffling
		self.orientation = orientation[self.permutation]

	def _buildstim(self):

		self._make_orientations()
		self._bar = Bar(			width=self.bar_width,
							height=self.bar_height
							)

		self._aperture = CircularStencil(	radius=self.aperture_radius,
							nvertices=self.aperture_nvertices,
							polarity=1)

	def _drawstim(self):

		# get the current bar position (ROTATED 90o!)
		bar_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
		frac = bar_dt/(self.offtimes[self.currentstim] - self.ontimes[self.currentstim])
		x,y = get_current_bar_xy(	frac,
						self.orientation[self.currentstim],
						radius=max(1,self.area_aspect))

		# enable stencil test, draw the aperture to the stencil buffer
		gl.glEnable(gl.GL_STENCIL_TEST)
		self._aperture.draw()

		# draw the bar (ROTATED 90o!), disable stencil test
		self._bar.draw(	x,y,0,
				angle=self.orientation[self.currentstim],
				color=self.bar_color
				)
		gl.glDisable(gl.GL_STENCIL_TEST)

		pass

class OccludedDriftingBar(DriftingBar):
	"""
	Drifting bar with a rectangular 'occluded' region

	Implements:
		_make_orientations
		_buildstim
		_drawstim
	"""
	subclass = 'occluded_drifting_bar'

	def _make_orientations(self):

		assert len(self.permutation) == self.nstim

		# angle = np.repeat(self.angles,self.full_nstim//2)
		occluder_pos = np.linspace(	-1.+(self.occluder_width/2.),
						1.-(self.occluder_width/2.),
						self.n_occluder_positions)*self.area_aspect

		# make a list of tuples (angle,position)
		states = []
		for angle in self.angles:
			for x0 in occluder_pos:
				states.append((angle,x0))

		# now we shuffle the stimulus
		states = [states[ii] for ii in self.permutation]

		self.orientation,self.occluder_pos = zip(*states)

	def _buildstim(self):

		self._make_orientations()
		self._bar = Bar(			width=self.bar_width,
							height=self.bar_height
							)

		self._aperture = RectangularStencil(	width=self.occluder_width*self.area_aspect,
							height=self.occluder_height,
							polarity=0)

	def _drawstim(self):

		# get the current bar position (ROTATED 90o!)
		bar_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
		frac = bar_dt/(self.offtimes[self.currentstim] - self.ontimes[self.currentstim])
		x,y = get_current_bar_xy(	frac,
						self.orientation[self.currentstim],
						radius=max(1,self.area_aspect))

		# enable stencil test, draw the aperture to the stencil buffer
		gl.glEnable(gl.GL_STENCIL_TEST)
		self._aperture.draw(x=self.occluder_pos[self.currentstim])

		# draw the bar (ROTATED 90o!), disable stencil test
		self._bar.draw(	x,y,0,
				angle=self.orientation[self.currentstim],
				color=self.bar_color)
		gl.glDisable(gl.GL_STENCIL_TEST)

		pass

class DriftingGrating(Task):
	"""
	Base class for drifting texture stimuli

	Implements:
		_make_orientations
		_buildstim
		_drawstim
	"""

	def _make_orientations(self):

		assert len(self.permutation) == self.nstim

		orientation = np.linspace(0.,360.,len(self.fullpermutation),endpoint=False)

		# do the shuffling
		orientation = orientation[self.permutation]
		self.orientation = orientation

		pass

	def _buildstim(self):
		self._make_orientations()
		self._make_grating()
		self._texture = GratingTextureQuad(	texdata=self._texdata,
							rect=(-1,-1,1,1))

		self._aperture = CircularStencil(	radius=self.aperture_radius,
							nvertices=self.aperture_nvertices,
							polarity=1)

		pass

	def _drawstim(self):

		# update the current phase angle
		on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
		self._phase = on_dt*self.grating_speed

		# enable stencil test, draw the aperture to the stencil buffer
		gl.glEnable(gl.GL_STENCIL_TEST)
		self._aperture.draw()


		# draw the texture, disable stencil test
		self._texture.draw(	offset=self._phase,
					# correction for unit circle
					angle=self.orientation[self.currentstim],
					color=self.grating_color
					)
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