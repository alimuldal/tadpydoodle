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
from base_tasks.task_classes import DriftingSinusoid, DriftingSquarewave

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
	fullpermutation = np.array([
	31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28, 32,  8, 13,  5, 
	17, 14,  7, 26,  1, 12, 25, 24,  6, 23,  4, 18, 21, 19,  9, 34,  3,  0 
	])
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

class gratings_2hz_1(gratings1):
	taskname = 'gratings_2hz_1'
	scan_hz = 2.

class gratings_2hz_2(gratings2):
	taskname = 'gratings_2hz_2'
	scan_hz = 2.

class gratings_nointerval_2hz_1(gratings_nointerval1):
	taskname = 'gratings_nointerval_2hz_1'
	scan_hz = 2.

class gratings_nointerval_2hz_2(gratings_nointerval2):
	taskname = 'gratings_nointerval_2hz_2'
	scan_hz = 2.

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
	fullpermutation = np.array([
	31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28, 32,  8, 13,  5, 
	17, 14,  7, 26,  1, 12, 25, 24,  6, 23,  4, 18, 21, 19,  9, 34,  3,  0 
	])
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

class squarewave_2hz_1(squarewave1):
	taskname = 'squarewave_2hz_1'
	scan_hz = 2.

class squarewave_2hz_2(squarewave2):
	taskname = 'squarewave_2hz_2'
	scan_hz = 2.

class squarewave_nointerval_2hz_1(squarewave_nointerval1):
	taskname = 'squarewave_nointerval_2hz_1'
	scan_hz = 2.

class squarewave_nointerval_2hz_2(squarewave_nointerval2):
	taskname = 'squarewave_nointerval_2hz_2'
	scan_hz = 2.

################################################################################
# tests

class orientation_test(squarewave1):

	taskname = 'grating_orientation_test'
	subclass = 'test_stimuli'

	nstim = 8
	on_duration = 1
	interval = 1
	initblanktime = 0
	finalblanktime = 0

	def _make_orientations(self):
		self.orientation = np.linspace(0,360,self.nstim,endpoint=False)

	_olddraw = squarewave1._drawstim
	def _drawstim(self):
		self._olddraw()
		print "%f deg" %self.orientation[self.currentstim]


# class orientation_test(gratings1):

# 	taskname = 'grating_orientation_test2'

# 	nstim = 8
# 	on_duration = 1
# 	interval = 1
# 	initblanktime = 0
# 	finalblanktime = 0

# 	def _make_orientations(self):
# 		self.orientation = np.linspace(0,360,self.nstim,endpoint=False)

# 	_olddraw = gratings1._drawstim
# 	def _drawstim(self):
# 		self._olddraw()
# 		print "%f deg" %self.orientation[self.currentstim]