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
from tasks.task_classes import BarFlash

################################################################################
# barflash-derived stimulus classes
# NB: in order to be displayed in tadpydoodle, stimuli must have a 'taskname'

class barmap(BarFlash):

	taskname = 'barmap'

	gridlim = (0.9,0.9)

	# stimulus-specific parameters
	nx = 6
	ny = 6
	bar_color = (1.,1.,1.,1.)
	bar_height = 2.
	bar_width = 0.2

	# stimulus timing
	initblanktime = 2.
	finalblanktime = 2.
	interval = 5
	on_duration = 1.

	# photodiode triggering parameters
	scan_hz = 5.
	photodiodeontime = 0.075

	#-----------------------------------------------------------------------
	# 10-long permutation when seed == 0
	fullpermutation = np.array([2, 8, 4, 9, 1, 6, 7, 3, 0, 5])
	# fullpermutation = np.arange(10)
	#-----------------------------------------------------------------------

	nstim = 10
	permutation = fullpermutation[:nstim]

class barmap_2hz(barmap):

	taskname = 'barmap_2hz'
	scan_hz = 2.