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

import wx
import multiprocessing
from ConfigParser import SafeConfigParser
import os
import copy
import imp
import inspect
import time

import glcanvases as glc
reload(glc)
import gui_elements as gui
reload(gui)
import render_timer as rt
reload(rt)

__version__ = "1.0"


class AppThread(multiprocessing.Process):

    # default configuration: [section] variable = value
    template = {
        'window': {'x_resolution': 800, 'y_resolution': 600,
                     'fullscreen': False, 'on_top': True, 'gamma': 1.7},
        'photodiode': {'show_photodiode': True, 'p_xpos': 300.,
                         'p_ypos': 100., 'p_scale': 20.},
        'crosshairs': {'show_crosshairs': True, 'c_xpos': 300.,
                         'c_ypos': 600., 'c_scale': 145.},
        'stimulus': {'show_preview': True, 'log_framerate': False,
                     'log_nframes': 10000, 'run_loop': True, 'vblank_mode': -1,
                     'min_delta_t': 2., 'framerate_window': 100},
        'playlist': {'playlist_directory': 'playlists',
                     'repeat_playlist': True, 'auto_start_tasks': False}
    }

    # configuration file
    configroot = '~/.tadpydoodle'
    configfile = 'tadpydoodlerc'

    # tasks
    base_taskdir = './base_tasks'
    user_taskdir = './user_tasks'
    run_task = False
    current_task = None
    taskdict = None

    def run(self):

        print "Starting TadPyDoodle v%s" % __version__
        app = wx.PySimpleApp()

        print "Loading configuration..."
        self.loadConfig()

        # setting this environment variable forces vsync on/off (on my
        # Acer laptop, Intel Sandy Bridge built-in grapics...)
        if self.vblank_mode != -1:
            os.environ.update({'vblank_mode': str(self.vblank_mode)})
        # print 'vblank_mode: %s' % os.environ.get('vblank_mode','undefined')

        print "Initialising stimulus window..."
        # we need to pause here, or for some reason the thread stalls
        # when creating the stimulus frame (but only on the
        # workstation?!)
        time.sleep(0.1)
        self.stimframe = wx.Frame(None, -1,
                                  size=(self.x_resolution, self.y_resolution),
                                  title='Stimulus window')
        self.stimframe.Bind(wx.EVT_CLOSE, self.onClose)

        self.stimframe.timer = rt.ThreadTimer(self.stimframe)
        self.stimcanvas = glc.StimCanvas(self.stimframe, self)
        self.stimframe.Bind(rt.EVT_THREAD_TIMER, self.stimcanvas.onDraw)

        self.stimframe.Show()

        print "Loading tasks..."
        self.loadTasks()

        print "Initialising controls ..."
        self.controlwindow = gui.ControlWindow(None, self,
                                               title='TadPyDoodle')
        self.controlwindow.Bind(wx.EVT_CLOSE, self.onClose)
        self.controlwindow.Show()
        self.controlwindow.SetFocus()

        print "Done"
        app.MainLoop()

    def resetConfig(self, event=None):
        """
        Resets the configuration to the hard-coded defaults specified in
        'self.template'
        """
        config = self.template
        for subsect in config.itervalues():
            for option, value in subsect.iteritems():
                self.__setattr__(option, value)

    def loadConfig(self, event=None):
        """
        Load configuration from a 'tadpydoodlerc' file specified in
        '<self.configroot>/<self.configfile>'
        """

        # create a configparser instance
        parser = SafeConfigParser()

        root = self.configroot.replace('~', os.getenv('HOME'))
        path = os.path.join(root, self.configfile)
        try:
            # try and read read the config file
            parser.readfp(open(path, 'r'))
        except IOError:
            # the file probably doesn't exist, never mind
            pass

        # we will use any values that the parser got to update a copy of
        # our dictionary of default values. this way, any values that
        # are missing from the rc file are filled in by the hard-coded
        # template
        config = copy.copy(self.template)
        for sect, subsect in self.template.iteritems():
            if parser.has_section(sect):
                for option, value in subsect.iteritems():
                    if parser.has_option(sect, option):
        # use the type of the default value in order to determine how to
        # convert the string that the parser returns
                        opt_type = type(value)
                        newstr = parser.get(sect, option)
                        if opt_type == bool:
                            newval = newstr == str(True)
                        else:
                            newval = opt_type(newstr)
                        config[sect][option] = newval

        # since the names of the options in the dictionary are the same
        # as the names of the attributes we need to set, we can just
        # loop through and use self.__setattr__
        for subsect in config.itervalues():
            for option, value in subsect.iteritems():
                self.__setattr__(option, value)

        # force a re-draw of the canvas if it already exists - the
        # display config may have changed
        if hasattr(self, 'stimcanvas'):
            self.stimcanvas.recalc_stim_bounds()
            self.stimcanvas.recalc_photo_bounds()
            self.stimcanvas.do_refresh_everything = True

    def saveConfig(self, event=None):
        """
        Save the current configuration to a 'tadpydoodlerc' file
        specified in '<self.configroot>/<self.configfile>'
        """
        parser = SafeConfigParser()
        template = self.template

        # update the parser according to the current configuration - use
        # the template to grab the section and option names
        for sect, subsect in template.iteritems():
            parser.add_section(sect)
            for option in subsect.iterkeys():
                newval = self.__getattribute__(option)
                parser.set(sect, option, str(newval))

        # write the new configuration out
        root = self.configroot.replace('~', os.getenv('HOME'))
        if not os.path.exists(root):
            os.makedirs(root)
        path = os.path.join(root, self.configfile)
        parser.write(open(path, 'w'))

    def loadTasks(self, event=None):
        """
        Recursively compile and  load all tasks in 'self.taskdir' and
        its subdirectories. Tasks may be defined in any source file, but
        each must have the '.taskname' attribute in order to be
        recognised. Duplicate tasknames are skipped with a warning.
        """

        base_taskdir, user_taskdir = (
            pth.replace('~', os.getenv('HOME'))
            for pth in (self.base_taskdir, self.user_taskdir)
        )

        for pth in (base_taskdir, user_taskdir):
            if not os.path.exists(pth):
                os.makedirs(pth)

        def istask(obj):
            return hasattr(obj, 'taskname')

        names = []
        objects = []
        for pth in (base_taskdir, user_taskdir):
            for relpath, _, fullnames in os.walk(pth):
                for fullname in fullnames:
                    fname, ext = os.path.splitext(fullname)
                    if ext.lower() == '.py':
                        # print os.path.join(relpath,fullname)
                        mod = imp.load_source(fname,
                                              os.path.join(relpath, fullname))
                    # we don't want to do this if we've made changes to the
                    # source files
                    # elif ext.lower() == '.pyc':
                    #   mod = imp.load_compiled(fname,
                    #                           os.path.join(relpath,fullname))

                    else:
                        continue

                    for name, obj in inspect.getmembers(mod,
                                                        predicate=istask):

                        if obj.taskname in names:
                            print 'Ignoring duplicate of task "%s" in %s' \
                                % (obj.taskname, fullname)
                        else:
                            names.append(obj.taskname)
                            objects.append(obj)
                    del mod

        self.current_task = None
        self.taskdict = dict(zip(names, objects))

    def onClose(self, event):
        if self.stimframe:
            self.stimcanvas.timer.stop()
            self.stimframe.Destroy()
        if self.controlwindow:
            self.controlwindow.Destroy()

if __name__ == '__main__':
    t = AppThread()
    t.run()
