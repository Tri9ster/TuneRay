import os
import sys

if sys.platform == "darwin" and getattr(sys, "frozen", False):
    # QtCore.abi3.so の静的イニシャライザ (qdarwinpermissionplugin_location) が
    # CFBundleCopyBundleURL() を NULL バンドルで呼び出しクラッシュする問題への対処。
    # QT_PLUGIN_PATH を明示的に設定することで Qt のバンドル経由のパス解決をスキップする。
    _macos = os.path.dirname(sys.executable)           # Contents/MacOS
    _frameworks = os.path.normpath(os.path.join(_macos, "..", "Frameworks"))
    _plugins = os.path.join(_frameworks, "PyQt6", "Qt6", "plugins")
    os.environ.setdefault("QT_PLUGIN_PATH", _plugins)
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", os.path.join(_plugins, "platforms"))
