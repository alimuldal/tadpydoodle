Tadpydoodle
===============================================================================

About
----------------
Tadpydoodle is a simple GUI-based package for visual stimulus presentation,
designed for neurophysiological experiments. It is written in Python for ease
of scripting and extension, and uses an OpenGL graphical backend for speed.
Currently only Linux is supported.

Dependencies
----------------
Required:

* PyOpenGL >= 3.1.0
* numpy >= 1.7.1
* wxPython >= 2.8.12

Optional:

* PyOpenGL-accelerate <= 3.1.0 (recommended)
* matplotlib >= 1.2.1 (required for diagnostic plots)

Installation
----------------
Simply unpack the source files into a local directory, or using git:

    $ git clone git@github.com:alimuldal/tadpydoodle.git tadpydoodle

Useage
----------------
Tadpydoodle can be started from the command line like this:

    <tadpydoodle/directory>$ python tadpydoodle.py

Configuration settings will be saved in `~/.tadpydoodle/tadpydoodlerc`.

Stimulus design
----------------
Stimuli are Python classes which can be defined in any Python source file
within the `tasks/` directory. They must have both `.taskname` and `.subclass`
attributes, and must implement a `._drawstim()` method. See the contents of the
`tasks/` directory for examples.

Authors
----------------
Tadpydoodle was written by Alistair Muldal (alimuldal@gmail.com) and Timothy
Lillicrap (timothy.lillicrap@gmail.com) at the Department of Pharmacology,
University of Oxford

License
----------------
Tadpydoodle is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
