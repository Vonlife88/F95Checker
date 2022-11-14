import imgui

from modules.structs import Os
from modules import globals, utils

title = "F95Checker: Login to F95Zone"
size = (500, 720)
stay_on_top = True
start_page = globals.login_page


def did_login(cookies):
    return "xf_user" in cookies


def run_qt():
    from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineCore, QtWebEngineWidgets
    import glfw

    window = QtWidgets.QWidget()
    window.setWindowTitle(title)
    window.setWindowIcon(QtGui.QIcon(str(globals.gui.icon_path)))
    window.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
    window.resize(*size)
    window.move(
        int(globals.gui.screen_pos[0] + (imgui.io.display_size.x / 2) - size[0] / 2),
        int(globals.gui.screen_pos[1] + (imgui.io.display_size.y / 2) - size[1] / 2)
    )
    window.setLayout(QtWidgets.QGridLayout())
    window.layout().setContentsMargins(0, 0, 0, 0)
    window.layout().setSpacing(0)
    window.setStyleSheet(f"""
        QProgressBar {{
            background: {utils.rgba_0_1_to_hex(globals.settings.style_bg)[:-2]};
            border-radius: 0px;
        }}
        QProgressBar::chunk {{
            background: {utils.rgba_0_1_to_hex(globals.settings.style_accent)[:-2]};
            border-radius: 0px;
        }}
        QLabel {{
            color: {utils.rgba_0_1_to_hex(globals.settings.style_text)[:-2]};
            font-size: 8pt;
        }}
    """)

    progress = QtWidgets.QProgressBar(window)
    progress.setTextVisible(False)
    progress.setFixedHeight(10)
    progress.setMaximum(100)
    label = QtWidgets.QLabel(text="Click to reload")

    profile = QtWebEngineCore.QWebEngineProfile(window)
    webview = QtWebEngineWidgets.QWebEngineView(profile, window)
    cookies = {}
    def on_cookie_add(cookie):
        name = cookie.name().data().decode('utf-8')
        value = cookie.value().data().decode('utf-8')
        cookies[name] = value
        if did_login(cookies):
            try:
                window.close()
            except RuntimeError:
                pass
    profile.cookieStore().cookieAdded.connect(on_cookie_add)
    webview.setUrl(QtCore.QUrl(start_page))

    loading = [False]
    def load_started(*_):
        loading[0] = True
        progress.setValue(1)
        progress.repaint()
    def load_progress(value):
        progress.setValue(max(1, value))
        progress.repaint()
    def load_finished(*_):
        loading[0] = False
        progress.setValue(0)
        progress.repaint()
    webview.loadStarted.connect(load_started)
    webview.loadProgress.connect(load_progress)
    webview.loadFinished.connect(load_finished)
    def reload(*_):
        if loading[0]:
            webview.stop()
            load_finished()
        else:
            webview.reload()
            load_started()
    progress.mousePressEvent = reload
    label.mousePressEvent = reload

    window.layout().addWidget(label, 0, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
    window.layout().addWidget(progress, 0, 0)
    window.layout().addWidget(webview, 1, 0)
    alive = [True]
    _closeEvent = window.closeEvent
    def closeEvent(*args, **kwargs):
        alive[0] = False
        return _closeEvent(*args, **kwargs)
    window.closeEvent = closeEvent
    window.show()
    while alive[0]:
        globals.gui.qt_app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.WaitForMoreEvents)
    glfw.make_context_current(globals.gui.window)
    return cookies

def run_gtk():
    import ctypes.util
    import gi

    def get_gtk_version(name):
        lib = ctypes.util.find_library(name)
        if not lib:
            raise ModuleNotFoundError(f"A required library file could not be found for {repr(name)}")
        ver = lib.rsplit("-", 1)[1].rsplit(".so", 1)[0].rsplit(".dylib", 1)[0].rsplit(".dll", 1)[0]
        if ver.count(".") < 1:
            ver += ".0"
        return ver

    gi.require_version("Gtk", get_gtk_version("gtk-3"))
    gi.require_version("WebKit2", get_gtk_version("webkit2gtk-4"))
    from gi.repository import Gtk, WebKit2

    window = Gtk.Window(title=title)
    window.set_icon_from_file(str(globals.gui.icon_path))
    window.set_keep_above(stay_on_top)
    window.resize(*size)
    window.move(
        globals.gui.screen_pos[0] + (imgui.io.display_size.x / 2) - size[0] / 2,
        globals.gui.screen_pos[1] + (imgui.io.display_size.y / 2) - size[1] / 2
    )

    # TODO: add progressbar

    context = WebKit2.WebContext.new_ephemeral()
    webview = WebKit2.WebView(web_context=context)
    cookies = {}
    def on_cookies_changed(cookie_manager):
        def cookies_callback(cookie_manager, cookie_task):
            cookies.update({cookie.get_name(): cookie.get_value() for cookie in cookie_manager.get_cookies_finish(cookie_task)})
            if did_login(cookies):
                window.destroy()
        cookie_manager.get_cookies(webview.get_uri(), None, cookies_callback)
    context.get_cookie_manager().connect("changed", on_cookies_changed)
    webview.load_uri(start_page)

    window.connect("destroy", Gtk.main_quit)
    window.add(webview)
    window.show_all()
    Gtk.main()
    return cookies


def run():
    if globals.os is Os.Windows:
        run = run_qt
    else:
        run = run_gtk
    return run()
