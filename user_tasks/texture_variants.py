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
from base_tasks.task_classes import (FlashingTexture, FlashingCheckerboard, 
    SinusoidCheckerboard)

class flashing_checkerboard_demo(FlashingCheckerboard):

    # this is how the stimulus will appear in td2's menu
    taskname = 'flash_checker_contrast_demo'
    subclass = 'test_stimuli'

    # stimulus-specific parameters
    gridshape = (6, 6)
    checker_rgb = (1., 1., 1.)
    background_color = (0.5, 0.5, 0.5, 1.)
    flash_hz = 2.

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 0.
    interval = 8.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    flash_amplitude = [0.1, 0.25, 0.5, 0.75, 1.0]
    nstim = 5

class sinusoidal_checkerboard_demo(SinusoidCheckerboard):

    # this is how the stimulus will appear in td2's menu
    taskname = 'sinusoidal_checker_contrast_demo'
    subclass = 'test_stimuli'

    # stimulus-specific parameters
    gridshape = (6, 6)
    checker_rgb = (1., 1., 1.)
    background_color = (0.5, 0.5, 0.5, 1.)
    sinusoid_hz = 2.
    phase_offset = 0.   # in radians

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 0.
    interval = 8.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    sinusoid_amplitude = [0.1, 0.25, 0.5, 0.75, 1.0]
    nstim = 5