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
from base_tasks.task_classes import FullFieldFlash, FullFieldSinusoid

class _gamma_1p8_flash(FullFieldFlash):

    # stimulus-specific parameters
    fullfield_rgb = (1, 1, 1)
    background_color = (0, 0, 0, 1.)
    flash_hz = 1E-6

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 8.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    gamma = 1.8
    nstim = 18
    seed = 0

    def __init__(self, *args, **kwargs):
        self.gen = np.random.RandomState(self.seed)
        self.permutation = self.gen.permutation(self.nstim)
        self.luminance_values = (np.linspace(0, 1, self.nstim) ** self.gamma)
        self.flash_amplitude = self.luminance_values[self.permutation]

        super(FullFieldFlash, self).__init__(*args, **kwargs)


# dynamically generate 20 random permutations of the fullfield flash stimulus
for ii in xrange(20):

    taskname = 'gamma_1p8_flash_%02i' % (ii + 1)
    locals().update(
        {taskname:type(taskname, (_gamma_1p8_flash,),
        {'seed':ii, 'taskname':taskname})}
    )


###############################################################################
# tests


class flash_demo(FullFieldFlash):

    # this is how the stimulus will appear in td2's menu
    taskname = 'full_field_flash_demo'
    subclass = 'test_stimuli'

    # stimulus-specific parameters
    fullfield_rgb = (0.5, 0.5, 0.5)
    background_color = (0.5, 0.5, 0.5, 1.)
    flash_hz = 2.

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 0.
    interval = 2.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    flash_amplitude = [0.1, 0.25, 0.5, 0.75, 1.0]
    nstim = 5

class sinusoid_demo(FullFieldSinusoid):

    # this is how the stimulus will appear in td2's menu
    taskname = 'full_field_sinusoid_demo'
    subclass = 'test_stimuli'

    # stimulus-specific parameters
    fullfield_rgb = (0.5, 0.5, 0.5)
    background_color = (0.5, 0.5, 0.5, 1.)
    sinusoid_hz = 5.
    phase_offset = 0    # in radians

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 0.
    interval = 2.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    sinusoid_amplitude = [0.1, 0.25, 0.5, 0.75, 1.0]
    nstim = 5