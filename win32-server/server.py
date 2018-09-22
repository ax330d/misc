#!c:\\python27\python.exe
# -*- coding: utf-8 -*-
# pylint: disable=E1101

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading
import cgi
# FIXME: remove win32 dep
import win32gui
import win32con
import win32process
import ctypes


__version__ = "0.0.2"
__author__ = "Arthur Gerkis"


# http://www.brunningonline.net/simon/blog/archives/000664.html
TH32CS_SNAPPROCESS = 0x00000002


class PROCESSENTRY32(ctypes.Structure):
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


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """Class to handle HTTP requests."""
    def __init__(self, *args):
        BaseHTTPRequestHandler.__init__(self, *args)

    @classmethod
    def _get_coords(cls, hwnd):
        """Get dimensions of window."""

        rect = win32gui.GetWindowRect(hwnd)
        xdim = rect[0]
        ydim = rect[1]
        wdim = rect[2] - xdim
        hdim = rect[3] - ydim
        return (xdim, ydim, wdim, hdim)

    def _enum_callback(self, handle, param):
        """Processes enumeration callack."""

        win_text = cgi.escape(win32gui.GetWindowText(handle))
        class_name = cgi.escape(win32gui.GetClassName(handle))
        _, pid = win32process.GetWindowThreadProcessId(handle)
        (xdim, ydim, wdim, hdim) = self._get_coords(handle)
        if pid not in param:
            param[pid] = []
        param[pid].append((handle, class_name, win_text, xdim,
                           ydim, wdim, hdim))

        classes = ["Button", "ComboBox", "Edit", "ListBox", "MDIClient",
                   "ScrollBar", "Static", "ComboLBox", "DDEMLEvent", "Message",
                   "#32768", "#32769", "#32770", "#32771", "#32772"]
        for _class in classes:
            button = win32gui.FindWindowEx(handle, 0, _class, None)
            if not button:
                continue
            text = win32gui.GetWindowText(button)
            print "class = {}, button = {:x}, PID = {}, text = {}".\
                format(_class, button, pid, text)
        return

    def _call_win32(self):
        """Enumerate processes."""

        pid_group = {}
        proc_names = {}
        data = ""
        counter = 0

        self._enum_proc(proc_names)
        win32gui.EnumChildWindows(None, self._enum_callback, pid_group)

        line = ("<tr>"
                "   <td>{nr}</td>"
                "   <td>{handle:x}</td>"
                "   <td>{class_name}</td>"
                "   <td>{win_text}</td>"
                "   <td>{dimension}</td>"
                "</tr>\n")

        for _pid in sorted(pid_group):
            name = "?"
            if _pid in proc_names:
                name = proc_names[_pid]
            data += ("<tr class=\"separator\">"
                     "    <td colspan=\"2\">PID: {pid}</td>"
                     "    <td colspan=\"3\">Name: {name}</td>"
                     "</tr>\n").format(pid=_pid, name=name)
            for _epid in pid_group[_pid]:
                handle, class_name, win_text, xdim, ydim, wdim, hdim = _epid
                dimension = "x = {}, y = {}, {} x {}".\
                    format(xdim, ydim, wdim, hdim)
                data += line.format(nr=counter, handle=handle,
                                    class_name=class_name,
                                    win_text=win_text,
                                    dimension=dimension)
                counter += 1
        return data

    @classmethod
    def _enum_proc(cls, proc_names):
        """Enumerate processes, get PIDs and names."""

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
            proc_names[pe32.th32ProcessID] = pe32.szExeFile
            if ctypes.windll.kernel32.Process32Next(hProcessSnap,
                                                    ctypes.byref(pe32)) == \
               win32con.FALSE:
                break
        ctypes.windll.kernel32.CloseHandle(hProcessSnap)
        return

    def end_response(self, html):
        """End request response."""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html)

    def do_GET(self):

        template = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Python Window explorer</title>
                <meta charset="UTF-8"></meta>
                <style type="text/css">
                    body {{
                        background-color: lavenderblush;
                        font-size: 0.8em;
                        font-family: arial;
                    }}
                    table {{
                        background-color: #fdfdfd;
                        border-collapse: collapse;
                        border: none;
                        width: 100%;
                    }}
                    .main {{
                        background-color: cornflowerblue;
                        font-weight: bold;
                    }}
                    tr:hover {{
                        background-color: silver;
                    }}
                    .separator {{
                        background-color: lightsteelblue;
                    }}
                    td {{
                        border: 1px solid #ccc;
                        padding: 3px;
                    }}
                </style>
            </head>

            <body onload="init()">
                <h3>Python Window explorer</h3>
                <table>
                    <tr class="main">
                        <td>Nr.</td>
                        <td>Handle</td>
                        <td>Class name</td>
                        <td>Window text</td>
                        <td>Dimensions</td>
                    </tr>
                    {table}
                </table>
            </body>
        </html>
        """

        short_path = ""
        if self.path.find("?") != -1:
            short_path, query_string = self.path.split("?", 1)
            _ = query_string.split("&")
        else:
            short_path = self.path

        if short_path == "/":
            data = self._call_win32()
            html = template.format(table=data)
            self.end_response(html)
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Implements threaded HTTP server."""
    allow_reuse_address = True

    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)


class SimpleHttpServer(object):
    """Simple threaded HTTP server."""
    def __init__(self, ip_addr, port):
        super(SimpleHttpServer, self).__init__()
        self.server_thread = None

        def handler(*args):
            """Wrap handler."""
            HTTPRequestHandler(*args)
        self.server = ThreadedHTTPServer((ip_addr, port), handler)

    def start(self):
        """Start server daemon."""
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def wait_for_thread(self):
        """Wait for thread."""
        self.server_thread.join()

    def stop(self):
        """Stop server."""
        self.server.shutdown()
        self.wait_for_thread()


def main():
    """Entry point."""
    server = SimpleHttpServer("", 9090)
    print "HTTP Server Running..."
    server.start()
    server.wait_for_thread()


if __name__ == "__main__":
    main()
