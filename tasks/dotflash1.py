import wx
from wxPython.glcanvas import wxGLCanvas
import sys,math
import numpy as np
import time
import pdb
import OpenGL
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut


class task():

	def __init__(self, canvas = None, gl = gl, glut = glut):

		np.random.seed(0)

		self.canvas = canvas
		self.gl = gl
		self.glut = glut
		self.starttime = -1
		self.name = 'dotflash1'

		N = 6
		M = 6
		numstim = N*M

		self.initblanktime = 2.0
		self.finalblanktime = 10.0
#		self.ontimes = 2.*np.array([0.,1.,2.,3.,4.,5.,6.,7.,8.])
		self.ontimes = 8.*np.arange(0.,numstim/2)

		self.theoreticalstimtimes = (	self.initblanktime +
						self.ontimes)

		self.actualstimtimes = -1.*np.ones(self.theoreticalstimtimes.size)
		self.stimflags = np.zeros(self.theoreticalstimtimes.size)

		self.finishtime = (	self.initblanktime + 
					self.finalblanktime +
					self.ontimes[-1])
					
		self.finished = False
		self.dt = -1.	


		# stim specific stuff
		self.offtimes =	self.ontimes + 1.	
		self.radius = 0.075

		self.xpos, self.ypos = np.meshgrid(np.arange(0.,N),np.arange(0.,M))
		self.xpos = self.xpos.flatten() / (N/2.)
		self.ypos = self.ypos.flatten() / (M/2.)
		self.permutation = np.random.permutation(np.arange(0,numstim))
		self.xpos = self.xpos[self.permutation] - 1.
		self.ypos = self.ypos[self.permutation] - 1.

		self.xpos = self.xpos[0:numstim/2]
		self.ypos = self.ypos[0:numstim/2]

#		self.showdot = np.empty((numstim,))
#		self.showdot[::2] = 1.
#		self.showdot[1::2] = 0.

#		self.xpos = np.array([0.,1.,2.,0.,1.,2.,0.,1.,2.]) - 1.
#		self.ypos = np.array([0.,0.,0.,1.,1.,1.,2.,2.,2.]) - 1.
#		self.ypos = np.random.permutation(self.xpos)

		self.xpos = 0.9*self.xpos
		self.ypos = 0.9*self.ypos

		self.buildlists()
		self.buildparamsdict()	

		# photodiode control:
		self.hz = 5.
		self.frametimes = np.arange(0., self.finishtime, 1./self.hz)
		self.currentframe = 0
		self.photodiodeontime = 0.075

	def buildparamsdict(self):

		pd = {}
		
		# do the standard stuff first:
		pd.update({'name':self.name})
		pd.update({'initblanktime':self.initblanktime})
		pd.update({'finalblanktime':self.finalblanktime})
		pd.update({'ontimes':self.ontimes})
		pd.update({'stimtimes':self.theoreticalstimtimes})
		pd.update({'finishtime':self.finishtime})

		# stim specific stuff
		pd.update({'offtimes':self.offtimes})	
		pd.update({'radius':self.radius})
		pd.update({'xpos':self.xpos})
		pd.update({'ypos':self.ypos})

		self.paramsdict = pd


	def buildlists(self):
	
		gl = self.gl

                radius = self.radius
		dot = gl.glGenLists(1)
		gl.glNewList(dot, gl.GL_COMPILE)
		gl.glColor3f(1.0,1.0,1.0)
		
		gl.glBegin(gl.GL_POLYGON)
		for angle in np.arange(0.,2*np.pi,(2*np.pi)/64.):
		        gl.glVertex3f(np.sin(angle) * radius, np.cos(angle) * radius, 0.)
		gl.glEnd()
		gl.glEndList()
		self.dot = dot


	def reinit(self):
		self.starttime = -1
		self.stimflags = np.zeros(self.theoreticalstimtimes.size)
		self.actualstimtimes = -1.*np.ones(self.theoreticalstimtimes.size)
		self.finished = False
		self.dt = -1.
		self.buildlists()
		self.currentframe = 0


	def display(self):

		gl = self.gl
		glut = self.glut

		if (self.starttime == -1):
			self.starttime = time.time()
#			self.canvas.photodiodevisible = True
		else:
			dt = time.time() - self.starttime
			self.dt = dt

			# start the imaging
#			if (dt > 0.1):
#				self.canvas.photodiodevisible = False

			timeafterinitblank = dt - self.initblanktime

			if (self.currentframe+1 < self.frametimes.size):
				if (dt > self.frametimes[self.currentframe+1]):
					self.currentframe += 1

			if ((dt > self.frametimes[self.currentframe]) and 
			    (dt < (self.frametimes[self.currentframe] + self.photodiodeontime))):
				self.canvas.photodiodevisible = True
			else:
				self.canvas.photodiodevisible = False
			

			if (timeafterinitblank < 0.):
				pass
			else:
				indx = np.where(self.ontimes < (timeafterinitblank))
	
				if ((len(indx) > 0) and (len(indx[0]) > 0)):
					indx = indx[0][-1]

					# should we present a stimulus, or do nothing?:

					if (timeafterinitblank < self.offtimes[indx]):
#						pdb.set_trace()

#						gl.glPushMatrix()	
#						gl.glLoadIdentity()
#						color = [1.0,0.,0.,1.]
#						gl.glMaterialfv(gl.GL_FRONT,gl.GL_DIFFUSE,color)
#						gl.glScale(0.2,0.2,0.2)	
#					if (self.showdot[indx]):
						gl.glTranslate(	self.xpos[indx],
								self.ypos[indx],
								0.)	
						gl.glCallList(self.dot)
#						gl.glPopMatrix()

					else:
						pass			

					if not(self.stimflags[indx]):
						recalcdt = time.time() - self.starttime
						self.actualstimtimes[indx] = recalcdt
						self.stimflags[indx] = 1.

				else: #we are still in init blank mode
					pass
			
			if ((dt > self.finishtime) and (self.finished == False)):
				self.finished = True
				print ('absolute difference between theoretical ' +
					'and actual stimulus times:')
				print np.abs(self.actualstimtimes - self.theoreticalstimtimes)



