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

class DummyTask(object):
	subclass = 'gamma_test'
	area_aspect=1
	currentframe = 1
	dt = 1
	totalframes = 1
	finishtime = 1.
	scan_hz = 1

	def __init__(self,canvas=None):
		self.background_color = ((self._i,)*3 + (1.,))

	def _drawstim():
		pass

	def __reinit():
		pass

class luminance_0(DummyTask):
	taskname = 'luminance_0'
	_i = 0.

class luminance_0_025(DummyTask):
	taskname = 'luminance_0.025'
	_i = 0.025

class luminance_0_05(DummyTask):
	taskname = 'luminance_0.05'
	_i = 0.05

class luminance_0_075(DummyTask):
	taskname = 'luminance_0.075'
	_i = 0.075

class luminance_0_1(DummyTask):
	taskname = 'luminance_0.1'
	_i = 0.1

class luminance_0_2(DummyTask):
	taskname = 'luminance_0.2'
	_i = 0.2

class luminance_0_3(DummyTask):
	taskname = 'luminance_0.3'
	_i = 0.3

class luminance_0_4(DummyTask):
	taskname = 'luminance_0.4'
	_i = 0.4

class luminance_0_5(DummyTask):
	taskname = 'luminance_0.5'
	_i = 0.5

class luminance_0_6(DummyTask):
	taskname = 'luminance_0.6'
	_i = 0.6

class luminance_0_7(DummyTask):
	taskname = 'luminance_0.7'
	_i = 0.7

class luminance_0_8(DummyTask):
	taskname = 'luminance_0.8'
	_i = 0.8

class luminance_0_9(DummyTask):
	taskname = 'luminance_0.9'
	_i = 0.9

class luminance_1_0(DummyTask):
	taskname = 'luminance_1.0'
	_i = 1.