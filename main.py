"""Desktop system monitor widget using PySide6."""

import sys
import time

import psutil
from PySide6.QtCore import QTimer, Qt, QPoint, QRectF
from PySide6.QtGui import QAction, QFont, QIcon, QMouseEvent, QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QProgressBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)


class SystemMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Window flags: frameless, always on top, tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.drag_pos: QPoint | None = None
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.disk_path = "C:/" if sys.platform == "win32" else "/"

        # Start with current process CPU reading to avoid first-call returning 0.0
        psutil.cpu_percent(interval=None)
        self._build_ui()
        self._setup_tray()
        self._setup_timer()
        self._center_on_screen()

    def _build_ui(self):
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(
            """
            #container {
                background-color: rgba(30, 30, 30, 220);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
            QLabel {
                color: #eeeeee;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
            }
            QLabel#title {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#value {
                color: #cccccc;
                font-size: 12px;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 30);
                text-align: center;
                height: 10px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #4fc3f7;
            }
            """
        )

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("系统监控")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setObjectName("value")
        layout.addWidget(self.cpu_label)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setTextVisible(False)
        layout.addWidget(self.cpu_bar)

        self.mem_label = QLabel("内存: --%")
        self.mem_label.setObjectName("value")
        layout.addWidget(self.mem_label)

        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        self.mem_bar.setTextVisible(False)
        layout.addWidget(self.mem_bar)

        self.disk_label = QLabel("磁盘: --%")
        self.disk_label.setObjectName("value")
        layout.addWidget(self.disk_label)

        self.disk_bar = QProgressBar()
        self.disk_bar.setRange(0, 100)
        self.disk_bar.setTextVisible(False)
        layout.addWidget(self.disk_bar)

        self.net_label = QLabel("网络: ↓ --  ↑ --")
        self.net_label.setObjectName("value")
        layout.addWidget(self.net_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)

        self.setFixedSize(220, 240)

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(1000)
        self._update_stats()

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_tray_icon(0))

        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.setToolTip("系统监控小部件")
        self.tray_icon.show()

    def _create_tray_icon(self, value: float) -> QIcon:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 50, 50, 220))
        painter.drawEllipse(4, 4, size - 8, size - 8)

        # Progress arc
        pen_width = 8
        rect = QRectF(8, 8, size - 16, size - 16)
        start_angle = 90 * 16
        span_angle = -int(value * 360 * 16 / 100)

        painter.setPen(Qt.PenStyle.NoPen)
        color = QColor(255, 112, 67) if value > 80 else QColor(79, 195, 247)
        painter.setBrush(color)
        painter.drawPie(rect, start_angle, span_angle)

        # Inner circle to make it a ring
        painter.setBrush(QColor(30, 30, 30, 220))
        inner_rect = QRectF(16, 16, size - 32, size - 32)
        painter.drawEllipse(inner_rect)

        # Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        text = f"{int(value)}"
        text_rect = painter.boundingRect(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
        return QIcon(pixmap)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 24
        x = geo.right() - self.width() - margin
        y = geo.top() + margin
        self.move(x, y)

    def _update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(self.disk_path)

        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.cpu_bar.setValue(int(cpu))
        self.cpu_bar.setStyleSheet(
            self._bar_style(cpu, "#4fc3f7", "#ff7043")
        )
        self.tray_icon.setIcon(self._create_tray_icon(cpu))
        self.tray_icon.setToolTip(
            f"CPU: {cpu:.1f}%\n内存: {mem.percent:.1f}%\n磁盘: {disk.percent:.1f}%"
        )

        self.mem_label.setText(
            f"内存: {mem.percent:.1f}%  ({self._format_bytes(mem.used)})"
        )
        self.mem_bar.setValue(int(mem.percent))
        self.mem_bar.setStyleSheet(
            self._bar_style(mem.percent, "#66bb6a", "#ff7043")
        )

        self.disk_label.setText(
            f"磁盘: {disk.percent:.1f}%  ({self._format_bytes(disk.used)})"
        )
        self.disk_bar.setValue(int(disk.percent))
        self.disk_bar.setStyleSheet(
            self._bar_style(disk.percent, "#ffa726", "#ef5350")
        )

        net_io = psutil.net_io_counters()
        now = time.time()
        dt = now - self.last_net_time
        if dt > 0:
            down_speed = max(0, (net_io.bytes_recv - self.last_net_io.bytes_recv) / dt)
            up_speed = max(0, (net_io.bytes_sent - self.last_net_io.bytes_sent) / dt)
            self.net_label.setText(
                f"网络: ↓{self._format_speed(down_speed)}  ↑{self._format_speed(up_speed)}"
            )
        self.last_net_io = net_io
        self.last_net_time = now

    def _bar_style(self, value: float, low_color: str, high_color: str):
        color = high_color if value > 80 else low_color
        return f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 30);
                text-align: center;
                height: 10px;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {color};
            }}
        """

    @staticmethod
    def _format_bytes(n: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(n) < 1024.0:
                return f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}PB"

    @staticmethod
    def _format_speed(n: float) -> str:
        for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
            if abs(n) < 1024.0:
                return f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}TB/s"

    # Mouse dragging support
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        menu.exec(event.globalPos())


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)

    widget = SystemMonitorWidget()
    widget.show()

    test_mode = "--test" in sys.argv
    if test_mode:
        QTimer.singleShot(3000, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
