import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication

from StickyNotes import StickyNote
from TodoList import TodoList

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 兼容打包后的路径
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "sticky_note_icon.ico")
    icon = QIcon(icon_path)

    # 托盘检测
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "错误", "系统不支持托盘图标。")
        sys.exit(1)

    tray = QSystemTrayIcon(icon)
    tray.setToolTip("便签工具")
    tray.setVisible(True)

    notes = []

    def create_note():
        note = StickyNote()
        note.setWindowIcon(icon)
        note.show()
        notes.append(note)

    def create_todo():
        todo = TodoList()
        todo.setWindowIcon(icon)
        todo.show()
        notes.append(todo)

    menu = QMenu()
    menu.addAction("新建便签", create_note)
    menu.addAction("新建待办清单", create_todo)
    menu.addSeparator()
    menu.addAction("退出", QCoreApplication.quit)

    tray.setContextMenu(menu)
    app.setWindowIcon(icon)

    # 初始创建一个便签
    create_note()

    sys.exit(app.exec_())