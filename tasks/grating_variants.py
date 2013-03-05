import numpy as np
from tasks.task_classes import DriftingSinusoid, DriftingSquarewave

################################################################################
# grating-derived stimulus classes
# NB: in order to be displayed in tadpydoodle, stimuli must have a 'taskname'

class gratings1(DriftingSinusoid):

	taskname = 'gratings1'

	# stimulus-specific parameters
	aperture_radius = 1.
	aperture_nvertices = 256
	grating_color = (1.,1.,1.,1.)
	grating_amplitude = 1. 		# amplitude of luminance change (1 == max)
	grating_nsamples = 1000 	# number of samples in grating
	n_cycles = 5. 			# number of full cycles in texture
	grating_speed = 0.5 		# phase change/frame

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 10.
	interval = 8.
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

class gratings2(gratings1):

	taskname = 'gratings2'
	permutation = gratings1.fullpermutation[gratings1.nstim:]

class gratings_nointerval1(gratings1):
	taskname = 'gratings_nointerval1'
	on_duration = gratings1.interval

class gratings_nointerval2(gratings2):
	taskname = 'gratings_nointerval2'
	on_duration = gratings2.interval

class squarewave1(DriftingSquarewave):

	taskname = 'squarewave1'

	# stimulus-specific parameters
	aperture_radius = 1.
	aperture_nvertices = 256
	grating_color = (1.,1.,1.,1.)
	grating_amplitude = 1. 		# amplitude of luminance change (1 == max)
	grating_nsamples = 1000 	# number of samples in grating
	n_cycles = 5. 			# number of full cycles in texture
	grating_speed = 0.5 		# phase change/frame
	duty_cycle = 0.5		# proporiton of time in the on phase

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 10.
	interval = 8.
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

class squarewave2(squarewave1):
	taskname = 'squarewave2'
	permutation = squarewave1.fullpermutation[squarewave1.nstim:]

class squarewave_nointerval1(squarewave1):
	taskname = 'squarewave_nointerval1'
	on_duration = squarewave1.interval

class squarewave_nointerval2(squarewave2):
	taskname = 'squarewave_nointerval2'
	on_duration = squarewave2.interval
