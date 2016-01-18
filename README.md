
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

### win32-server

Simple python tool to observe all opened windows properties.

![Python Window Server](images/pw.png)

### auto-gui

Python tool to automatically click on popups. Can be used with fuzzing
tools.

List of files:
 * click.py - tool itself
 * sched.bat - bat file that automates click.py launch ever 120 seconds
 * window.ini - configuration file (you can add own windows)

Requires pywin32.
