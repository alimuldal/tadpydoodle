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
import time

import OpenGL
# disable for speed?
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
import OpenGL.GL as gl

# dummy glBlendFuncSeparate in order to create instances of tasks in the
# absence of an OpenGL context
if not gl.glBlendFuncSeparate:
    gl.glBlendFuncSeparate = lambda a, b, c, d: None

import wx

import ipdb

"""
################################################################################
Conventions for stimulus orientation
################################################################################

1) Since the projector is oriented vertically, the main stimulus canvas (and the
   framebuffer) are rotated 90deg clockwise relative to the preview canvas.

      - When you are designing a stimulus, x and y coordinates should correspond
    to what you see on the preview canvas (and to what actually gets
    projected onto the screen), rather than as they appear on the stimulus
    canvas.

      - Transforming the coordinates from preview --> stimulus canvas should be
    handled within the _drawstim() method of the stimulus and *nowhere
    else*.

2) It is important to bear in mind that what the animal *actually* sees is a
   mirror image of what the projector displays (i.e. flipped in x), because the
   animal sees the 'back' surface of the translucent screen.

      - This should be corrected for at the point of analysis, *not* in the
    stimulus class itself - all coordinates, orientations etc. should look
    'correct' on the preview canvas.
"""

#
# stimulus primitives

class StaticBox(object):
    """
    Literally just a quad

    Parameters:
        rect
        color

    Methods:
        draw(color)
    """
    def __init__(self, rect=(-1, -1, 1, 1)):
        """ Create the display list """

        x0, y0, x1, y1 = rect

        self.display_list = gl.glGenLists(1)

        gl.glNewList(self.display_list, gl.GL_COMPILE)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE,
                               gl.GL_ONE, gl.GL_ZERO)

        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(x0, y1)
        gl.glVertex2f(x0, y0)
        gl.glVertex2f(x1, y0)
        gl.glVertex2f(x1, y1)
        gl.glEnd()

        gl.glDisable(gl.GL_BLEND)
        gl.glEndList()

    def draw(self, color=(1., 1., 1., 1.)):
        """ Just draw the box (can vary color) """
        gl.glColor4f(*color)
        gl.glCallList(self.display_list)

class Bar(object):

    """
    A simple rectangular bar.

    Parameters:
        width
        height
        color

    Methods:
        draw(self,x,y,z,angle,color)
    """

    def __init__(self, width, height):
        """ Create the display list """
        self.display_list = gl.glGenLists(1)

        gl.glNewList(self.display_list, gl.GL_COMPILE)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE,
                               gl.GL_ONE, gl.GL_ZERO)

        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(-width / 2., height / 2)
        gl.glVertex2f(width / 2., height / 2)
        gl.glVertex2f(width / 2., -height / 2)
        gl.glVertex2f(-width / 2., -height / 2)
        gl.glEnd()

        gl.glDisable(gl.GL_BLEND)
        gl.glEndList()

    def draw(self, x=0., y=0., z=0., angle=0., color=(1., 1., 1., 1.)):
        """ Locally translate/rotate and draw the bar """
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslate(x, y, z)
        gl.glRotate(angle, 0., 0., 1.)
        gl.glColor4f(*color)
        gl.glCallList(self.display_list)
        gl.glPopMatrix()


def get_current_bar_xy(frac, angle, radius=1, origin=(0, 0)):
    """
    Convenience function to get the current x/y position based on the
    fraction of the sweep completed and the angle of the sweep.

    The optional 'radius' and 'origin' parameters control the length of the
    sweep and the centre point that it passes through respectively.
    """
    x0, y0 = origin
    rads = np.deg2rad(angle)
    sx = x0 + radius * np.cos(rads + np.pi)
    sy = y0 + radius * np.sin(rads + np.pi)
    ex = x0 + radius * np.cos(rads)
    ey = y0 + radius * np.sin(rads)
    return sx + frac * (ex - sx), sy + frac * (ey - sy)


class Dot(object):

    """
    A simple circular dot.

    Parameters:
        radius
        nvertices
        color

    Methods:
        draw(self,x,y,z)
    """

    def __init__(self, nvertices):
        """ Create the display list """
        self.display_list = gl.glGenLists(1)
        gl.glNewList(self.display_list, gl.GL_COMPILE)

        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE,
                               gl.GL_ONE, gl.GL_ZERO)
        gl.glEnable(gl.GL_BLEND)

        gl.glBegin(gl.GL_POLYGON)
        for angle in np.linspace(0., 2 * np.pi, nvertices, endpoint=False):
            gl.glVertex2f(np.sin(angle), np.cos(angle))
        gl.glEnd()

        gl.glDisable(gl.GL_BLEND)
        gl.glEndList()

    def draw(self, x=0., y=0., z=0., r=1., color=(1., 1., 1., 1.)):
        """ Locally translate and draw the dot """
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslate(x, y, z)
        gl.glScalef(r, r, 1.)
        gl.glColor4f(*color)
        gl.glCallList(self.display_list)
        gl.glPopMatrix()


class CircularStencil(object):

    """
    A circular stencil with a hard edge. If 'polarity' is 1, the stimulus
    will be drawn only inside the circle, whereas if it is 0 the circle will
    occlude the stimulus.

    N.B. GL_STENCIL_TEST must be enabled in order for it to do anything!

    Parameters:
        nvertices
        polarity

    Methods:
        draw(self,x=0.,y=0.,z=0.)
    """

    def __init__(self, nvertices=256, polarity=1):

        self.display_list = gl.glGenLists(1)
        gl.glNewList(self.display_list, gl.GL_COMPILE)

        # don't write to pixel RGBA values
        gl.glColorMask(0, 0, 0, 0)
        gl.glDisable(gl.GL_DEPTH_TEST)

        # set the stencil buffer to 1 wherever the aperture gets drawn
        # (regardless of what the previous buffer value was)
        gl.glStencilFunc(gl.GL_ALWAYS, 1, 1)
        gl.glStencilOp(gl.GL_REPLACE, gl.GL_REPLACE, gl.GL_REPLACE)

        gl.glBegin(gl.GL_POLYGON)
        for angle in np.linspace(0., 2 * np.pi, nvertices, endpoint=False):
            gl.glVertex2f(np.sin(angle), np.cos(angle))
        gl.glEnd()

        # re-enable writing to RGBA values
        gl.glColorMask(1, 1, 1, 1)

        # we will draw our current stimulus only where the stencil
        # buffer is equal to 1
        gl.glStencilFunc(gl.GL_EQUAL, polarity, 1)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)

        gl.glEndList()

    def draw(self, x=0, y=0, z=0, r=1.):
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslate(x, y, z)
        gl.glScalef(r, r, 1.)
        gl.glCallList(self.display_list)
        gl.glPopMatrix()


class RectangularStencil(object):

    """
    A rectangular stencil with a hard edge. If 'polarity' is 1, the stimulus
    will be drawn only inside the rectangle, whereas if it is 0 the
    rectangle will occlude the stimulus.

    N.B. GL_STENCIL_TEST must be enabled in order for it to do anything!

    Parameters:
        rect (x0,y0,w,h)
        polarity

    Methods:
        draw(self,x=0.,y=0.,z=0.,angle=0)
    """

    def __init__(self, width, height, polarity=1):

        self.display_list = gl.glGenLists(1)
        gl.glNewList(self.display_list, gl.GL_COMPILE)

        # don't write to pixel RGBA values
        gl.glColorMask(0, 0, 0, 0)
        gl.glDisable(gl.GL_DEPTH_TEST)

        # set the stencil buffer to 1 wherever the aperture gets drawn
        # (regardless of what the previous buffer value was)
        gl.glStencilFunc(gl.GL_ALWAYS, 1, 1)
        gl.glStencilOp(gl.GL_REPLACE, gl.GL_REPLACE, gl.GL_REPLACE)

        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(-width / 2., -height / 2.)
        gl.glVertex2f(-width / 2., -height / 2. + height)
        gl.glVertex2f(-width / 2. + width, -height / 2. + height)
        gl.glVertex2f(-width / 2. + width, -height / 2.)
        gl.glEnd()

        # re-enable writing to RGBA values
        gl.glColorMask(1, 1, 1, 1)

        # we will draw our current stimulus only where the stencil
        # buffer is equal to 1
        gl.glStencilFunc(gl.GL_EQUAL, polarity, 1)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)

        gl.glEndList()

    def draw(self, x=0, y=0, z=0, angle=0):
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glTranslate(x, y, z)
        gl.glRotate(angle, 0, 0, 1)
        gl.glCallList(self.display_list)
        gl.glPopMatrix()

class TextureQuad2D(object):

    """
    A 2D luminance-format textured quad with wrapping

    Parameters:
        texdata
        color
        rect

    Methods:
        draw(self,translation,rotation)
    """

    def __init__(self, texdata, rect=(-1., -1., 1., 1.), smooth=True):

        if smooth:
            filt = gl.GL_LINEAR
        else:
            filt = gl.GL_NEAREST

        # build the texture
        self.texture = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER, filt)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER, filt)

        # set the swizzle mask to map R -> (G, B), 1 -> A
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_SWIZZLE_G, gl.GL_RED)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_SWIZZLE_B, gl.GL_RED)
        gl.glTexParameterf(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_SWIZZLE_A, gl.GL_ONE)
        h, w = texdata.shape

        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_R16_SNORM, w, h, 0, gl.GL_LUMINANCE,
            gl.GL_FLOAT, texdata
        )

        # display list for the texture
        # --------------------------------------------------------------
        display_list = gl.glGenLists(1)
        gl.glNewList(display_list, gl.GL_COMPILE)

        gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE,
                               gl.GL_ONE, gl.GL_ZERO)
        gl.glEnable(gl.GL_TEXTURE_2D)

        x0, y0, x1, y1 = rect

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(x0, y1)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(x0, y0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(x1, y0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(x1, y1)
        gl.glEnd()

        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_BLEND)

        gl.glEndList()
        # --------------------------------------------------------------

        self.display_list = display_list

        pass


    def draw(self, offset=0., angle=0., color=(1., 1., 1., 1.)):
        """
        Translate/rotate within texture coordinates, then draw the
        texture
        """

        # we work on the texture matrix for now
        gl.glMatrixMode(gl.GL_TEXTURE)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)

        # we move in the opposite direction in texture coords
        gl.glTranslate(-offset, 0, 0)
        gl.glRotatef(-angle, 0, 0, 1)
        gl.glColor4f(*color)

        gl.glCallList(self.display_list)

        # we pop and go BACK to the modelview matrix for safety!!!
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

class TextureQuad1D(object):

    """
    A 1D luminance-format textured quad with wrapping, ideal for displaying
    repetative contrast gratings.

    Parameters:
        texdata
        color
        rect

    Methods:
        draw(self,translation,rotation)
    """

    def __init__(self, texdata, rect=(-1., -1., 1., 1.), smooth=True):

        if smooth:
            filt = gl.GL_LINEAR
        else:
            filt = gl.GL_NEAREST

        # build the texture
        self.texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.texture)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE)
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MAG_FILTER, filt)
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER, filt)

        # set the swizzle mask to map R -> (G, B), 1 -> A
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_SWIZZLE_G, gl.GL_RED)
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_SWIZZLE_B, gl.GL_RED)
        gl.glTexParameterf(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_SWIZZLE_A, gl.GL_ONE)

        gl.glTexImage1D(gl.GL_TEXTURE_1D, 0, gl.GL_R16_SNORM, len(texdata),
                        0, gl.GL_LUMINANCE, gl.GL_FLOAT, texdata)

        # display list for the texture
        # --------------------------------------------------------------
        display_list = gl.glGenLists(1)
        gl.glNewList(display_list, gl.GL_COMPILE)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE,
                               gl.GL_ONE, gl.GL_ZERO)
        gl.glEnable(gl.GL_TEXTURE_1D)

        x0, y0, x1, y1 = rect

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(x0, y1)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(x0, y0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(x1, y0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(x1, y1)
        gl.glEnd()

        gl.glDisable(gl.GL_TEXTURE_1D)
        gl.glDisable(gl.GL_BLEND)

        gl.glPopMatrix()

        gl.glEndList()
        # --------------------------------------------------------------

        self.display_list = display_list

    def draw(self, offset=0., angle=0., color=(1., 1., 1., 1.)):
        """
        Translate/rotate within texture coordinates, then draw the
        texture
        """

        # we work on the texture matrix for now
        gl.glMatrixMode(gl.GL_TEXTURE)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glBindTexture(gl.GL_TEXTURE_1D, self.texture)

        # we move in the opposite direction in texture coords
        gl.glTranslatef(-offset, 0, 0)
        gl.glRotatef(-angle, 0, 0, 1)

        # draw the texture
        gl.glColor4f(*color)
        gl.glCallList(self.display_list)

        # we pop and go BACK to the modelview matrix for safety!!!
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

#
# base class


class Task(object):

    """
    Base class for all tasks.

    Implements:
        __init__
        _reinit
        _buildtimes
        _buildparamsdict
        _display
    """

    currentframe = -1
    dt = -1
    background_color = (0., 0., 0., 0.)

    # this determines the ratio of width:height for the stimulus box
    area_aspect = 1.

    def __init__(self, canvas=None):
        self._canvas = canvas
        self.starttime = -1
        self._buildstim()
        self._buildtimes()
        self._buildparamsdict()
        pass

    def _reinit(self):
        """
        return the stimulus to its initialised state
        """
        self.starttime = -1
        self._buildtimes()
        self._buildstim()

    def _buildtimes(self):
        """
        get the theoretical stimulus and photodiode times, initialise
        the actual times
        """

        # theoretical stimulus times
        self.ontimes = self.interval * np.arange(self.nstim)
        self.offtimes = self.ontimes + self.on_duration
        self.theoreticalstimtimes = (self.initblanktime + self.ontimes)
        self.finishtime = (self.initblanktime
                           + self.finalblanktime
                           + self.offtimes[-1])
        # theoretical scan times
        self.frametimes = np.arange(0., self.finishtime, 1. / self.scan_hz)
        self.nframes = self.frametimes.size

        self.actualstimtimes = -1. * np.ones(self.nstim)
        self.finished = False
        self.dt = -1.
        self.currentframe = 0
        self.currentstim = -1
        self.on_flag = False
        self.off_flag = False
        self.stim_on_last_frame = False
        pass

    def _buildparamsdict(self):
        """
        build the 'paramsdict' by introspection
        """
        pd = {}
        for name in dir(self):
            if not name.startswith('_'):
                pd.update({name: self.__getattribute__(name)})
        self.paramsdict = pd

    def _display(self):
        """
        draw the current stimulus state to the glcanvas
        """

        # we haven't started yet
        if self.starttime == -1:
            self.starttime = time.time()

        # we've started
        else:
            # time since we started
            dt = time.time() - self.starttime

            # if we haven't displayed all of the frames yet...
            if self.currentframe < (self.nframes - 1):
                # ...and if it's after the start time of the next frame...
                if dt > self.frametimes[self.currentframe + 1]:
                    # ...increment the current frame
                    self.currentframe += 1

            # if it's before the end of the photodiode on period,
            # set the photodiode trigger on
            new_photodiode_state = (
                dt < (self.frametimes[self.currentframe]
                      + self.photodiodeontime)
            )
            self._canvas.do_refresh_photodiode = (
                self._canvas.master.show_photodiode != new_photodiode_state)
            self._canvas.master.show_photodiode = new_photodiode_state

            timeafterinitblank = dt - self.initblanktime

            # check if we're still in the initial blank period
            if timeafterinitblank > 0.:

                # if we haven't displayed all of the stimuli yet...
                if self.currentstim < (self.nstim - 1):
                    # and if it's after the start time of the next stimulus...
                    if timeafterinitblank > self.ontimes[self.currentstim + 1]:
                        # ...increment the current stimulus
                        self.currentstim += 1
                        self.on_flag = False

                # are we in the "ON" period of this stimulus?
                if timeafterinitblank < self.offtimes[self.currentstim]:

                    # do the actual drawing
                    #-------------------------------
                    self._drawstim()
                    #-------------------------------

                    # force a re-draw of the stimulus area
                    self._canvas.do_refresh_stimbox = True

                    # make sure we re-draw one more time
                    # after the stimulus has finished
                    self.stim_on_last_frame = True

                    # get the actual ON time for this
                    # stimulus
                    if not self.on_flag:
                        recalcdt = time.time() - self.starttime
                        self.actualstimtimes[self.currentstim] = recalcdt
                        self.on_flag = True

                elif self.stim_on_last_frame:
                    self._canvas.do_refresh_stimbox = True
                    self.stim_on_last_frame = False

                if dt > self.finishtime and not self.finished:
                    self.finished = True
                    ctrl = self._canvas.master.controlwindow
                    pd_checkbox = (
                        ctrl.optionpanel.checkboxes['show_photodiode'])
                    pd_checkbox.ref.set(False)
                    self._canvas.master.show_photodiode = False
                    self._canvas.do_refresh_everything = True
                    wx.Bell()

                    print "Task '%s' finished: %s" % (
                        self.taskname, time.asctime())
                    print("Absolute difference between "
                          "theoretical and actual stimulus times:")
                    print np.abs(
                        self.actualstimtimes - self.theoreticalstimtimes)

                    if not self._canvas.master.auto_start_tasks:
                        ctrl.playlistpanel.onRunTask()
                    ctrl.playlistpanel.Next()

            self.dt = dt

#
# stimulus subtypes


class DotFlash(Task):

    """
    Base class for flashing dot stimuli

    Implements:
        _make_positions
        _buildstim
        _drawstim
    """

    # the name of the stimulus subclass
    subclass = 'dot_flash'

    def _make_positions(self):

        assert len(self.permutation) == self.nstim

        # generate a random permutation of x,y coordinates
        nx, ny = self.gridshape
        x_vals = np.linspace(-1, 1, nx) * self.gridlim[0] * self.area_aspect
        y_vals = np.linspace(-1, 1, ny) * self.gridlim[1]
        x, y = np.meshgrid(x_vals, y_vals)
        self.xpos = x.ravel()[self.permutation]
        self.ypos = y.ravel()[self.permutation]

    def _buildstim(self):
        """
        construct a generic flashing dot stimulus
        """
        self._make_positions()

        # create the dot
        self._dot = Dot(self.nvertices)
        pass

    def _drawstim(self):
        # draw the dot in the current position
        self._dot.draw(self.xpos[self.currentstim],
                       self.ypos[self.currentstim],
                       0.,
                       self.radius,
                       self.dot_color
                       )


class WeberDotFlash(DotFlash):
    """
    Flashing dots with pseudorandom positions and luminance values.
    Luminance values are distributed on a log scale.

    Implements:
        _make_positions
        _drawstim
    """

    subclass = 'weber_dot_flash'

    def _make_positions(self):

        assert len(self.permutation) == self.nstim

        # generate a random permutation of x,y coordinates and
        # luminances
        nx, ny = self.gridshape
        x_vals = np.linspace(-1, 1, nx) * self.gridlim[0] * self.area_aspect
        y_vals = np.linspace(-1, 1, ny) * self.gridlim[1]

        nl = self.n_luminances

        # necessary in order to get negative luminance increments to work
        sign = np.sign(self.luminance_range).min()
        lmin, lmax = np.abs(self.luminance_range)
        l_vals = (np.linspace(lmin, lmax, nl) ** self.dot_gamma) * sign

        x, y, l = np.meshgrid(x_vals, y_vals, l_vals)
        self.xpos = x.flat[self.permutation]
        self.ypos = y.flat[self.permutation]
        l = l.flat[self.permutation]

        self.dot_color = np.zeros((self.nstim, 4))
        self.dot_color[:, :3] = self.dot_rgb
        self.dot_color[:, 3] = l

    def _drawstim(self):
        # draw the dot in the current position
        self._dot.draw(self.xpos[self.currentstim],
                       self.ypos[self.currentstim],
                       0.,
                       self.radius,
                       self.dot_color[self.currentstim]
                       )

class OnOffDotFlash(DotFlash):
    """
    Dots with a step increment or decrement in luminance relative to the
    stimulus background

    Implements:
        _make_positions
        _drawstim
    """

    subclass = 'on_off_dot_flash'

    def _make_positions(self):

        assert len(self.permutation) == self.nstim

        # generate a random permutation of x,y coordinates and
        # luminances
        nx, ny = self.gridshape
        x_vals = np.linspace(-1, 1, nx) * self.gridlim[0] * self.area_aspect
        y_vals = np.linspace(-1, 1, ny) * self.gridlim[1]

        l_vals = self.luminance_step, -self.luminance_step

        x, y, l = np.meshgrid(x_vals, y_vals, l_vals)
        self.xpos = x.flat[self.permutation]
        self.ypos = y.flat[self.permutation]
        l = l.flat[self.permutation]

        self.dot_color = np.zeros((self.nstim, 4))
        self.dot_color[:, :3] = self.dot_rgb * l[:, None]
        self.dot_color[:, 3] = 1.

    def _drawstim(self):
        # draw the dot in the current position
        self._dot.draw(self.xpos[self.currentstim],
                       self.ypos[self.currentstim],
                       0.,
                       self.radius,
                       self.dot_color[self.currentstim]
                       )

class MultiSizeDotFlash(DotFlash):
    """
    Dots with multiple different radii

    Implements:
        _make_positions
        _drawstim
    """

    subclass = 'multi_size_dot_flash'

    def _make_positions(self):

        assert len(self.permutation) == self.nstim

        r = self.radii

        # dynamically define the grid limits based on the dot radii
        self.gridlim = (self.area_aspect - r.max(), 1. - r.max())

        # generate a random permutation of x,y coordinates and
        # radii
        nx, ny = self.gridshape
        x_vals = np.linspace(-1, 1, nx) * self.gridlim[0] * self.area_aspect
        y_vals = np.linspace(-1, 1, ny) * self.gridlim[1]


        x, y, r = np.meshgrid(x_vals, y_vals, r)
        self.xpos = x.flat[self.permutation]
        self.ypos = y.flat[self.permutation]
        self.radius = r.flat[self.permutation]

    def _drawstim(self):
        # draw the dot in the current position
        self._dot.draw(self.xpos[self.currentstim],
                       self.ypos[self.currentstim],
                       0.,
                       self.radius[self.currentstim],
                       self.dot_color
                       )



class FullFieldFlash(Task):
    """
    A full field flashing stimulus

    Implements:
        _buildstim
        _drawstim
    """

    subclass = 'full_field_flash'

    def _buildstim(self):
        self._box = StaticBox()

    def _drawstim(self):

        # update the current polarity
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        period = (1. / self.flash_hz)
        polarity = 2. * ((on_dt % period) < (period / 2.)) - 1
        alpha = polarity * self.flash_amplitude[self.currentstim]

        # draw the texture
        self._box.draw(color=(self.fullfield_rgb + (alpha,)))

class FullFieldSinusoid(FullFieldFlash):
    """
    A full field sinusoidal stimulus
    """

    def _drawstim(self):

        # current phase
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        phase = np.sin(2 * np.pi * on_dt * self.sinusoid_hz +
                       self.phase_offset)
        alpha = phase * self.sinusoid_amplitude[self.currentstim]

        # draw the texture
        self._box.draw(color=(self.fullfield_rgb + (alpha,)))

class BarFlash(Task):

    """
    Base class for flashing bar stimuli

    Implements:
        _buildstim
        _drawstim
    """

    subclass = 'bar_flash'

    def _make_positions(self):

        assert len(self.permutation) == self.nstim

        nx, ny = self.nx, self.ny
        x_vals = np.zeros((nx + ny), dtype=np.float32)
        y_vals = np.zeros((nx + ny), dtype=np.float32)
        orientations = np.zeros((nx + ny), dtype=np.float32)

        x_vals[:nx] = np.linspace(-1, 1, nx) * \
            self.gridlim[0] * self.area_aspect
        orientations[nx:] = 90.
        y_vals[nx:] = np.linspace(-1, 1, ny) * self.gridlim[1]

        self.xpos = x_vals[self.permutation]
        self.ypos = y_vals[self.permutation]
        self.orientation = orientations[self.permutation]

    def _buildstim(self):
        self._make_positions()
        self._bar = Bar(width=self.bar_width,
                        height=self.bar_height
                        )

    def _drawstim(self):

        # update the current polarity
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        period = (1. / self.flash_hz)
        is_on = (on_dt % period) < (period / 2.)
        alpha = is_on * self.flash_amplitude

        # draw the bar in the current position/orientation
        self._bar.draw(self.xpos[self.currentstim],
                       self.ypos[self.currentstim],
                       angle=self.orientation[self.currentstim],
                       color=self.bar_rgb + (alpha,))


class DriftingBar(Task):

    """
    Base class for drifting bar stimuli

    Implements:
        _make_orientations
        _buildstim
        _drawstim

    """

    subclass = 'drifting_bar'

    def _make_orientations(self):

        assert len(self.permutation) == self.nstim

        # direction for each bar sweep
        orientation = np.linspace(
            0., 360., len(self.fullpermutation), endpoint=False)

        # do the shuffling
        self.orientation = orientation[self.permutation]

    def _buildstim(self):

        self._make_orientations()
        self._bar = Bar(width=self.bar_width,
                        height=self.bar_height
                        )

        self._aperture = CircularStencil(nvertices=self.aperture_nvertices,
                                         polarity=1)

    def _drawstim(self):

        # get the current bar position (ROTATED 90o!)
        bar_dt = self.dt - \
            (self.initblanktime + self.ontimes[self.currentstim])
        frac = bar_dt / \
            (self.offtimes[self.currentstim] - self.ontimes[self.currentstim])
        x, y = get_current_bar_xy(frac,
                                  self.orientation[self.currentstim],
                                  radius=max(1, self.area_aspect))

        # enable stencil test, draw the aperture to the stencil buffer
        gl.glEnable(gl.GL_STENCIL_TEST)
        self._aperture.draw(r=self.aperture_radius)

        # draw the bar (ROTATED 90o!), disable stencil test
        self._bar.draw(x, y, 0,
                       angle=self.orientation[self.currentstim],
                       color=self.bar_color
                       )
        gl.glDisable(gl.GL_STENCIL_TEST)

        pass

class MultiSpeedBars(DriftingBar):
    """
    Drifting bar with multiple speeds/orientations

    needs:
        self.bar_speeds (deg/sec)
        self.n_orientations

    """

    subclass = 'multi_speed_bars'

    def _make_orientations(self):

        # might want to dynamically generate speeds...
        self.n_speeds = len(self.bar_speeds)

        # assuming that speeds are in deg/s, 90x90 deg stimulus area
        unique_speeds = self.bar_speeds

        unique_orientations = np.linspace(0, 360, self.n_orientations,
                                          endpoint=False)

        ori, speed = np.meshgrid(unique_orientations, unique_speeds)

        self.orientation = ori.flat[self.permutation]
        self.speed = speed.flat[self.permutation]

        self.on_duration = 90. / self.speed

        pass

    def _buildstim(self):

        self._make_orientations()

        self._bar = Bar(width=self.bar_width,
                        height=self.bar_height
                        )

        self._aperture = CircularStencil(nvertices=self.aperture_nvertices,
                                         polarity=1)

        pass

    pass


class OccludedDriftingBar(DriftingBar):

    """
    Drifting bar with a rectangular 'occluded' region

    Implements:
        _make_orientations
        _buildstim
        _drawstim
    """
    subclass = 'occluded_drifting_bar'

    def _make_orientations(self):

        assert len(self.permutation) == self.nstim

        # angle = np.repeat(self.angles,self.full_nstim//2)
        occluder_pos = np.linspace(
            -1. + (self.occluder_width / 2.),
            1. - (self.occluder_width / 2.),
            self.n_occluder_positions
        ) * self.area_aspect

        # make a list of tuples (angle,position)
        states = []
        for angle in self.angles:
            for x0 in occluder_pos:
                states.append((angle, x0))

        # now we shuffle the stimulus
        states = [states[ii] for ii in self.permutation]

        self.orientation, self.occluder_pos = zip(*states)

    def _buildstim(self):

        self._make_orientations()
        self._bar = Bar(width=self.bar_width,
                        height=self.bar_height
                        )

        self._aperture = RectangularStencil(
            width=self.occluder_width * self.area_aspect,
            height=self.occluder_height,
            polarity=0)

    def _drawstim(self):

        # get the current bar position (ROTATED 90o!)
        bar_dt = self.dt - \
            (self.initblanktime + self.ontimes[self.currentstim])
        frac = bar_dt / \
            (self.offtimes[self.currentstim] - self.ontimes[self.currentstim])
        x, y = get_current_bar_xy(frac,
                                  self.orientation[self.currentstim],
                                  radius=max(1, self.area_aspect))

        # enable stencil test, draw the aperture to the stencil buffer
        gl.glEnable(gl.GL_STENCIL_TEST)
        self._aperture.draw(x=self.occluder_pos[self.currentstim])

        # draw the bar (ROTATED 90o!), disable stencil test
        self._bar.draw(x, y, 0,
                       angle=self.orientation[self.currentstim],
                       color=self.bar_color)
        gl.glDisable(gl.GL_STENCIL_TEST)

        pass


class DriftingGrating(Task):

    """
    Base class for drifting texture stimuli

    Implements:
        _make_orientations
        _buildstim
        _drawstim
    """

    def _make_orientations(self):

        assert len(self.permutation) == self.nstim

        orientation = np.linspace(
            0., 360., len(self.fullpermutation), endpoint=False)

        # do the shuffling
        orientation = orientation[self.permutation]
        self.orientation = orientation

        pass

    def _buildstim(self):
        self._make_orientations()
        self._make_grating()
        self._texture = TextureQuad1D(texdata=self._texdata,
                                      rect=(-1, -1, 1, 1))

        self._aperture = CircularStencil(nvertices=self.aperture_nvertices,
                                         polarity=1)

        pass

    def _drawstim(self):

        # update the current phase angle
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        self._phase = on_dt * (self.grating_speed / 90.)

        # enable stencil test, draw the aperture to the stencil buffer
        gl.glEnable(gl.GL_STENCIL_TEST)
        self._aperture.draw(r=self.aperture_radius)

        # draw the texture, disable stencil test
        self._texture.draw(offset=self._phase,
                           # correction for unit circle
                           angle=self.orientation[self.currentstim],
                           color=self.grating_color
                           )
        gl.glDisable(gl.GL_STENCIL_TEST)

        pass


class DriftingSinusoid(DriftingGrating):

    """
    Base class for drifting bar stimuli

    Implements:
        _make_grating
    """

    subclass = 'drifting_sinusoid'

    def _make_grating(self):

        phaseangle = np.linspace(
            0, 2 * np.pi * self.n_cycles, self.grating_nsamples)

        sinusoid = np.float32(np.sin(phaseangle)) / 2.  # range [-0.5, 0.5]
        sinusoid *= self.grating_amplitude              # scaling
        sinusoid += 0.5 + self.grating_offset           # offset origin

        self._texdata = sinusoid
        self._phase = 0


class DriftingSquarewave(DriftingGrating):

    """
    Base class for drifting bar stimuli

    Implements:
        _make_grating
    """

    subclass = 'drifting_squarewave'

    def _make_grating(self):

        t = np.arange(self.grating_nsamples)
        period = self.grating_nsamples // self.n_cycles

        # range [-0.5, 0.5]
        squarewave = np.float32(rectwave(t, period, self.duty_cycle)) - 0.5
        squarewave *= self.grating_amplitude        # scaling
        squarewave += 0.5 + self.grating_offset     # offset origin
        # squarewave = np.zeros(self.grating_nsamples)
        # squarewave[:10] = 1

        self._texdata = squarewave
        self._phase = 0

class MultiSpeedSquarewave(DriftingSquarewave):

    subclass = 'multi_speed_squarewave'

    def _make_orientations(self):

        # might want to dynamically generate speeds...
        self.n_speeds = len(self.grating_speeds)

        # assuming that speeds are in deg/s, 90x90 deg stimulus area
        unique_speeds = self.grating_speeds

        unique_orientations = np.linspace(0, 360, self.n_orientations,
                                          endpoint=False)

        ori, speed = np.meshgrid(unique_orientations, unique_speeds)

        self.orientation = ori.flat[self.permutation]
        self.speed = speed.flat[self.permutation]

        pass

    def _drawstim(self):

        # update the current phase angle
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        self._phase = on_dt * (self.speed[self.currentstim] / 90.)

        # enable stencil test, draw the aperture to the stencil buffer
        gl.glEnable(gl.GL_STENCIL_TEST)
        self._aperture.draw(r=self.aperture_radius)

        # draw the texture, disable stencil test
        self._texture.draw(offset=self._phase,
                           # correction for unit circle
                           angle=self.orientation[self.currentstim],
                           color=self.grating_color
                           )
        gl.glDisable(gl.GL_STENCIL_TEST)

    pass

class FlashingTexture(Task):
    """
    Very basic class for flashing texture stimuli

    Implements:
        _make_texdata
        _buildstim
        _drawstim
    """

    subclass = 'flashing_texture'

    def _make_texdata(self):
        # raise NotImplementedError('Override me in a subclass!')
        pass

    def _buildstim(self):
        self._make_texdata()
        self._texture = TextureQuad2D(texdata=self._texdata,
                                      rect=(-1, -1, 1, 1))

    def _drawstim(self):
        # draw the texture
        self._texture.draw(color=self.texture_color)

def rectwave(t, period=10, duty_cycle=0.5):
    return (t % period) <= period * duty_cycle


class FlashingCheckerboard(FlashingTexture):
    """
    A flashing checkerboard with variable contrast, baseline luminance

    Implements:
        _make_texdata
        _buildstim
        _drawstim
    """

    subclass = 'flashing_checkerboard'

    def _make_texdata(self):

        self._texdata = np.zeros(self.gridshape, dtype=np.float32) - 0.5
        self._texdata[0::2, 0::2] += 1.
        self._texdata[1::2, 1::2] += 1.

    def _buildstim(self):
        self._make_texdata()
        self._texture = TextureQuad2D(texdata=self._texdata,
                                      rect=(-1, -1, 1, 1), smooth=False)
    def _drawstim(self):

        # update the current polarity
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        period = (1. / self.flash_hz)
        polarity = 2. * ((on_dt % period) < (period / 2.)) - 1
        alpha = polarity * self.flash_amplitude[self.currentstim]

        # draw the texture
        self._texture.draw(color=(self.checker_rgb + (alpha,)))

class SinusoidCheckerboard(FlashingCheckerboard):

    def _drawstim(self):

        # current phase
        on_dt = self.dt - (self.initblanktime + self.ontimes[self.currentstim])
        phase = np.sin(2 * np.pi * on_dt * self.sinusoid_hz +
                       self.phase_offset)
        alpha = phase * self.sinusoid_amplitude[self.currentstim]

        # draw the texture
        self._texture.draw(color=(self.checker_rgb + (alpha,)))