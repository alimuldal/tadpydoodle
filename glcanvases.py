import OpenGL

# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False

# test for bottlenecks
OpenGL.ERROR_ON_COPY = False

import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
import OpenGL.GL.framebufferobjects as fbo

import wx
from wx.glcanvas import GLCanvas,GLCanvasWithContext

# import threading
import numpy as np
import time
# import os

class StimCanvas(GLCanvas):
	"""
	This is the canvas where the simulus gets drawn to 'first' (a copy of
	what's currently being displayed can also be drawn inside an associated
	PreviewCanvas)
	"""

	def __init__(self,parent,master):
		attribList = [	wx.glcanvas.WX_GL_DOUBLEBUFFER,
				wx.glcanvas.WX_GL_BUFFER_SIZE,8,
				wx.glcanvas.WX_GL_DEPTH_SIZE,8,
				wx.glcanvas.WX_GL_STENCIL_SIZE,0]
		super(StimCanvas,self).__init__(parent,-1,attribList=attribList)

		self.parent = parent
		self.master = master
		self.slaves = []
		self.Bind(wx.EVT_PAINT,self.onPaint)

		self.drawcount = 0
		self.slowestframe = -1
		self.starttime = time.time()
		self.currtime = self.starttime

		# we do this in order that self.drawqueue.hasRun() == True
		def dummy(): pass
		self.drawqueue = wx.CallLater(0,dummy)

		self.done_postinit = False

		pass

	def postinit(self):
		"""
		This is called at the start of onPaint if not self.done_predraw.
		We have to do this initialisation AFTER the canvas has been
		created because it requires an OpenGL context!
		"""
		self.SetCurrent()
		self.makedisplaylists()
		self.initFBO()

		pass

	def makedisplaylists(self):
		""" Compile display lists for the crosshairs and photodiode """

		photodiodelist = gl.glGenLists(1)
		gl.glNewList(photodiodelist, gl.GL_COMPILE)
		gl.glBegin(gl.GL_POLYGON)
		gl.glVertex3f(-1., 1., 0.)	
		gl.glVertex3f(1., 1., 0.)
		gl.glVertex3f(1., -1., 0.)
		gl.glVertex3f(-1., -1., 0.)
		gl.glVertex3f(-1., 1., 0.)	
		gl.glEnd()
		gl.glEndList()
		self.photodiodelist = photodiodelist

		crosshairlist = gl.glGenLists(1)
		gl.glNewList(crosshairlist, gl.GL_COMPILE)

		gl.glColor4f(1.,0.,0.,1.)
		gl.glBegin(gl.GL_LINE_LOOP)
		gl.glVertex3f(-1., 1., 0.)	
		gl.glVertex3f(1., 1., 0.)
		gl.glVertex3f(1., -1., 0.)
		gl.glVertex3f(-1., -1., 0.)
		gl.glVertex3f(-1., 1., 0.)	
		gl.glEnd()

		radius = 0.5
		gl.glBegin(gl.GL_LINE_LOOP)
		for angle in np.arange(0.,2*np.pi,(2*np.pi)/64.):
			gl.glVertex3f(np.sin(angle) * radius, np.cos(angle) * radius, 0.)
		gl.glEnd()
		gl.glBegin(gl.GL_LINES)
		gl.glVertex3f(0., 0.3, 0.)	
		gl.glVertex3f(0., -.3, 0.)
		gl.glVertex3f(.3, 0., 0.)
		gl.glVertex3f(-0.3, 0., 0.)
		gl.glEnd()

		gl.glEndList()
  		self.crosshairlist = crosshairlist

  		pass

  	def initFBO(self):
  		"""
  		Initialise the framebuffer object. This should happen whenever
  		the stimulus resolution changes
  		"""

  		xres,yres = self.master.x_resolution,self.master.y_resolution

		# create & bind an EMPTY texture object. we will render the
		# whole viewport to this texture
		self.fbo_texture = gl.glGenTextures(1)
		gl.glBindTexture(gl.GL_TEXTURE_2D,self.fbo_texture)
		gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
		gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )
		gl.glTexImage2D(gl.GL_TEXTURE_2D,0,gl.GL_RGB32F,xres,yres,0,
				gl.GL_RGB,gl.GL_FLOAT,None)

		# create & bind a framebuffer object
		self.framebuffer = fbo.glGenFramebuffers(1)
		fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,self.framebuffer)


		# create & bind renderbuffer object to store depth info
		self.depthbuffer = fbo.glGenRenderbuffers(1)
		fbo.glBindRenderbufferEXT(fbo.GL_RENDERBUFFER,self.depthbuffer)
		fbo.glRenderbufferStorageEXT(	fbo.GL_RENDERBUFFER,
						gl.GL_DEPTH_COMPONENT,
						xres,yres)

		# attach the texture to the color component of the framebuffer
		fbo.glFramebufferTexture2D(	fbo.GL_FRAMEBUFFER,		# target
						fbo.GL_COLOR_ATTACHMENT0,	# attachment point
						gl.GL_TEXTURE_2D,		# texture target
						self.fbo_texture,	# texture id
						0			# mipmap level
						)

		# attach the renderbuffer to the depth component of the framebuffer
		fbo.glFramebufferRenderbuffer(	fbo.GL_FRAMEBUFFER,
						fbo.GL_DEPTH_ATTACHMENT,
						fbo.GL_RENDERBUFFER,
						self.depthbuffer,
						)

		# # make sure the FBO is set up correctly
		# status = fbo.glCheckFramebufferStatusEXT(fbo.GL_FRAMEBUFFER)
		# assert status == fbo.GL_FRAMEBUFFER_COMPLETE_EXT, status

		# switch back to the display manager-provided framebuffer
		fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,0)

		pass

	def onPaint(self,event=None):
		"""
		This gets called whenever the parent window contents need to be
		repainted
		"""

		# make sure we've finished initialising the OpenGL stuff
		if not self.done_postinit:
			self.postinit()
			self.done_postinit = True

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

		if self.master.show_preview:
			# if we're previewing, draw to the offscreen framebuffer
			fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,self.framebuffer)
		else:
			# otherwise, just draw to the normal back buffer
			fbo.glBindFramebuffer(fbo.GL_FRAMEBUFFER,0)

		xres,yres = self.master.x_resolution,self.master.y_resolution

		# the viewport is the same size as the stimulus resolution
		gl.glViewport(0, 0, xres, yres)

		# set an orthogonal projection - visible region will be from
		# 0-->size in x and y, and from -100-->100 in z
		gl.glMatrixMode(gl.GL_PROJECTION)
		gl.glLoadIdentity()
		# left, right, bottom, top, near, far
		gl.glOrtho(0,xres,0,yres,-100,100)

		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glLoadIdentity()
		gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
		gl.glClearColor(0., 0., 0., 0.)		# should vary this according to the task!

		gl.glPushMatrix()

		if self.master.show_crosshairs:
			gl.glLoadIdentity()
			gl.glTranslate(self.master.c_ypos,self.master.c_xpos, -1)
			gl.glScale(*(self.master.c_scale,)*3)
			gl.glCallList(self.crosshairlist)

		# we always draw the photodiode, but we change its color
		# conditionally - when off it will appear black against a white
		# background
		gl.glLoadIdentity()
		gl.glTranslate(self.master.p_ypos,self.master.p_xpos, -1)
		gl.glScale(*(self.master.p_scale,)*3)
		if (self.master.show_photodiode):
			gl.glColor4f(1.,1.,1.,1.)
		else:
			gl.glColor4f(0.,0.,0.,1.)
		gl.glCallList(self.photodiodelist)
		gl.glColor4f(1.,1.,1.,1.)

		if self.master.run_task:
			gl.glLoadIdentity()
			gl.glTranslate(self.master.c_ypos, self.master.c_xpos, -1);
			gl.glScale(*(self.master.c_scale,)*3)
			
			# we enable depth testing in case the task requires it
			gl.glEnable(gl.GL_DEPTH_TEST)
			self.master.current_task.display()
			gl.glDisable(gl.GL_DEPTH_TEST)

		gl.glPopMatrix()

		if self.master.show_preview:
			# now blit the contents of the FBO to the back buffer
			fbo.glBindFramebuffer(	fbo.GL_READ_FRAMEBUFFER,self.framebuffer)
			fbo.glBindFramebuffer(	fbo.GL_DRAW_FRAMEBUFFER,0)
			fbo.glBlitFramebuffer(	0,0,xres,yres,0,0,xres,yres,
						gl.GL_COLOR_BUFFER_BIT, gl.GL_NEAREST)

		# swap the front and back buffers, so that the new frame is now
		# visible. this is the bottleneck where all of the OpenGL calls
		# actually execute
		self.SwapBuffers()

		# if we're running the display loop, queue another draw call
		if self.master.run_loop:
			self.drawcount += 1
			self.drawqueue = wx.CallLater(self.master.min_delta_t,self.onDraw)

		# keep a running minimum of the framerate
		now = time.time()
		dt = now - self.currtime
		if dt > self.slowestframe:
			self.slowestframe = dt
		self.currtime = now

		if not self.drawcount % self.master.framerate_window:
			self.drawcount = 0
			self.slowestframe = -1

		# we draw every nth frame to the preview canvas to avoid
		# unncecessary overhead
		if not self.drawcount % self.master.preview_frequency:
			if self.master.show_preview:
				[slave.onDraw() for slave in self.slaves]

		# update the task status panel
		self.master.controlwindow.statuspanel.onUpdate()


class PreviewCanvas(GLCanvas):
	"""
	This canvas is always bound to a 'master' StimCanvas with a framebuffer.
	It just draws the contents of its master's framebuffer when its onDraw
	gets triggered by the master.

	Since it shares an OpenGL context with its master, it can only be
	created after its master has been created AND DRAWN at least once.
	"""

	def __init__(self,parent,stimcanvas,size=None):
		attribList = [	wx.glcanvas.WX_GL_DOUBLEBUFFER,
				wx.glcanvas.WX_GL_BUFFER_SIZE,8,
				wx.glcanvas.WX_GL_DEPTH_SIZE,8,
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

		# this is crappy nomenclature - 'master' here refers to the
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
		self.stimcanvas.slaves.append(self)

	def detach(self):
		self.stimcanvas.slaves.remove(self)

	def postinit(self):
		""" called in onPaint if self.done_postinit == False """

		# pre-compile the texture display list
		self.texlist = gl.glGenLists(1)
		gl.glNewList(self.texlist, gl.GL_COMPILE)

		# rotate the texture 90o counterclockwise
		gl.glMatrixMode(gl.GL_TEXTURE);
		gl.glLoadIdentity();
		gl.glTranslatef(0.5,0.5,0.0);
		gl.glRotatef(-90,0.0,0.0,1.0);
		gl.glTranslatef(-0.5,-0.5,0.0);

		# draw the texture
		gl.glBegin( gl.GL_QUADS )
		gl.glTexCoord2f( 0, 1 );	gl.glVertex2f( 0, 1 )
		gl.glTexCoord2f( 0, 0 );	gl.glVertex2f( 0, 0 )
		gl.glTexCoord2f( 1, 0 );	gl.glVertex2f( 1, 0 )
		gl.glTexCoord2f( 1, 1 );	gl.glVertex2f( 1, 1 )
		gl.glEnd()
		gl.glEndList()

		pass

	def onPaint(self,event=None):

		# we can only draw after the master canvas has already done so,
		# otherwise we won't have an OpenGL context
		if self.stimcanvas.done_postinit:
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

		w,h = self.GetSize()
		gl.glViewport(0,0,w,h)

		gl.glMatrixMode(gl.GL_PROJECTION)
		gl.glLoadIdentity()
		gl.glOrtho(0,1,0,1,0,1)

		gl.glMatrixMode(gl.GL_MODELVIEW)
		gl.glLoadIdentity()

		# clear the buffers
		gl.glClear( gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT )

		# bind the master's FBO texture
		gl.glEnable(gl.GL_TEXTURE_2D)
		gl.glBindTexture(gl.GL_TEXTURE_2D,self.stimcanvas.fbo_texture)

		# call the display list to draw the texture
		gl.glCallList(self.texlist)

		gl.glDisable(gl.GL_TEXTURE_2D)
		gl.glBindTexture(gl.GL_TEXTURE_2D,0)

		# swap buffers, show the updated texture in this canvas
		self.SwapBuffers()

	def onMotion(self,event):
		""" called when mouse moves within the figure """

		if wx.GetKeyState(wx.WXK_F1):
			mode = 1
		elif wx.GetKeyState(wx.WXK_F2):
			mode = 2
		else:
			mode = 0

		if mode:
			# map coordinates on the preview window to coordinates
			# in display space
			preview_x,preview_y = event.GetX(),event.GetY()

			p_w,p_h = self.GetSize()
			d_h,d_w = self.master.x_resolution,self.master.y_resolution

			display_x = (d_w)*(1. - float(preview_x)/p_w)
			display_y = (d_h)*(1. - float(preview_y)/p_h)

			# aaaargh hellish callbacks!
			if mode == 1:
				controls = self.master.controlwindow.adjustpanel.p_textctls
				prefix = 'p_'
			else:
				controls = self.master.controlwindow.adjustpanel.c_textctls
				prefix = 'c_'

			controls[prefix+'xpos'].ref.set(display_x)
			controls[prefix+'xpos'].SetValue(str(display_x))
			controls[prefix+'ypos'].ref.set(display_y)
			controls[prefix+'ypos'].SetValue(str(display_y))

	def onWheel(self,event):

		if wx.GetKeyState(wx.WXK_F1):
			control = self.master.controlwindow.adjustpanel.p_textctls['p_scale']
		elif wx.GetKeyState(wx.WXK_F2):
			control = self.master.controlwindow.adjustpanel.c_textctls['c_scale']
		else:
			return

		rot = -1 + 2*(event.GetWheelRotation() > 0.)
		delta = rot*self.master.controlwindow.adjustpanel.scaleinc

		val = control.ref.get()
		val += delta
		control.ref.set(val)
		control.SetValue(str(val))