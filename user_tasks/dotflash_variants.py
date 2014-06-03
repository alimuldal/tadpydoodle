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
from base_tasks.task_classes import DotFlash,WeberDotFlash

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
    31, 20, 16, 30, 22, 15, 10,  2, 11, 29, 27, 35, 33, 28, 32,  8, 13,  5, 
    17, 14,  7, 26,  1, 12, 25, 24,  6, 23,  4, 18, 21, 19,  9, 34,  3,  0])
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

class inverted_dotflash1_2hz(inverted_dotflash1):
    taskname = "inverted_dotflash1_2hz"
    scan_hz = 2.

class inverted_dotflash2_2hz(inverted_dotflash2):
    taskname = "inverted_dotflash2_2hz"
    scan_hz = 2.

class inverted_dotflash1_2hz_005(inverted_dotflash1_2hz):
    taskname = 'inverted_dotflash1_2hz_005'
    background_color = (0.05,0.05,0.05,1.0)

class inverted_dotflash2_2hz_005(inverted_dotflash2_2hz):
    taskname = 'inverted_dotflash2_2hz_005'
    background_color = (0.05,0.05,0.05,1.0)

class inverted_dotflash1_2hz_02(inverted_dotflash1_2hz):
    taskname = 'inverted_dotflash1_2hz_02'
    background_color = (0.2,0.2,0.2,1.0)

class inverted_dotflash2_2hz_02(inverted_dotflash2_2hz):
    taskname = 'inverted_dotflash2_2hz_02'
    background_color = (0.2,0.2,0.2,1.0)

class inverted_dotflash1_2hz_04(inverted_dotflash1_2hz):
    taskname = 'inverted_dotflash1_2hz_04'
    background_color = (0.4,0.4,0.4,1.0)

class inverted_dotflash2_2hz_04(inverted_dotflash2_2hz):
    taskname = 'inverted_dotflash2_2hz_04'
    background_color = (0.4,0.4,0.4,1.0)

class inverted_dotflash1_2hz_07(inverted_dotflash1_2hz):
    taskname = 'inverted_dotflash1_2hz_07'
    background_color = (0.7,0.7,0.7,1.0)

class inverted_dotflash2_2hz_07(inverted_dotflash2_2hz):
    taskname = 'inverted_dotflash2_2hz_07'
    background_color = (0.7,0.7,0.7,1.0)


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
    area_aspect = 2     # twice as wide as high

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 8
    on_duration = 1

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

class resp_map(DotFlash):
    """
    Quick-and-dirty assessment of responses in different parts of the
    stimulus area
    """

    # this is how the stimulus will appear in td2's menu
    taskname = 'resp_map'

    # stimulus-specific parameters
    gridshape = (4,4)
    gridlim = (0.9,0.9)
    dot_color = (1.,1.,1.,1.)
    radius = 0.1
    nvertices = 64

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 5
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    nstim = np.prod(gridshape)
    permutation = np.arange(np.prod(gridshape))

    def _buildtimes(self):
        super(DotFlash,self)._buildtimes()
        self._stimon_prev = False

    def print_pos(self):
        nx,ny = self.gridshape
        idx = np.unravel_index(self.currentstim,(nx,ny))
        printgrid(nx,ny,idx)

    def _display(self):
        super(DotFlash,self)._display()
        if self.stim_on_last_frame and not self._stimon_prev:
            self.print_pos()
        self._stimon_prev = self.stim_on_last_frame

def printgrid(nx,ny,idx):
    gridstr = ''
    for ii in xrange(ny):
        gridstr = '-'*4*nx + '\n' + gridstr
        gridstr = ''.join(
            ['| O ' if (ii,jj) == idx else  '|   ' for jj in xrange(nx)]
            ) + '|\n' + gridstr
    gridstr = '-'*4*nx + '\n' + gridstr
    print gridstr

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


class weber_dotflash1(WeberDotFlash):
    """
    Flashing dots with pseudorandom positions and luminances.
    """

    taskname = 'weber_dotflash1'

    # stimulus-specific parameters
    gridshape = (5,5)
    gridlim = (0.9,0.9)
    radius = 0.075
    nvertices = 64

    n_luminances = 5
    luminance_range = (0.,1.)

    # approximate exponent for psychophysical contrast curve. this is used
    # to select reasonably-spaced luminance values.
    gamma = 1.8

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 8
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    full_nstim = np.prod(gridshape + (n_luminances,))
    #-----------------------------------------------------------------------
    gen = np.random.RandomState(0)
    fullpermutation = gen.permutation(full_nstim)

    #-----------------------------------------------------------------------

    # take the first 25 of the full 125 states
    nstim = 25
    permutation = fullpermutation[(0*nstim):(1*nstim)]

class weber_dotflash2(weber_dotflash1):
    taskname = 'weber_dotflash2'

    # take the second 25 of the full 125 states
    nstim = 25
    permutation = weber_dotflash1.fullpermutation[(1*nstim):(2*nstim)]

class weber_dotflash3(weber_dotflash1):
    taskname = 'weber_dotflash3'

    # take the second 25 of the full 125 states
    nstim = 25
    permutation = weber_dotflash1.fullpermutation[(2*nstim):(3*nstim)]

class weber_dotflash4(weber_dotflash1):
    taskname = 'weber_dotflash4'

    # take the second 25 of the full 125 states
    nstim = 25
    permutation = weber_dotflash1.fullpermutation[(3*nstim):(4*nstim)]

class weber_dotflash5(weber_dotflash1):
    taskname = 'weber_dotflash5'

    # take the second 25 of the full 125 states
    nstim = 25
    permutation = weber_dotflash1.fullpermutation[(4*nstim):(5*nstim)]

# class widescreen_dotflash3(widescreen_dotflash1):
#   taskname = 'widescreen_dotflash3'
#   fullpermutation = widescreen_dotflash1.fullpermutation
#   nstim = widescreen_dotflash1.nstim
#   part = 3
#   permutation = fullpermutation[(part-1)*nstim:part*nstim]

# class widescreen_dotflash4(widescreen_dotflash1):
#   taskname = 'widescreen_dotflash4'
#   fullpermutation = widescreen_dotflash1.fullpermutation
#   nstim = widescreen_dotflash1.nstim
#   part = 4
#   permutation = fullpermutation[(part-1)*nstim:part*nstim]


class interlaced_8x8_1(dotflash1):
    """
    An 8x8 grid, which is presented as a set of interleaved 8x8 grids
    """

    # this is how the stimulus will appear in td2's menu
    taskname = 'interlaced_8x8_1'

    # stimulus-specific parameters
    gridshape = (8, 8)

    # stimulus timing
    initblanktime = 2.
    finalblanktime = 10.
    interval = 8.
    on_duration = 1.

    # photodiode triggering parameters
    scan_hz = 2.
    photodiodeontime = 0.075

    # 16/64 positions
    nstim = 16

    # start with the bottom left corner

    # allpos = np.arange(64).reshape(8, 8)
    # permutation = allpos[::2, ::2].flat[np.random.permutation(nstim)]

    permutation = np.array(
        [38, 16, 20, 22,  6, 52, 34, 32, 18,  2,  0, 48, 50,  4, 54, 36]
    )

class interlaced_8x8_2(interlaced_8x8_1):

    taskname = 'interlaced_8x8_2'
    # offset by 1 in y

    # allpos = np.arange(64).reshape(8, 8)
    # permutation = allpos[1::2, ::2].flat[np.random.permutation(nstim)]

    permutation = np.array(
        [28, 26, 40, 10,  8, 24, 12, 56, 60, 58, 46, 42, 14, 44, 30, 62]
    )

class interlaced_8x8_3(interlaced_8x8_1):

    taskname = 'interlaced_8x8_3'

    # offset by 1 in x

    # allpos = np.arange(64).reshape(8, 8)
    # permutation = allpos[::2, 1::2].flat[np.random.permutation(nstim)]

    permutation = np.array(
        [53,  7,  5, 37,  1, 35, 55, 39, 51, 19, 33, 21, 23, 17, 49,  3]
    )

class interlaced_8x8_4(interlaced_8x8_1):

    taskname = 'interlaced_8x8_4'

    # offset by 1 in x & y

    # allpos = np.arange(64).reshape(8, 8)
    # permutation = allpos[1::2, 1::2].flat[np.random.permutation(nstim)]

    permutation = np.array(
        [15, 45, 31, 47, 63, 61, 11, 41, 43,  9, 59, 13, 27, 29, 57, 25]
    )

################################################################################
# tests

class position_test(widescreen_dotflash1):
    taskname = 'position_test'
    subclass = 'test_stimuli'

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

