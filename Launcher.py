# Launcher.py
import sys, os, random
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QRect, QEvent, QPoint
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QFontDatabase, QFont

from StickyNotes import StickyNote
from TodoList import TodoList

if sys.platform.startswith("win") and getattr(sys, "frozen", False):
    try:
        import winreg
        exe = sys.executable.replace("/", "\\")
        # 1) .sn → StickyNotes.note
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.sn")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "StickyNotes.note")
        key.Close()
        # 2) 文件类型描述
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\StickyNotes.note")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Sticky Note File")
        key.Close()
        # 3) 默认图标
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\StickyNotes.note\DefaultIcon")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, exe)
        key.Close()
        # 4) 打开命令
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\StickyNotes.note\shell\open\command")
        winreg.SetValueEx(
            key, "", 0, winreg.REG_SZ,
            f"\"{exe}\" \"%1\""
        )
        key.Close()
    except Exception:
        # 安全忽略任何注册失败
        pass

COLOR_SCHEMES = [
    ("#fffde7", "#fbc02d"),
    ("#e8f5e9", "#66bb6a"),
    ("#fce4ec", "#ec407a"),
    ("#e3f2fd", "#42a5f5"),
    ("#fff3e0", "#ffa726"),
    ("#eeeeee", "#757575"),
    ("#f3e5f5", "#ab47bc"),
]
CAPSULE_RADIUS = 30
CLICK_THRESHOLD = 5
open_windows = []

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(160, 60)

        self.left_color, _ = random.choice(COLOR_SCHEMES)
        self._dragging = False
        self._press = QPoint(); self._start = QPoint()
        self.open_windows = []  # 引用窗口

        self.left_lbl = QLabel("便签", self)
        self.right_lbl = QLabel("待办", self)
        for lbl in (self.left_lbl, self.right_lbl):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#333333;")
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.left_lbl)
        lay.addWidget(self.right_lbl)

        self.installEventFilter(self)

    def paintEvent(self, ev):
        w,h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0,0,w,h,CAPSULE_RADIUS,CAPSULE_RADIUS)
        p.fillPath(path, QColor("#f5f5f5"))
        left = QRect(0,0,w//2,h)
        cp = QPainterPath()
        r = CAPSULE_RADIUS
        cp.moveTo(left.right(),0)
        cp.lineTo(left.x()+r,0)
        cp.quadTo(left.x(),0,left.x(),r)
        cp.lineTo(left.x(),left.bottom()-r)
        cp.quadTo(left.x(),left.bottom(),left.x()+r,left.bottom())
        cp.lineTo(left.right(),left.bottom())
        cp.closeSubpath()
        p.fillPath(cp, QColor(self.left_color))

    def mousePressEvent(self, ev):
        if ev.button()==Qt.LeftButton:
            self._start_pos = ev.globalPos()
            self._press_pos = ev.globalPos()
            self._dragging = False

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton:
            delta = ev.globalPos() - self._press_pos
            if delta.manhattanLength() > CLICK_THRESHOLD:
                self._dragging = True
                self.move(self.x()+delta.x(), self.y()+delta.y())
                self._press_pos = ev.globalPos()

    def mouseReleaseEvent(self, ev):
        if ev.button()!=Qt.LeftButton:
            return
        # 拖拽不触发点击
        if not self._dragging:
            dist = (ev.globalPos() - self._start_pos).manhattanLength()
            if dist < CLICK_THRESHOLD:
                if ev.pos().x() < self.width()//2:
                    note = StickyNote()
                    note.show()
                    self.open_windows.append(note)
                else:
                    todo = TodoList()
                    todo.show()
                    self.open_windows.append(todo)
        self._dragging = False

    def eventFilter(self, o, ev):
        if ev.type()==QEvent.Enter:
            self.setCursor(Qt.PointingHandCursor)
        elif ev.type()==QEvent.Leave:
            self.setCursor(Qt.ArrowCursor)
        return super().eventFilter(o, ev)

if __name__=="__main__":
    app = QApplication(sys.argv)
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    simhei_path = os.path.join(base, "fonts", "SimHei.ttf")
    zh_id = QFontDatabase.addApplicationFont(simhei_path)
    zh_fams = QFontDatabase.applicationFontFamilies(zh_id) if zh_id!=-1 else []
    zh_fam = zh_fams[0] if zh_fams else "SimHei"

    en_fam = "SVGASYS"
    f = QFont(en_fam, 12)
    f.setStyleStrategy(QFont.PreferDefault)
    app.setFont(f)
    app.setStyleSheet(f"""
        * {{
            font-family: "{en_fam}", "{zh_fam}";
            font-size: 12pt;
        }}
    """)

    args = sys.argv[1:]
    if args and args[0].lower().endswith(".sn"):
        path = os.path.abspath(args[0].strip('"'))
        win = StickyNote(path)
        win.show(); win.raise_(); win.activateWindow()
        open_windows.append(win)
    else:
        launcher = Launcher()
        launcher.show()
        open_windows.append(launcher)

    sys.exit(app.exec_())