import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton, QHBoxLayout,
    QVBoxLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QPoint, QEvent
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
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 200)

        self.old_pos = None
        self.resizing_edge = None
        self.bg_color, self.btn_color = random.choice(COLOR_SCHEMES)

        # 外层容器
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            background-color: {self.bg_color};
            border-radius: 16px;
        """)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.addWidget(self.container)

        # 标题栏
        self.title_bar = QWidget(self.container)
        self.title_bar.setFixedHeight(30)
        self.title_bar.installEventFilter(self)
        self.title_bar.setStyleSheet("background: transparent;")

        self.title_edit = QLineEdit("自定义便签", self.title_bar)
        self.title_edit.setFixedWidth(120)
        self.title_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 14px;
                padding-left: 6px;
                font-family: "SVGASYS", "SimHei";
            }
        """)

        def cute_button(symbol):
            btn = QPushButton(symbol)
            btn.setFixedSize(24,24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.btn_color};
                    border: none;
                    border-radius: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    font-family: "SVGASYS", "SimHei";
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {self._adjust_color(self.btn_color, 1.2)};
                }}
            """)
            return btn

        self.min_btn = cute_button("—")
        self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn = cute_button("✕")
        self.close_btn.clicked.connect(self.close)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8,4,8,0)
        title_layout.addWidget(self.title_edit)
        title_layout.addStretch()
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.close_btn)

        # 文本编辑区
        self.text_edit = QTextEdit(self.container)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.bg_color};
                border: none;
                padding: 6px;
                font-size: 14px;
                font-family: "SVGASYS", "SimHei";
            }}
            QTextEdit QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 0;
                border-radius: 3px;
            }}
            QTextEdit QScrollBar::handle:vertical {{
                background: {self._adjust_color(self.btn_color,0.9)};
                min-height: 24px;
                border-radius: 3px;
            }}
            QTextEdit QScrollBar::handle:vertical:hover {{
                background: {self._adjust_color(self.btn_color,1.2)};
            }}
            QTextEdit QScrollBar::add-line:vertical,
            QTextEdit QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QTextEdit QScrollBar::add-page:vertical,
            QTextEdit QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(self.text_edit)

        self.show()

    def _adjust_color(self, hex_color, factor):
        c = QColor(hex_color)
        return QColor(
            min(int(c.red()*factor),255),
            min(int(c.green()*factor),255),
            min(int(c.blue()*factor),255)
        ).name()

    def eventFilter(self, source, event):
        if source == self.title_bar:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.old_pos = event.globalPos(); return True
            elif event.type() == QEvent.MouseMove and self.old_pos:
                delta = event.globalPos() - self.old_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_pos = event.globalPos(); return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.old_pos = None; return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_B:
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                fmt = cursor.charFormat()
                fmt.setFontWeight(QFont.Normal if fmt.fontWeight() > QFont.Normal else QFont.Bold)
                cursor.mergeCharFormat(fmt)
                self.text_edit.mergeCurrentCharFormat(fmt)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.resizing_edge = self._get_edge(event.pos())

    def mouseMoveEvent(self, event):
        if self.resizing_edge and self.old_pos:
            delta = event.globalPos() - self.old_pos
            geo = self.geometry()
            if "left" in self.resizing_edge: geo.setLeft(geo.left() + delta.x())
            if "right" in self.resizing_edge: geo.setRight(geo.right() + delta.x())
            if "top" in self.resizing_edge: geo.setTop(geo.top() + delta.y())
            if "bottom" in self.resizing_edge: geo.setBottom(geo.bottom() + delta.y())
            self.setGeometry(geo); self.old_pos = event.globalPos()
        else:
            edge = self._get_edge(event.pos())
            cursor_map = {
                "top_left": Qt.SizeFDiagCursor, "top_right": Qt.SizeBDiagCursor,
                "bottom_left": Qt.SizeBDiagCursor, "bottom_right": Qt.SizeFDiagCursor,
                "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
                "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor, None: Qt.ArrowCursor
            }
            self.setCursor(cursor_map.get(edge, Qt.ArrowCursor))

    def mouseReleaseEvent(self, event):
        self.old_pos = None; self.resizing_edge = None
        self.setCursor(Qt.ArrowCursor)

    def _get_edge(self, pos):
        rect = self.rect(); x, y = pos.x(), pos.y()
        return (
            "top_left" if x < 6 and y < 6 else
            "top_right" if x > rect.width() - 6 and y < 6 else
            "bottom_left" if x < 6 and y > rect.height() - 6 else
            "bottom_right" if x > rect.width() - 6 and y > rect.height() - 6 else
            "left" if x < 6 else "right" if x > rect.width() - 6 else
            "top" if y < 6 else "bottom" if y > rect.height() - 6 else None
        )
