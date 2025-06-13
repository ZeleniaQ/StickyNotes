# StickyNotes.py
import sys, os, random, json
from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QEvent, QRect
from PyQt5.QtGui import QColor, QFont

COLOR_SCHEMES = [
    ("#fffde7", "#fbc02d"),
    ("#e8f5e9", "#66bb6a"),
    ("#fce4ec", "#ec407a"),
    ("#e3f2fd", "#42a5f5"),
    ("#fff3e0", "#ffa726"),
    ("#eeeeee", "#757575"),
    ("#f3e5f5", "#ab47bc"),
]
EDGE_MARGIN = 6

class StickyNote(QWidget):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300,200)

        self.old_pos = None
        self.resizing_edge = None
        self.bg_color, self.btn_color = random.choice(COLOR_SCHEMES)

        # 容器 & 布局
        self.container = QWidget(self)
        self.container.setStyleSheet(f"background-color:{self.bg_color};border-radius:16px;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(self.container)

        # 标题栏
        self.title_bar = QWidget(self.container)
        self.title_bar.setFixedHeight(30)
        self.title_bar.installEventFilter(self)
        self.title_bar.setStyleSheet("background:transparent;")
        self.title_edit = QLineEdit("自定义便签", self.title_bar)
        self.title_edit.setFixedWidth(120)
        self.title_edit.setStyleSheet("""
            QLineEdit {
              border:none;background:transparent;font-weight:bold;
              font-size:14px;padding-left:6px;
              font-family:YouYuan,"Microsoft YaHei UI",sans-serif;
            }
        """)

        def btn(sym):
            b = QPushButton(sym)
            b.setFixedSize(24,24)
            b.setStyleSheet(f"""
                QPushButton {{
                   background-color:{self._adj(self.btn_color,0.9)};
                   color:white;font-size:14px;font-weight:bold;
                   border:none;border-radius:12px;
                }}
                QPushButton:hover {{
                  background-color:{self._adj(self.btn_color,1.2)};
                }}
            """)
            return b

        self.min_btn = btn("—");   self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn = btn("✕"); self.close_btn.clicked.connect(self.close)

        tlay = QHBoxLayout(self.title_bar)
        tlay.setContentsMargins(8,4,8,0)
        tlay.addWidget(self.title_edit)
        tlay.addStretch()
        tlay.addWidget(self.min_btn)
        tlay.addWidget(self.close_btn)

        # 编辑区
        self.text_edit = QTextEdit(self.container)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
              background-color:{self.bg_color};
              border:none;padding:6px;
              font-size:14px;
              font-family:YouYuan,"Microsoft YaHei UI",sans-serif;
            }}
        """)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sb = self.text_edit.verticalScrollBar()
        sb.setStyleSheet(f"""
            QScrollBar:vertical {{
              border:none;background:transparent;
              width:6px;margin:4px 2px 4px 0;border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
              background:{self._adj(self.btn_color,0.9)};
              min-height:24px;border-radius:3px;
            }}
            QScrollBar::handle:vertical:hover {{
              background:{self._adj(self.btn_color,1.2)};
            }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{{background:none;}}
        """)

        bl = QVBoxLayout(self.container)
        bl.setContentsMargins(0,0,0,0)
        bl.addWidget(self.title_bar)
        bl.addWidget(self.text_edit)

        # 如果指定了文件，先加载
        if self.file_path:
            self._load(self.file_path)

        self.show()

    def _adj(self, c, f):
        col = QColor(c)
        return QColor(
            min(int(col.red()*f),255),
            min(int(col.green()*f),255),
            min(int(col.blue()*f),255)
        ).name()

    def closeEvent(self, ev):
        r = QMessageBox.question(
            self,"保存便签","是否保存更改？",
            QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel
        )
        if r==QMessageBox.Cancel:
            ev.ignore(); return
        if r==QMessageBox.Yes:
            if not self.file_path:
                p,_ = QFileDialog.getSaveFileName(
                    self,"保存便签","","Sticky Note (*.sn)"
                )
                if not p:
                    ev.ignore(); return
                self.file_path = p
            self._save(self.file_path)
        ev.accept()

    def _save(self, path):
        data = {
            "title":   self.title_edit.text(),
            "content": self.text_edit.toPlainText(),
            "geometry": [self.x(), self.y(), self.width(), self.height()]
        }
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)

    def _load(self, path):
        try:
            with open(path,"r",encoding="utf-8") as f:
                d = json.load(f)
            self.title_edit.setText(d.get("title",""))
            self.text_edit.setPlainText(d.get("content",""))
            geo = d.get("geometry",None)
            if geo and len(geo)==4:
                gx,gy,gw,gh = geo
                # 保证在可视区域或居中
                screen = QApplication.primaryScreen().availableGeometry()
                rect = QRect(gx,gy,gw,gh)
                if not screen.contains(rect):
                    gx = screen.x() + (screen.width()-gw)//2
                    gy = screen.y() + (screen.height()-gh)//2
                self.setGeometry(gx,gy,gw,gh)
        except Exception as e:
            QMessageBox.warning(self,"加载失败",f"无法加载便签：\n{e}")

    # 拖动 & 缩放略——和之前完全一致
    def eventFilter(self, src, ev):
        if src is self.title_bar:
            if ev.type()==QEvent.MouseButtonPress and ev.button()==Qt.LeftButton:
                self.old_pos = ev.globalPos(); return True
            if ev.type()==QEvent.MouseMove and self.old_pos:
                d = ev.globalPos()-self.old_pos
                self.move(self.x()+d.x(),self.y()+d.y())
                self.old_pos = ev.globalPos(); return True
            if ev.type()==QEvent.MouseButtonRelease:
                self.old_pos = None; return True
        return super().eventFilter(src, ev)
    def mousePressEvent(self, ev):
        if ev.button()==Qt.LeftButton:
            self.old_pos = ev.globalPos()
            self.resizing_edge = self._get_edge(ev.pos())
    def mouseMoveEvent(self, ev):
        if self.resizing_edge and self.old_pos:
            d = ev.globalPos()-self.old_pos; g=self.geometry()
            if "left"   in self.resizing_edge: g.setLeft(g.left()+d.x())
            if "right"  in self.resizing_edge: g.setRight(g.right()+d.x())
            if "top"    in self.resizing_edge: g.setTop(g.top()+d.y())
            if "bottom" in self.resizing_edge: g.setBottom(g.bottom()+d.y())
            self.setGeometry(g); self.old_pos = ev.globalPos()
        else:
            ed = self._get_edge(ev.pos())
            cmap = {
                "top_left":Qt.SizeFDiagCursor,"top_right":Qt.SizeBDiagCursor,
                "bottom_left":Qt.SizeBDiagCursor,"bottom_right":Qt.SizeFDiagCursor,
                "left":Qt.SizeHorCursor,"right":Qt.SizeHorCursor,
                "top":Qt.SizeVerCursor,"bottom":Qt.SizeVerCursor,None:Qt.ArrowCursor
            }
            self.setCursor(cmap.get(ed,Qt.ArrowCursor))
    def mouseReleaseEvent(self, ev):
        self.old_pos=None;self.resizing_edge=None
        self.setCursor(Qt.ArrowCursor)
    def _get_edge(self, pos):
        r=self.rect(); x,y=pos.x(),pos.y()
        return (
            "top_left"    if x<EDGE_MARGIN and y<EDGE_MARGIN else
            "top_right"   if x>r.width()-EDGE_MARGIN and y<EDGE_MARGIN else
            "bottom_left" if x<EDGE_MARGIN and y>r.height()-EDGE_MARGIN else
            "bottom_right"if x>r.width()-EDGE_MARGIN and y>r.height()-EDGE_MARGIN else
            "left"   if x<EDGE_MARGIN else
            "right"  if x>r.width()-EDGE_MARGIN else
            "top"    if y<EDGE_MARGIN else
            "bottom" if y>r.height()-EDGE_MARGIN else
            None
        )

# 方便调试
if __name__=="__main__":
    app = QApplication(sys.argv)
    w = StickyNote()
    sys.exit(app.exec_())
