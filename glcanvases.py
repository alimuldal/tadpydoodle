import OpenGL

# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False

# test for bottlenecks
OpenGL.ERROR_ON_COPY = True

import OpenGL.GL as gl
# import OpenGL.GLU as glu
# import OpenGL.GLUT as glut
import OpenGL.GL.framebufferobjects as fbo
# import OpenGL.GLX as glx

import wx
from wx.glcanvas import GLCanvas,GLCanvasWithContext

# import threading
import numpy as np
import time
# import os

import collections

class StimCanvas(GLCanvas):
	"""
	This is the canvas where the simulus gets drawn to 'first' (a copy of
	what's currently being displayed can also be drawn inside an associated
	PreviewCanvas)
	"""

	def __init__(self,parent,master):
		# really, having this canvas double-buffered and giving it
		# stencil and depth buffers are unncecessary if we are
		# rendering to an offcreen framebuffer first, but I include
		# them in case the user turns off preview mode.
		attribList = [	wx.glcanvas.WX_GL_DOUBLEBUFFER,
				wx.glcanvas.WX_GL_BUFFER_SIZE,8,
				# wx.glcanvas.WX_GL_RGBA,
				wx.glcanvas.WX_GL_DEPTH_SIZE,16,
				wx.glcanvas.WX_GL_STENCIL_SIZE,8]

		GLCanvas.__init__(self,parent,-1,attribList=attribList)

		self.parent = parent
		self.master = master
		self.listeners = []
		self.Bind(wx.EVT_PAINT,self.onPaint)

		self.drawcount = 0
		self.slowestframe = -1
		self.starttime = time.time()
		self.currtime = self.starttime

		self.do_refresh_everything = True

		# we do this in order that self.drawqueue.hasRun() == True
		def dummy(): pass
		self.drawqueue = wx.CallLater(0,dummy)

		self.done_postinit = False

		# ring buffers
		self.max_frame_time_buffer = collections.deque(maxlen=self.master.framerate_window)
		self.frametimes = collections.deque(maxlen=self.master.log_nframes)
		self.alldraws = collections.deque(maxlen=self.master.log_nframes)
		self.stimdraws = collections.deque(maxlen=self.master.log_nframes)
		self.photodraws = collections.deque(maxlen=self.master.log_nframes)

		pass

	def postinit(self):
		"""
		This is called at the start of onPaint if (not
		self.done_predraw). We have to do this initialisation AFTER the
		canvas has been created because it requires an OpenGL context!
		"""
		self.SetCurrent()
		self.makedisplaylists()
		self.initFBO()

		# clear values
		gl.glClearStencil(0)
		gl.glClearDepth(0)

		# blending is costly
		gl.glDisable(gl.GL_BLEND)

		# # hinting, probably probably ignored by implementation
		# gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
		# gl.glHint(gl.GL_POLYGON_SMOOTH_HINT, gl.GL_NICEST)

		pass

	def makedisplaylists(self):
		""" Compile display list for the crosshairs """

		# display list for the stimulus box
		#---------------------------------------------------------------
		stimboxlist = gl.glGenLists(1)
		gl.glNewList(stimboxlist, gl.GL_COMPILE)

		gl.glColor4f(1.,0.,0.,1.)

		# the box
		gl.glBegin(gl.GL_LINE_LOOP)
		gl.glVertex2f( -1.0,  1.0 )	
		gl.glVertex2f(  1.0,  1.0 )
		gl.glVertex2f(  1.0, -1.0 )
		gl.glVertex2f( -1.0, -1.0 )
		gl.glVertex2f( -1.0,  1.0 )	
		gl.glEnd()

		gl.glEndList()
		#---------------------------------------------------------------

		# display list for the crosshairs
		#---------------------------------------------------------------
		crosshairlist = gl.glGenLists(1)
		gl.glNewList(crosshairlist, gl.GL_COMPILE)

		gl.glColor4f(1.,0.,0.,1.)

		# the circle
		radius = 0.5
		gl.glBegin(gl.GL_LINE_LOOP)
		for angle in np.linspace(0,2*np.pi,64):
			gl.glVertex2f( np.sin(angle)*radius, np.cos(angle)*radius )
		gl.glEnd()

		# the cross
		gl.glBegin(gl.GL_LINES)
		gl.glVertex2f( 0.0,  0.3 )	
		gl.glVertex2f( 0.0, -0.3 )
		gl.glVertex2f( 0.3,  0.0 )
		gl.glVertex2f(-0.3,  0.0 )
		gl.glEnd()

		gl.glEndList()
		#---------------------------------------------------------------

  		self.stimboxlist = stimboxlist
  		self.crosshairlist = crosshairlist

  		pass

  	def initFBO(self):
  		"""
  		Initialise the framebuffer object. This should happen whenever
  		the stimulus resolution changes, since the size of the
  		required renderbuffer depends on the pixel size of the viewport
  		we're rendering.
  		"""

  		xres,yres = self.master.x_resolution,self.master.y_resolution

		# create & bind an EMPTY texture object. we will render the
		# whole viewport to this texture
		self.fbo_texture = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_2D,self.fbo_texture)

		# texture params
		gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )

		# map the texture
		gl.glTexImage2D(
			gl.GL_TEXTURE_2D,		# target
			0,				# mipmap level
			gl.GL_RGB,			# internal format (use any RGB format)
			xres,				# width
			yres,				# height
			0,				# border
			gl.GL_RGB,			# input data format
			gl.GL_UNSIGNED_BYTE,		# input data type
			None				# input data (none until we render to the framebuffer)
			)

		# create & bind a framebuffer object
		self.framebuffer = fbo.glGenFramebuffers(1)
		fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,self.framebuffer)

		# create & bind renderbuffer object to store depth info
		self.depthbuffer = fbo.glGenRenderbuffers(1)
		fbo.glBindRenderbufferEXT(fbo.GL_RENDERBUFFER,self.depthbuffer)
		fbo.glRenderbufferStorageEXT(
			fbo.GL_RENDERBUFFER,		# target
			gl.GL_DEPTH24_STENCIL8,		# internal format (ATI support for combined depth/stencil?)
			xres,				# width
			yres				# height
			)

		# attach the texture to the color component of the framebuffer
		fbo.glFramebufferTexture2D(	
			fbo.GL_FRAMEBUFFER,		# target
			fbo.GL_COLOR_ATTACHMENT0,	# attachment
			gl.GL_TEXTURE_2D,		# texure target
			self.fbo_texture,		# texture ID
			0				# mipmap level
			)

		# attach the renderbuffer to the depth component of the framebuffer
		fbo.glFramebufferRenderbuffer(
			fbo.GL_FRAMEBUFFER,		# target
			fbo.GL_DEPTH_STENCIL_ATTACHMENT,# attachment (ATI support for combined depth/stencil?)
			fbo.GL_RENDERBUFFER,		# renderbuffer target
			self.depthbuffer 		# renderbuffer ID
			)

		# make sure the FBO is set up correctly
		status = fbo.glCheckFramebufferStatusEXT(fbo.GL_FRAMEBUFFER)
		assert status == fbo.GL_FRAMEBUFFER_COMPLETE_EXT

		# switch back to the display manager-provided framebuffer
		fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,0)

		pass

	def recalc_stim_bounds(self):
		"""
		recalculate the bounding boxes for the stimulus area
		"""

		try:
			aspect = self.master.current_task.area_aspect
		except (AttributeError):
			aspect = 1.

		x,y,scale = self.master.c_ypos, self.master.c_xpos, self.master.c_scale
		self.stimbounds = ( 	int(np.floor(x-(scale+1))),
			 		int(np.floor(y-(aspect*scale+1))),
			 		int(np.ceil(2*(scale+1))),
			 		int(np.ceil(2*(aspect*scale+1)))
			 		)

		self.stimbox_aspect = aspect

	def recalc_photo_bounds(self):

		x,y,scale = self.master.p_ypos, self.master.p_xpos, self.master.p_scale
		self.photobounds = ( 	int(np.floor(x-(scale+1))),
			 		int(np.floor(y-(scale+1))),
			 		int(np.ceil(2*(scale+1))),
			 		int(np.ceil(2*(scale+1)))
			 		)

	def onPaint(self,event=None):
		"""
		This gets called whenever the parent window contents need to be
		repainted
		"""

		# make sure we've finished initialising the OpenGL stuff
		if not self.done_postinit:
			self.postinit()
			self.done_postinit = True

		# recalculate the stimulus and photodiode bounding boxes, force
		# a re-draw of the whole scene
		self.recalc_stim_bounds()
		self.recalc_photo_bounds()
		self.do_refresh_everything = True

		# only redraw if there is not already a pending draw request!
		if self.drawqueue.hasRun:
			self.onDraw()
		pass

	def onDraw(self):
		"""
		This is the business end, where the actual rendering loop
		executes
		"""
		self.SetCurrent()

		# if we're previewing, we will draw to the offscreen framebuffer
		if self.master.show_preview:
			fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,self.framebuffer)
		else:
			# otherwise, just draw to the normal back buffer
			fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,0)

		# the viewport is the same size as the stimulus resolution
		xres,yres = self.master.x_resolution,self.master.y_resolution
		gl.glViewport(0, 0, xres, yres)

		# set an orthogonal projection - visible region will be from
		# 0-->size in x and y, and from -128-->128 in z
		gl.glMatrixMode(gl.GL_PROJECTION)
		gl.glLoadIdentity()
		gl.glOrtho(0,xres,0,yres,-128,128)
		# (left, right, bottom, top, near, far)

		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glLoadIdentity()

		# clear color and depth buffers
		if self.do_refresh_everything:

			gl.glClearColor(0., 0., 0., 0.)
			gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT|gl.GL_STENCIL_BUFFER_BIT)

			# we'll need to re-draw these after we've wiped the
			# whole scene
			self.do_refresh_photodiode = True
			self.do_refresh_stimbox = True

			self.do_refresh_everything = False
			self.everything_changed = True

			# print "refresh_everything: %f" %time.time()

		#---------------------------------------------------------------
		# NB - we need to draw from back to front in order for depth
		# testing to work correctly!
		#---------------------------------------------------------------

		# enable scissor test so that only selected regions of the
		# canvas are affected
		gl.glEnable(gl.GL_SCISSOR_TEST)

		# now draw/clear calls only affect the box where the stimulus is
		gl.glScissor( *self.stimbounds )

		if self.do_refresh_stimbox:

			# clear the stimulus area using the task background
			# color. we do this even if the task isn't running yet
			# so that the correct background color is displayed in
			# advance.
			try:
				gl.glClearColor(*self.master.current_task.background_color)
			except AttributeError:
				gl.glClearColor(0.,0.,0.,0.)

			gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT|gl.GL_STENCIL_BUFFER_BIT)

			self.stimbox_changed = True
			self.do_refresh_stimbox = False
			# print "refresh_stimbox: %f" %time.time()

		x,y,scale = self.master.c_ypos, self.master.c_xpos, self.master.c_scale

		# draw the current stimulus state
		if self.master.run_task:
			gl.glPushMatrix()
			gl.glTranslate(x, y, 0)
			gl.glScale(*(scale,)*3)
			self.master.current_task._display()
			gl.glPopMatrix()

		# draw the crosshairs
		if self.master.show_crosshairs:
			gl.glPushMatrix()
			gl.glTranslate(x, y, -127)
			gl.glScale(*(scale,)*3)
			gl.glCallList(self.crosshairlist)

			gl.glScale(1,self.stimbox_aspect,1)
			gl.glCallList(self.stimboxlist)
			gl.glPopMatrix()

		# draw the photodiode
		if self.do_refresh_photodiode:

			# we 'draw' the photodiode by selectively clearing a
			# rectangle in pixel coordinates
			gl.glScissor( *self.photobounds )

			# set our clear color according to whether the
			# photodiode is ON or OFF
			if self.master.show_photodiode:
				gl.glClearColor(1,1,1,1)
			else:
				gl.glClearColor(0,0,0,1)

			# clear the region containing the photodiode
			gl.glClear(gl.GL_COLOR_BUFFER_BIT)

			self.photodiode_changed = True
			self.do_refresh_photodiode = False
			# print "refresh_photodiode: %f" %time.time()

		# disable scissor test, any part of the screen is accessible
		gl.glDisable(gl.GL_SCISSOR_TEST)

		# if we're logging framerate, also record what was being redrawn
		if self.master.log_framerate:
			self.alldraws.append(int(self.everything_changed))
			self.stimdraws.append(int(self.stimbox_changed))
			self.photodraws.append(int(self.photodiode_changed))

		# did anything change during this loop iteration?
		if (self.stimbox_changed or self.photodiode_changed or self.everything_changed):

			# if we're rendering offscreen we now need to blit the
			# contents of the FBO to the back buffer so that they
			# will be made visible when we call SwapBuffers()
			if self.master.show_preview:

				# we read from the framebuffer and write to the
				# back buffer
				fbo.glBindFramebuffer(	fbo.GL_READ_FRAMEBUFFER,self.framebuffer)
				fbo.glBindFramebuffer(	fbo.GL_DRAW_FRAMEBUFFER,0)

				if self.everything_changed:
					# blit the whole viewport area
					x0,y0,w,h = 0,0,xres,yres
					fbo.glBlitFramebuffer(	x0,y0,x0+w,y0+h,
								x0,y0,x0+w,y0+h,
								gl.GL_COLOR_BUFFER_BIT,
								gl.GL_NEAREST)

				else:
					if self.stimbox_changed:
						# blit just the stimulus area
						x0,y0,w,h = self.stimbounds
						fbo.glBlitFramebuffer(	x0,y0,x0+w,y0+h,
									x0,y0,x0+w,y0+h,
									gl.GL_COLOR_BUFFER_BIT,
									gl.GL_NEAREST)

					if self.photodiode_changed:
						# blit just the photodiode area
						x0,y0,w,h = self.photobounds
						fbo.glBlitFramebuffer(	x0,y0,x0+w,y0+h,
									x0,y0,x0+w,y0+h,
									gl.GL_COLOR_BUFFER_BIT,
									gl.GL_NEAREST)

			# swap the front and back buffers so that the changes
			# are made visible
			self.SwapBuffers()

			self.everything_changed = False
			self.stimbox_changed = False
			self.photodiode_changed = False

			# print_gl_error()

			if self.master.show_preview:
				# draw every 'new' frame to the preview canvas
				[listener.onDraw() for listener in self.listeners]

		else:
			# nothing has changed during this rendering loop, so we
			# don't need to blit anything or call SwapBuffers on
			# either the main canvas or the preview canvas
			pass

		# # draw only every nth frame to the preview canvas to reduce
		# # overhead
		# if not self.drawcount % self.master.preview_frequency:
		# 	[listener.onDraw() for listener in self.listeners]

		# keep a running minimum of the framerate and update the task
		# status panel
		now = time.time()
		dt = now - self.currtime

		# benchmarking - store the frame time in a ring buffer
		if self.master.log_framerate:
			self.frametimes.append(dt)
		# if dt > self.slowestframe: self.slowestframe = dt
		self.max_frame_time_buffer.append(dt)
		self.slowestframe = max(self.max_frame_time_buffer)

		self.currtime = now

		if not self.drawcount % self.master.framerate_window:
			self.drawcount = 0
			self.master.controlwindow.statuspanel.onUpdate()

		# if we're running the display loop, queue another draw call
		if self.master.run_loop:
			self.drawcount += 1
			self.drawqueue = wx.CallLater(self.master.min_delta_t,self.onDraw)

class PreviewCanvas(GLCanvas):
	"""
	This canvas is always bound to a 'master' StimCanvas with a framebuffer.
	It just draws the contents of its master's framebuffer when its onDraw
	gets triggered by the master.

	Since it shares an OpenGL context with its master, it can only be
	created after its master has been created AND DRAWN at least once.
	"""

	def __init__(self,parent,stimcanvas,size=None):

		# we don't need a depth or stencil buffer, since this is all
		# taken care of by the offscreen framebuffer. in fact, it
		# doesn't really need to be double-buffered either. meh.
		attribList = [	wx.glcanvas.WX_GL_DOUBLEBUFFER,
				wx.glcanvas.WX_GL_BUFFER_SIZE,8,
				# wx.glcanvas.WX_GL_RGBA,
				wx.glcanvas.WX_GL_DEPTH_SIZE,0,
				wx.glcanvas.WX_GL_STENCIL_SIZE,0]

		if size is None: size = stimcanvas.GetSize()

		# we get the OpenGL context from the master
		self.context = stimcanvas.GetContext()

		# this is a funny class constructor, not a class itself...
		canvas = GLCanvasWithContext(parent,shared=self.context,size=size,attribList=attribList)
		# ...so we do this magic so that canvas is properly instantiated
		self.PostCreate(canvas)

		self.parent = parent
		self.stimcanvas = stimcanvas

		# this is just poor nomenclature - 'master' here refers to the
		# thread, not the other canvas
		self.master = stimcanvas.master

		wx.EVT_PAINT(self,self.onPaint)
		wx.EVT_MOTION(self, self.onMotion)
		wx.EVT_MOUSEWHEEL(self, self.onWheel)
		self.old_mx = None
		self.old_my = None

		self.done_postinit = False
		self.attach()

		pass

	# def __del__(self):
	# 	if self.done_postinit:
	# 		self.detach()

	def attach(self):
		self.stimcanvas.listeners.append(self)

	def detach(self):
		self.stimcanvas.listeners.remove(self)

	def postinit(self):
		""" called in onPaint if self.done_postinit == False """

		# display list for setting up the projection
		# --------------------------------------------------------------
		self.projectionlist = gl.glGenLists(1)
		gl.glNewList(self.projectionlist, gl.GL_COMPILE)

		gl.glMatrixMode(gl.GL_PROJECTION)
		gl.glLoadIdentity()
		gl.glOrtho(0,1,0,1,0,1)

		gl.glEndList()
		# --------------------------------------------------------------

		# display list for the texture that we will use to display the
		# contents of the offscreen
		# --------------------------------------------------------------
		self.texlist = gl.glGenLists(1)
		gl.glNewList(self.texlist, gl.GL_COMPILE)

		# rotate the texture 90o counterclockwise
		gl.glEnable(gl.GL_TEXTURE_2D)

		gl.glMatrixMode(gl.GL_TEXTURE)
		gl.glPushMatrix()
		gl.glLoadIdentity()

		gl.glTranslatef(  0.5, 0.5, 0.0     )
		gl.glRotatef(	-90.0, 0.0, 0.0, 1.0)
		gl.glTranslatef( -0.5,-0.5, 0.0     )

		# draw the texture
		gl.glColor4f(1.,1.,1.,1.)
		gl.glBegin( gl.GL_QUADS )
		gl.glTexCoord2f( 0, 1 );	gl.glVertex2f( 0, 1 )
		gl.glTexCoord2f( 0, 0 );	gl.glVertex2f( 0, 0 )
		gl.glTexCoord2f( 1, 0 );	gl.glVertex2f( 1, 0 )
		gl.glTexCoord2f( 1, 1 );	gl.glVertex2f( 1, 1 )
		gl.glEnd()

		gl.glPopMatrix()
		gl.glDisable(gl.GL_TEXTURE_2D)

		# unbind the texture!
		gl.glBindTexture(gl.GL_TEXTURE_2D,0)

		gl.glEndList()
		# --------------------------------------------------------------

		pass

	def onPaint(self,event=None):

		# we can only draw after the master canvas has already done so,
		# otherwise we won't have an OpenGL context to draw into
		if self.stimcanvas.done_postinit:
			self.currsize = self.GetSize()
			self.onDraw()

	def onDraw(self):

		# NB the syntax is different here - if the context was created
		# separately from the canvas you have to pass it explicitly to
		# SetCurrent
		self.SetCurrent(self.context)

		# make sure we have a texture to draw
		if not self.done_postinit:
			self.postinit()
			self.done_postinit = True

		gl.glViewport(0,0,*self.currsize)

		# set up the projection
		gl.glCallList(self.projectionlist)

		# bind the master's FBO texture
		gl.glBindTexture(gl.GL_TEXTURE_2D,self.stimcanvas.fbo_texture)

		# call the display list to draw the texture
		gl.glCallList(self.texlist)

		# swap buffers, show the updated texture in this canvas
		self.SwapBuffers()

		# print_gl_error()

	def onMotion(self,event):
		""" called when mouse moves within the figure """

		if wx.GetKeyState(wx.WXK_F1):
			mode = 1
		elif wx.GetKeyState(wx.WXK_F2):
			mode = 2
		else:
			return

		# map coordinates on the preview window to coordinates
		# in display space
		preview_x,preview_y = event.GetX(),event.GetY()

		p_w,p_h = self.currsize
		d_h,d_w = self.master.x_resolution,self.master.y_resolution

		display_x = (d_w)*(1. - float(preview_x)/p_w)
		display_y = (d_h)*(1. - float(preview_y)/p_h)

		# aaaargh hellish callbacks!
		if mode == 1:
			controls = self.master.controlwindow.adjustpanel.p_textctls
			prefix = 'p_'

			# recalculate the photodiode bounding box afterwards
			recalc = self.stimcanvas.recalc_photo_bounds

		else:
			controls = self.master.controlwindow.adjustpanel.c_textctls
			prefix = 'c_'

			# recalculate the stimulus bounding box afterwards
			recalc = self.stimcanvas.recalc_stim_bounds

		controls[prefix+'xpos'].ref.set(display_x)
		controls[prefix+'xpos'].SetValue(str(display_x))
		controls[prefix+'ypos'].ref.set(display_y)
		controls[prefix+'ypos'].SetValue(str(display_y))

		# recalculate bounding box
		recalc()

		# force a re-draw of the whole scene
		self.stimcanvas.do_refresh_everything = True

	def onWheel(self,event):

		if wx.GetKeyState(wx.WXK_F1):
			control = self.master.controlwindow.adjustpanel.p_textctls['p_scale']
			# recalculate the photodiode bounding box afterwards
			recalc = self.stimcanvas.recalc_photo_bounds

		elif wx.GetKeyState(wx.WXK_F2):
			control = self.master.controlwindow.adjustpanel.c_textctls['c_scale']
			# recalculate the stimulus bounding box afterwards
			recalc = self.stimcanvas.recalc_stim_bounds
		else:
			return

		rot = -1 + 2*(event.GetWheelRotation() > 0.)
		delta = rot*self.master.controlwindow.adjustpanel.scaleinc

		val = control.ref.get()
		val += delta
		control.ref.set(val)
		control.SetValue(str(val))

		# recalculate bounding box
		recalc()

		# force a re-draw of the whole scene
		self.stimcanvas.do_refresh_everything = True

def print_gl_error():
	"""
	for debugging purposes, check to see if OpenGL threw an error, and print
	the relevant error descriptor
	"""
	errorcodes = [	'GL_INVALID_ENUM',
			'GL_INVALID_VALUE',
			'GL_INVALID_OPERATION',
			'GL_INVALID_FRAMEBUFFER_OPERATION',
			'GL_OUT_OF_MEMORY',
			'GL_STACK_UNDERFLOW',
			'GL_STACK_OVERFLOW']
	error = gl.glGetError()

	if error:
		for state in errorcodes:

			if error == eval('gl.'+state):
				print state
