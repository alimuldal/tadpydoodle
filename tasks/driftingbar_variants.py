import numpy as np
from tasks.task_classes import DriftingBar, OccludedDriftingBar

################################################################################
# drifting bar-derived stimulus classes
# NB: in order to be displayed in tadpydoodle, stimuli must have a 'taskname'

class bars1(DriftingBar):

	taskname = 'bars1'

	# stimulus-specific parameters
	aperture_radius = 1.
	aperture_nvertices = 256
	bar_color = (1.,1.,1.,1.)
	bar_height = 2.
	bar_width = 0.2

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 10.
	interval = 8
	on_duration = 1.

	# photodiode triggering parameters
	scan_hz = 5.
	photodiodeontime = 0.075

	#-----------------------------------------------------------------------
	# 36-long permutation when seed == 0, as in original bars1.py
	fullpermutation = [
	31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28, 32,  8, 13,  5, 
	17, 14,  7, 26,  1, 12, 25, 24,  6, 23,  4, 18, 21, 19,  9, 34,  3,  0 ]
	#-----------------------------------------------------------------------

	nstim = 18
	permutation = fullpermutation[:nstim]

class bars2(bars1):

	taskname = 'bars2'
	permutation = bars1.fullpermutation[bars1.nstim:]

class bars_firsthalf(OccludedDriftingBar):

	taskname = 'bars_firsthalf'

	# stimulus-specific parameters
	area_aspect = 2
	aperture_radius = 1.
	aperture_nvertices = 256
	bar_color = (1.,1.,1.,1.)
	bar_height = 2.
	bar_width = 0.2
	rect_occlusion = (-1,-1.1*area_aspect,2,1.1*area_aspect)
	angles = (90,270)

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 10.
	interval = 8
	on_duration = 2.

	# photodiode triggering parameters
	scan_hz = 5.
	photodiodeontime = 0.075

	seed = 0
	full_nstim = 36
	nstim = full_nstim // 2
	_gen = np.random.RandomState(seed)
	fullpermutation = _gen.permutation(full_nstim)
	permutation = fullpermutation[:nstim]

class bars_secondhalf(bars_firsthalf):
	taskname = 'bars_secondhalf'
	rect_occlusion = (-1,0,2,1.1*bars_firsthalf.area_aspect)
	permutation = bars_firsthalf.fullpermutation[bars_firsthalf.nstim:]