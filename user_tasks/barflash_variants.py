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
from base_tasks.task_classes import BarFlash

#
# barflash-derived stimulus classes
# NB: in order to be displayed in tadpydoodle, stimuli must have a 'taskname'


class barmap(BarFlash):

    taskname = 'barmap'

    gridlim = (0.9, 0.9)

    # stimulus-specific parameters
    nx = 5
    ny = 5
    bar_rgb = (1., 1., 1.)
    bar_height = 2.
    bar_width = 0.2
    flash_hz = 1E-12
    flash_amplitude = 1.

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 2.
    interval = 8
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 5.
    photodiodeontime = 0.075

    nstim = nx + ny
    #-----------------------------------------------------------------------
    # gen = np.random.RandomState(0)
    # permutation = gen.permutation(nstim)

    # equivalent 10-long permutation when seed == 0
    permutation = np.array([2, 8, 4, 9, 1, 6, 7, 3, 0, 5])
    #-----------------------------------------------------------------------


class old_barmap(barmap):
    taskname = 'old_barmap'
    interval = 5.


class barmap_2hz(barmap):
    taskname = 'barmap_2hz'
    scan_hz = 2.


class old_barmap_2hz(barmap_2hz):
    taskname = 'old_barmap_2hz'
    interval = 5.


class inverted_barmap(barmap):
    taskname = 'inverted_barmap'
    bar_color = (0., 0., 0., 1.)
    background_color = (1., 1., 1., 1.)


class inverted_barmap_2hz(barmap_2hz):
    taskname = 'inverted_barmap_2hz'
    bar_color = (0., 0., 0., 1.)
    background_color = (1., 1., 1., 1.)


class inverted_barmap_2hz_005(inverted_barmap_2hz):
    taskname = 'inverted_barmap_2hz_005'
    background_color = (0.05, 0.05, 0.05, 1.0)


class inverted_barmap_2hz_02(inverted_barmap_2hz):
    taskname = 'inverted_barmap_2hz_02'
    background_color = (0.2, 0.2, 0.2, 1.0)


class inverted_barmap_2hz_04(inverted_barmap_2hz):
    taskname = 'inverted_barmap_2hz_04'
    background_color = (0.4, 0.4, 0.4, 1.0)


class inverted_barmap_2hz_07(inverted_barmap_2hz):
    taskname = 'inverted_barmap_2hz_07'
    background_color = (0.7, 0.7, 0.7, 1.0)


class flashing_barmap_2hz(barmap_2hz):
    taskname = 'flashing_barmap_2hz'
    flash_hz = 5
