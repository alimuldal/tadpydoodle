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
import threading
# import multiprocessing
import time

wxEVT_THREAD_TIMER = wx.NewEventType()
EVT_THREAD_TIMER = wx.PyEventBinder(wxEVT_THREAD_TIMER, 1)

#######################################################################

class ThreadTimer(object):
	def __init__(self, parent):
		self.parent = parent
		self.reinit()

	def reinit(self):
		self.thread = Thread()
		self.thread.parent = self
		self.alive = False

	def start(self, interval):
		self.interval = interval
		self.alive = True
		self.pending = False
		self.thread.start()

	def stop(self):
		self.alive = False

class Thread(threading.Thread):
	def run(self):
		while self.parent.alive:
			time.sleep(self.parent.interval/1000.0)
			if not self.parent.pending:
				self.parent.pending = True
				self._post()

	def _post(self):
		event = wx.PyEvent(eventType=wxEVT_THREAD_TIMER)
		wx.PostEvent(self.parent.parent, event)

