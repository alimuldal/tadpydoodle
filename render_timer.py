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

