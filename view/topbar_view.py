from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics
import platform

class TopBar(QWidget):
    def __init__(self):
        super().__init__()
        
        self._base_label_style = """
            QLabel {
                color: #ffffff;
                background: transparent;
                padding: 6px 12px;
                margin: 0px 2px;
                border: none;
            }
        """
        
        self._color_cache = {} 
        
        self.setup_window()
        self.setup_ui()
        self.reserve_screen_space()

    def setup_window(self):
        flags = (Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool)
        
        if platform.system() != "Windows":
            flags |= Qt.WindowType.X11BypassWindowManagerHint
            
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        
        self.setFixedHeight(32)
        self.setFixedWidth(screen.width())
        self.move(0, 0)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(16, 16, 16, 245);
                border-bottom: 1px solid rgba(255, 255, 255, 50);
            }
        """)

        font = self._get_optimal_font()
        
        self.date_label = QLabel("21 jul")
        self.time_label = QLabel("22:24:28")
        self.ram_label = QLabel("RAM 66%")
        self.cpu_label = QLabel("CPU 43%")
        
        self.media_label = QLabel("")
        self.media_label.setFont(font)
        self.media_label.setStyleSheet(self._base_label_style + """
            QLabel {
                color: #ffffff;
                font-weight: bold;
                max-width: 400px;
            }
        """)
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_label.hide()  
        
        labels = [self.date_label, self.time_label, self.ram_label, self.cpu_label]
        for label in labels:
            label.setFont(font)
            label.setStyleSheet(self._base_label_style)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        layout.addWidget(self.date_label)
        layout.addWidget(self.time_label)
        
        separator_left = QLabel("|")
        separator_left.setFont(font)
        separator_left.setStyleSheet("color: rgba(255, 255, 255, 100); padding: 6px 4px;")
        layout.addWidget(separator_left)
        
        layout.addStretch()
        
        layout.addWidget(self.media_label)
        
        layout.addStretch()
        
        separator_right = QLabel("|")
        separator_right.setFont(font)
        separator_right.setStyleSheet("color: rgba(255, 255, 255, 100); padding: 6px 4px;")
        layout.addWidget(separator_right)
        
        layout.addWidget(self.ram_label)
        layout.addWidget(self.cpu_label)
        
        self.setLayout(layout)

    def _get_optimal_font(self):
        fonts_to_try = ["Consolas", "Monaco", "monospace"]
        
        for font_name in fonts_to_try:
            font = QFont(font_name, 9)
            if font.exactMatch():
                return font
        
        return QFont("monospace", 9)

    def reserve_screen_space(self):
        try:
            system = platform.system()
            if system == "Windows":
                self._reserve_space_windows()
            elif system == "Linux":
                self._reserve_space_linux()
        except Exception as e:
            print(f"Aviso: Não foi possível reservar espaço na tela: {e}")

    def _reserve_space_windows(self):
        import ctypes
        from ctypes import wintypes
        
        try:
            ABM_NEW = 0x00000000
            ABM_SETPOS = 0x00000003
            ABE_TOP = 1
            
            class APPBARDATA(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("hWnd", wintypes.HWND),
                    ("uCallbackMessage", wintypes.UINT),
                    ("uEdge", wintypes.UINT),
                    ("rc", wintypes.RECT),
                    ("lParam", wintypes.LPARAM),
                ]
            
            shell32 = ctypes.windll.shell32
            
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.hWnd = int(self.winId())
            abd.uCallbackMessage = 0
            abd.uEdge = ABE_TOP
            
            screen_width = self.width()  
            abd.rc.left = 0
            abd.rc.top = 0
            abd.rc.right = screen_width
            abd.rc.bottom = self.height()
            
            shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
            shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))
            
        except Exception as e:
            print(f"Falha ao reservar espaço no Windows: {e}")

    def _reserve_space_linux(self):
        try:
            self.setProperty("_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DOCK")
            self.setProperty("_NET_WM_STATE", "_NET_WM_STATE_ABOVE")
            
            screen_width = self.width()
            strut = [0, 0, self.height(), 0]
            strut_partial = [0, 0, self.height(), 0, 0, 0, 0, screen_width-1, 0, 0, 0, 0]
            
            self.setProperty("_NET_WM_STRUT", strut)
            self.setProperty("_NET_WM_STRUT_PARTIAL", strut_partial)
            
        except Exception as e:
            print(f"Falha ao reservar espaço no Linux: {e}")

    def update_ram_usage(self, percentage):
        color = self._get_usage_color(percentage)
        self.ram_label.setText(f"RAM {percentage:.0f}%")
        self._update_label_color(self.ram_label, color)

    def update_cpu_usage(self, percentage):
        color = self._get_usage_color(percentage)
        self.cpu_label.setText(f"CPU {percentage:.0f}%")
        self._update_label_color(self.cpu_label, color)

    def update_media_info(self, media_text: str):
        if media_text and media_text.strip():
            self.media_label.setText(media_text)
            self.media_label.show()
        else:
            self.media_label.hide()

    def update_date(self, date_text: str):
        self.date_label.setText(date_text)

    def update_time(self, time_text: str):
        self.time_label.setText(time_text)

    def _get_usage_color(self, percentage):
        rounded_pct = round(percentage / 5) * 5
        
        if rounded_pct not in self._color_cache:
            if rounded_pct < 50:
                self._color_cache[rounded_pct] = "#ffffff"
            elif rounded_pct < 75:
                self._color_cache[rounded_pct] = "#ffaa00"
            else:
                self._color_cache[rounded_pct] = "#ff6b6b"
                
        return self._color_cache[rounded_pct]

    def _update_label_color(self, label, color):
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: transparent;
                padding: 6px 12px;
                margin: 0px 2px;
                border: none;
            }}
        """)

    def closeEvent(self, event):
        super().closeEvent(event)