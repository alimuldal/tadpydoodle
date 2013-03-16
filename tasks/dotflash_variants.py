import numpy as np
from tasks.task_classes import DotFlash

################################################################################
# dotflash-derived stimulus classes
# NB: in order to be displayed in tadpydoodle, stimuli must have a 'taskname'

class dotflash1(DotFlash):
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
	31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28,	32,  8, 13,  5, 
	17, 14,  7, 26,  1, 12, 25, 24,  6, 23,	 4, 18, 21, 19,  9, 34,  3,  0])
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

class inverted_dotflash1(dotflash1):
	taskname = 'inverted_dotflash1'
	background_color = (1.,1.,1.,1.)
	dot_color = (0.,0.,0.,1.)

class  inverted_dotflash2(dotflash2):
	taskname = 'inverted_dotflash2'
	background_color = (1.,1.,1.,1.)
	dot_color = (0.,0.,0.,1.)

class widescreen_dotflash1(DotFlash):
	"""
	A coarser dotflash mapping over twice the stimulus width. The grid is
	8x4 (32 states, 2x movies), and the dot radius is accordingly scaled up.
	"""

	# this is how the stimulus will appear in td2's menu
	taskname = 'widescreen_dotflash1'

	# stimulus-specific parameters
	gridshape = (8,4)
	gridlim = (0.8,0.8)
	dot_color = (1.,1.,1.,1.)
	radius = 0.075
	nvertices = 64
	area_aspect = 2 	# twice as wide as high

	# stimulus timing
	# initblanktime = 2.
	# finalblanktime = 10.
	# interval = 8
	# on_duration = 1
	initblanktime = 0
	finalblanktime = 0
	interval = 1
	on_duration = interval

	# photodiode triggering parameters
	scan_hz = 5.
	photodiodeontime = 0.075

	seed = 0
	_gen = np.random.RandomState(seed)
	full_nstim = np.prod(gridshape)
	fullpermutation = _gen.permutation(full_nstim)

	# split into parts
	nstim = full_nstim // 2
	part = 1
	permutation = fullpermutation[(part-1)*nstim:part*nstim]

class widescreen_dotflash2(widescreen_dotflash1):
	taskname = 'widescreen_dotflash2'
	fullpermutation = widescreen_dotflash1.fullpermutation
	nstim = widescreen_dotflash1.nstim
	part = 2
	permutation = fullpermutation[(part-1)*nstim:part*nstim]

class widescreen_dotflash_2hz_1(widescreen_dotflash1):
	taskname = 'widescreen_dotflash_2hz_1'
	scan_hz = 2.

class widescreen_dotflash_2hz_2(widescreen_dotflash2):
	taskname = 'widescreen_dotflash_2hz_2'
	scan_hz = 2.

class position_test(widescreen_dotflash1):
	taskname = 'position_test'

	area_aspect = 2
	gridshape = (8,4)
	gridlim = (0.8,0.8)
	_ux = np.linspace(-1.,1.,gridshape[0])*gridlim[0]*area_aspect
	_uy = np.linspace(-1.,1.,gridshape[1])*gridlim[1]
	xpos,ypos = np.meshgrid(_ux,_uy)
	xpos,ypos = xpos.flatten(),ypos.flatten()

	dot_color = (0,0,0,0)
	background_color = (1,1,1,1)

	nstim = np.prod(gridshape)
	initblanktime = 0
	finalblanktime = 0
	interval = 1
	on_duration = interval

	def _make_positions(self):
		pass

	_olddraw = widescreen_dotflash1._drawstim
	def _drawstim(self):
		self._olddraw()
		print "x = %.2f, y = %.2f" %(self.xpos[self.currentstim],self.ypos[self.currentstim])

# class widescreen_dotflash3(widescreen_dotflash1):
# 	taskname = 'widescreen_dotflash3'
# 	fullpermutation = widescreen_dotflash1.fullpermutation
# 	nstim = widescreen_dotflash1.nstim
# 	part = 3
# 	permutation = fullpermutation[(part-1)*nstim:part*nstim]

# class widescreen_dotflash4(widescreen_dotflash1):
# 	taskname = 'widescreen_dotflash4'
# 	fullpermutation = widescreen_dotflash1.fullpermutation
# 	nstim = widescreen_dotflash1.nstim
# 	part = 4
# 	permutation = fullpermutation[(part-1)*nstim:part*nstim]
