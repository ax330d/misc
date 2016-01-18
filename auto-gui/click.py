#!c:\\python27\python.exe
# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=C0103

"""Tool to close popups."""

import ConfigParser
import win32gui
import win32api
import win32con
import win32process
import ctypes

__version__ = "0.0.2"
__author__ = "Arthur Gerkis"


# http://www.brunningonline.net/simon/blog/archives/000664.html
TH32CS_SNAPPROCESS = 0x00000002


class PROCESSENTRY32(ctypes.Structure):
    """PROCESSENTRY32 structure."""
    _fields_ = [("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.c_ulong),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260)]


class GUIController(object):
    """GUIController class"""
    def __init__(self):
        self._text_to_act_hash = {}
        self._allowed_proc = ['firefox.exe', 'iexplore.exe', 'chrome.exe']
        self._allowed_actions = ['cancel', 'ok', 'close']
        self._pids = []
        self._read_config()

    def _read_config(self):
        """Read configuration file."""
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read('window.ini')
        sections = config.sections()
        for item in sections:
            ary = config.items(item)
            for i in ary:
                self._text_to_act_hash[i[0]] = (item, i[1])
        return

    def rand_clicks(self):
        """Trigger random clicks."""
        self._enumerate('clicks')
        return

    def close_popups(self):
        """Close popups."""
        self._enumerate('popups')
        return

    def resize(self):
        """Resize window."""
        self._enumerate('resize')
        return

    def _enumerate(self, a_type):
        """Enumerate all handles."""

        self._enum_proc()
        win32gui.EnumChildWindows(None, self._enum_callback, a_type)
        self._pids = []
        return

    def _enum_callback(self, hwnd, param=None):
        """Enumerate callbacks."""
        win_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        if not self._pid_belongs(pid) or win_text == '':
            return

        if param == 'resize':
            (_, _, w, h) = self._get_coords(hwnd)
            self._resize(hwnd, 800, 400)
            print "Resize"
            return

        if param == 'clicks':
            _, _, w, h = self._get_coords(hwnd)
            self._click_pos(hwnd, (w + 30, h + 30))
            print "Clicks"
            return

        found = False
        for key in self._text_to_act_hash.keys():
            (cls, action) = self._text_to_act_hash[key]
            action = action.strip("'")
            if class_name != cls:
                continue
            if win_text.find(key) != 0:
                continue
            found = True

        if not found:
            return
        if action not in self._allowed_actions:
            return

        if action == 'close':
            print 'CLOSE'
            self._close(hwnd)

        elif action == 'ok':
            print 'OK'
            self._click_ok(hwnd)

        elif action == 'cancel':
            print 'CANCEL'
            self._click_cancel(hwnd)
        return

    @classmethod
    def _close(cls, hwnd):
        """Send close message."""

        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return

    def _click_cancel(self, hwnd):
        """Click Cancel button."""
        button = win32gui.FindWindowEx(hwnd, 0, "Button", "Cancel")
        if button:
            print 'Button Cancel =', button
            self._click(button)
        return

    def _click_ok(self, hwnd):
        """Click Ok button."""
        button = win32gui.FindWindowEx(hwnd, 0, "Button", "OK")
        if button:
            print 'Button OK =', button
            self._click(button)

        button = win32gui.FindWindowEx(hwnd, 0, "Button", "&Yes")
        if button:
            print 'Button Yes =', button
            self._click(button)
        return

    @classmethod
    def _click_pos(cls, hwnd, pos=None):
        """Send click message."""
        tmp = 0
        if pos:
            client_pos = win32gui.ScreenToClient(hwnd, pos)
            tmp = win32api.MAKELONG(client_pos[0], client_pos[1])
        win32gui.SendMessage(hwnd,
                             win32con.WM_ACTIVATE,
                             win32con.WA_ACTIVE, 0)
        win32gui.SendMessage(hwnd,
                             win32con.WM_LBUTTONDOWN,
                             win32con.MK_LBUTTON, tmp)
        win32gui.SendMessage(hwnd,
                             win32con.WM_LBUTTONUP,
                             win32con.MK_LBUTTON, tmp)
        return

    @classmethod
    def _resize(cls, hwnd, new_x, new_y, new_w=800, new_h=400):
        """Resize window."""
        hwout = None
        win32gui.SetWindowPos(hwnd, hwout, new_x, new_y, new_w, new_h, 0x0040)
        return

    def _pid_belongs(self, pid):
        """Detect if PID belongs to PIDs."""
        if pid in self._pids:
            return True
        return False

    def _enum_proc(self):
        """Enumerate processes."""
        # See http://msdn2.microsoft.com/en-us/library/ms686701.aspx
        hProcessSnap = ctypes.windll.kernel32.\
            CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe32 = PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if ctypes.windll.kernel32.Process32First(hProcessSnap,
                                                 ctypes.byref(pe32)) == \
           win32con.FALSE:
            print "Failed getting first process."
            return
        while True:
            if pe32.szExeFile in self._allowed_proc:
                self._pids.append(pe32.th32ProcessID)
            if ctypes.windll.kernel32.Process32Next(hProcessSnap,
                                                    ctypes.byref(pe32)) == \
               win32con.FALSE:
                break
        ctypes.windll.kernel32.CloseHandle(hProcessSnap)
        return

    @classmethod
    def _click(cls, hwnd):
        """Click."""
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, 0)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, 0)
        return

    @classmethod
    def _get_coords(cls, hwnd):
        """Change width/height of window."""
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y
        return (x, y, w, h)


def main():
    """Main."""
    gctrl = GUIController()
    gctrl.close_popups()

if __name__ == '__main__':
    main()
