import random
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QCheckBox,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QPainterPath, QRegion

COLOR_SCHEMES = [
    ("#fffde7","#fbc02d"),("#e8f5e9","#66bb6a"),
    ("#fce4ec","#ec407a"),("#e3f2fd","#64b5f6"),
    ("#fff3e0","#ffa726"),("#eeeeee","#757575"),
    ("#f3e5f5","#ab47bc"),
]
EDGE_MARGIN = 6

class TodoItem(QWidget):
    def __init__(self, show_placeholder=False):
        super().__init__()
        chk = QCheckBox()
        txt = QLineEdit()
        if show_placeholder:
            txt.setPlaceholderText(" 输入待办事项…")
        txt.setStyleSheet("""
            QLineEdit {
                border: none;
                font-size: 13px;
                font-family: "SVGASYS", "SimHei";
            }
        """)
        chk.stateChanged.connect(lambda s: txt.font().setStrikeOut(s==Qt.Checked) or txt.setFont(txt.font()))

        row = QHBoxLayout()
        row.setContentsMargins(0,0,0,0)
        row.setSpacing(8)
        row.addWidget(chk)
        row.addWidget(txt)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,4,0,4)
        outer.setSpacing(4)
        outer.addLayout(row)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border-top:1px dashed #aaa;")
        sep.setFixedHeight(1)
        outer.addWidget(sep)

class TodoList(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300,400)
        self.setMask(self.round_mask(16))

        self.old_pos=None; self.resizing_edge=None
        self.bg_color, self.btn_color = random.choice(COLOR_SCHEMES)

        # 容器
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            background-color:{self.bg_color};
            border-radius:16px;
        """)
        main = QVBoxLayout(self)
        main.setContentsMargins(0,0,0,0)
        main.addWidget(self.container)

        # 标题栏
        self.title_bar = QWidget(self.container)
        self.title_bar.setFixedHeight(30)
        self.title_bar.installEventFilter(self)
        self.title_bar.setStyleSheet("background:transparent;")

        self.title_edit = QLineEdit("Todo List", self.title_bar)
        self.title_edit.setReadOnly(True)
        self.title_edit.setStyleSheet("""
            QLineEdit {
                border:none;
                background:transparent;
                font-weight:bold;
                font-size:14px;
                padding-left:6px;
                font-family:"SVGASYS","SimHei";
            }
        """)
        self.title_edit.setFixedWidth(120)

        def cute_btn(sym):
            b=QPushButton(sym)
            b.setFixedSize(24,24)
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color:{self.btn_color};
                    border:none;border-radius:12px;
                    font-size:14px;font-weight:bold;
                    font-family:"SVGASYS","SimHei";
                    color:white;
                }}
                QPushButton:hover {{
                    background-color:{self._adjust_color(self.btn_color,1.2)};
                }}
            """)
            return b

        btn_min = cute_btn("—"); btn_min.clicked.connect(self.showMinimized)
        btn_cl  = cute_btn("✕"); btn_cl.clicked.connect(self.close)

        tl = QHBoxLayout(self.title_bar)
        tl.setContentsMargins(8,4,8,0); tl.setSpacing(6)
        tl.addWidget(self.title_edit); tl.addStretch()
        tl.addWidget(btn_min); tl.addWidget(btn_cl)

        # 滚动区
        self.scroll = QScrollArea(self.container)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        bar = self.scroll.verticalScrollBar()
        bar.setStyleSheet(f"""
            QScrollBar:vertical {{
                border:none; background:transparent;
                width:6px; margin:4px 2px 4px 0; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:{self._adjust_color(self.btn_color,0.9)};
                min-height:24px; border-radius:3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background:{self._adjust_color(self.btn_color,1.2)};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{ background:none; }}
        """)

        self.inner = QWidget()
        lay = QVBoxLayout(self.inner)
        lay.setContentsMargins(12,8,12,8)
        lay.setSpacing(12)
        for i in range(8):
            lay.addWidget(TodoItem(show_placeholder=(i==0)))

        self.scroll.setWidget(self.inner)

        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(self.title_bar); cl.addWidget(self.scroll)

        self.show()

    def _adjust_color(self,c,f):
        col=QColor(c)
        return QColor(min(int(col.red()*f),255),
                      min(int(col.green()*f),255),
                      min(int(col.blue()*f),255)).name()

    def round_mask(self, r):
        path = QPainterPath()
        path.addRoundedRect(0,0,self.width(),self.height(),r,r)
        return QRegion(path.toFillPolygon().toPolygon())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.setMask(self.round_mask(16))

    def eventFilter(self, s, e):
        # 拖动标题栏
        if s is self.title_bar:
            if e.type()==QEvent.MouseButtonPress and e.button()==Qt.LeftButton:
                self.old_pos = e.globalPos(); return True
            if e.type()==QEvent.MouseMove and self.old_pos:
                d = e.globalPos() - self.old_pos
                self.move(self.x()+d.x(), self.y()+d.y())
                self.old_pos = e.globalPos(); return True
            if e.type()==QEvent.MouseButtonRelease:
                self.old_pos = None; return True
        return super().eventFilter(s, e)

    def mousePressEvent(self, e):
        if e.button()==Qt.LeftButton:
            self.old_pos = e.globalPos()
            self.resizing_edge = self._get_edge(e.pos())

    def mouseMoveEvent(self, e):
        if self.resizing_edge and self.old_pos:
            d = e.globalPos() - self.old_pos; g = self.geometry()
            if "left" in self.resizing_edge: g.setLeft(g.left()+d.x())
            if "right" in self.resizing_edge: g.setRight(g.right()+d.x())
            if "top" in self.resizing_edge: g.setTop(g.top()+d.y())
            if "bottom" in self.resizing_edge: g.setBottom(g.bottom()+d.y())
            self.setGeometry(g); self.old_pos = e.globalPos()
        else:
            ed = self._get_edge(e.pos())
            cmap = {
                "top_left": Qt.SizeFDiagCursor, "top_right": Qt.SizeBDiagCursor,
                "bottom_left": Qt.SizeBDiagCursor, "bottom_right": Qt.SizeFDiagCursor,
                "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
                "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor, None: Qt.ArrowCursor
            }
            self.setCursor(cmap.get(ed, Qt.ArrowCursor))

    def mouseReleaseEvent(self, e):
        self.old_pos = None; self.resizing_edge = None
        # 拖放结束更新遮罩
        self.setMask(self.round_mask(16))
        self.setCursor(Qt.ArrowCursor)

    def _get_edge(self, pos):
        r = self.rect(); x,y = pos.x(), pos.y()
        return (
            "top_left" if x<EDGE_MARGIN and y<EDGE_MARGIN else
            "top_right" if x>r.width()-EDGE_MARGIN and y<EDGE_MARGIN else
            "bottom_left" if x<EDGE_MARGIN and y>r.height()-EDGE_MARGIN else
            "bottom_right" if x>r.width()-EDGE_MARGIN and y>r.height()-EDGE_MARGIN else
            "left" if x<EDGE_MARGIN else "right" if x>r.width()-EDGE_MARGIN else
            "top" if y<EDGE_MARGIN else "bottom" if y>r.height()-EDGE_MARGIN else None
        )
