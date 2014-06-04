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
from scipy.misc import lena
from base_tasks.task_classes import *


class example_barmap(BarFlash):

    taskname = 'example_barmap'

    gridlim = (0.9, 0.9)

    # stimulus-specific parameters
    nx = 5
    ny = 5
    bar_color = (1., 1., 1., 1.)
    bar_height = 2.
    bar_width = 0.2

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 2.
    interval = 8
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 5.
    photodiodeontime = 0.075

    nstim = nx + ny
    np.random.seed(0)
    fullpermutation = permutation = np.random.permutation(nstim)


class example_dotflash(DotFlash):

    # this is how the stimulus will appear in td2's menu
    taskname = 'example_dotflash'

    # stimulus-specific parameters
    gridshape = (5, 5)
    gridlim = (0.9, 0.9)
    dot_color = (1., 1., 1., 1.)
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

    nstim = np.prod(gridshape)
    np.random.seed(0)
    fullpermutation = permutation = np.random.permutation(nstim)


class example_driftingbar(DriftingBar):

    taskname = 'example_driftingbar'

    # stimulus-specific parameters
    aperture_radius = 1.
    aperture_nvertices = 256
    bar_color = (1., 1., 1., 1.)
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

    nstim = 18
    np.random.seed(0)
    fullpermutation = permutation = np.random.permutation(18)


class example_sinusoid(DriftingSinusoid):

    taskname = 'example_sinusoid'

    # stimulus-specific parameters
    aperture_radius = 1.
    aperture_nvertices = 256
    grating_color = (1., 1., 1., 1.)
    grating_amplitude = 1.      # amplitude of luminance change (1 == max)
    grating_offset = 0.         # zero of grating (default == 0, all additive)
    grating_nsamples = 1000     # number of samples in grating
    n_cycles = 5.               # number of full cycles in texture
    grating_speed = 0.5         # phase change/frame

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 8.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 5.
    photodiodeontime = 0.075

    nstim = 18
    np.random.seed(0)
    fullpermutation = permutation = np.random.permutation(18)


class example_squarewave(DriftingSquarewave, example_sinusoid):

    taskname = 'example_squarewave'
    duty_cycle = 0.5


class example_texture(FlashingTexture):

    taskname = 'example_texture'

    # _texdata needs to be float32 and flipped along the row dimension
    img = lena().astype(np.float64)
    img = (img - img.min()) / img.ptp()
    _texdata = np.flipud(img)

    # stimulus-specific parameters
    texture_color = (0., 1., 1., 1.)

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 2.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 5.
    photodiodeontime = 0.075

    nstim = 10
