from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QListWidget, QListWidgetItem, QLabel,
                             QGraphicsDropShadowEffect, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QIcon, QPixmap, QColor, QAction
from typing import List, Union
from model.launcher_model import AppInfo, FileInfo, WebInfo, CommandInfo, MathInfo
import os
import platform
import subprocess
import sys

class OverlayWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.showFullScreen()

class CustomListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        
    def create_item_widget(self, item_data) -> QListWidgetItem:
        item = QListWidgetItem()
        
        if isinstance(item_data, AppInfo):
            item.setText(item_data.name)
            if item_data.icon_path and os.path.exists(item_data.icon_path):
                icon = QIcon(item_data.icon_path)
                item.setIcon(icon)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        elif isinstance(item_data, FileInfo):
            size_str = self.format_file_size(item_data.size)
            item.setText(f"📄 {item_data.name} ({size_str})")
            item.setToolTip(item_data.path)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        elif hasattr(item_data, 'type') and item_data.type == "folder":
            item.setText(f"📁 {item_data.name}")
            item.setToolTip(item_data.path)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        elif isinstance(item_data, WebInfo):
            item.setText(f"🌐 {item_data.name}")
            item.setToolTip(item_data.url)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        elif isinstance(item_data, CommandInfo):
            item.setText(f"> {item_data.name}")
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        elif isinstance(item_data, MathInfo):
            item.setText(f"> {item_data.name}")
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            
        return item
    
    def format_file_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return

        item_data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(item_data, (AppInfo, FileInfo)):
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: rgba(40, 40, 40, 240);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 40);
                    padding: 4px;
                    border-radius: 6px;
                }
                QMenu::item {
                    padding: 6px 12px;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: rgba(70, 130, 255, 90);
                }
            """)
            
            
            open_folder_action = QAction("Abrir local do arquivo", self)
            
            def open_folder():
                path = item_data.path
                if os.path.exists(path):
                    folder = os.path.dirname(path)
                    subprocess.Popen(f'explorer /select,"{path}"')
            
            open_folder_action.triggered.connect(open_folder)
            menu.addAction(open_folder_action)
            menu.exec(event.globalPos())

class LauncherView(QWidget):
    item_executed = pyqtSignal(object)
    search_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.overlay = None
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_animations()
        
    def setup_ui(self):
        flags = (Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint)
        
        if platform.system() == "Linux":
            flags |= Qt.WindowType.X11BypassWindowManagerHint
            
        self.setWindowFlags(flags)
        
        if platform.system() != "Windows":
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(720, 480)
        self.center_window()
        
        background_color = "rgba(0, 0, 0, 240)" if platform.system() == "Windows" else "rgb(0, 0, 0)"
        
        self.setStyleSheet(f"""
            LauncherView {{
                background-color: {background_color};
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }}
            QLineEdit {{
                background-color: rgba(26, 26, 26, 200);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 14px 16px;
                font-size: 15px;
                color: #ffffff;
                margin: 16px;
                font-family: "Consolas", "Monaco", monospace;
                font-weight: normal;
                selection-background-color: rgba(70, 130, 255, 100);
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(70, 130, 255, 120);
                background-color: rgba(30, 30, 30, 220);
            }}
            QListWidget {{
                background-color: transparent;
                border: none;
                margin: 0px 16px 8px 16px;
                outline: none;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 13px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 10px 14px;
                margin: 1px 0px;
                color: #ffffff;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(70, 130, 255, 80);
                color: #ffffff;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 15);
            }}
            QLabel {{
                color: rgba(255, 255, 255, 140);
                font-size: 11px;
                margin: 8px 20px 12px 20px;
                font-family: "Consolas", "Monaco", monospace;
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 60);
                min-height: 20px;
                border-radius: 3px;
                margin: 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 90);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)
        
        self.background_widget = QWidget()
        self.background_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.background_widget)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.drag_area = QWidget()
        self.drag_area.setFixedHeight(20) 
        self.drag_area.mousePressEvent = self.mousePressEvent
        self.drag_area.mouseMoveEvent = self.mouseMoveEvent
        self.drag_area.mouseReleaseEvent = self.mouseReleaseEvent
        content_layout.addWidget(self.drag_area)
        
        self.search_input = QLineEdit()
        self.update_placeholder()
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.returnPressed.connect(self.execute_selected)
        
        self.results_list = CustomListWidget()
        self.results_list.itemDoubleClicked.connect(self.execute_selected)
        
        self.info_label = QLabel()
        self.update_info_label()
        
        content_layout.addWidget(self.search_input)
        content_layout.addWidget(self.results_list)
        content_layout.addWidget(self.info_label)
        
        self.background_widget.setLayout(content_layout)
        self.setLayout(main_layout)
        
        if platform.system() != "Windows":
            self.setup_shadow_effect()
        
    def setup_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
    def setup_animations(self):
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def update_placeholder(self):
        self.search_input.setPlaceholderText("Digite para buscar...")
        
    def update_info_label(self):
        self.info_label.setText("Ctrl+Space: abrir • Enter: executar • Esc: fechar")
        
    def setup_shortcuts(self):
        self.close_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.close_shortcut.activated.connect(self.hide_launcher)
        
        self.up_shortcut = QShortcut(QKeySequence("Up"), self.search_input)
        self.up_shortcut.activated.connect(self.navigate_up)
        
        self.down_shortcut = QShortcut(QKeySequence("Down"), self.search_input)
        self.down_shortcut.activated.connect(self.navigate_down)
        
        self.tab_shortcut = QShortcut(QKeySequence("Tab"), self.search_input)
        self.tab_shortcut.activated.connect(self.autocomplete)
        
        try:
            import pynput
            from pynput import keyboard
            
            def on_hotkey():
                QTimer.singleShot(0, self.toggle_visibility)
                
            self.listener = keyboard.GlobalHotKeys({
                '<ctrl>+<space>': on_hotkey
            })
            self.listener.start()
            
        except ImportError:
            print("pynput não instalado. Use 'pip install pynput' para atalho global")
            self.toggle_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
            self.toggle_shortcut.activated.connect(self.toggle_visibility)
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 3
        self.move(x, y)
    
    def on_search_changed(self):
        query = self.search_input.text()
        self.search_requested.emit(query)
    
    def update_results(self, results: List[Union[AppInfo, FileInfo, WebInfo, CommandInfo, MathInfo]]):
        self.results_list.clear()
        
        for result in results[:12]:
            item = self.results_list.create_item_widget(result)
            self.results_list.addItem(item)
        
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def navigate_up(self):
        current = self.results_list.currentRow()
        if current > 0:
            self.results_list.setCurrentRow(current - 1)
        elif self.results_list.count() > 0:
            self.results_list.setCurrentRow(self.results_list.count() - 1)
    
    def navigate_down(self):
        current = self.results_list.currentRow()
        if current < self.results_list.count() - 1:
            self.results_list.setCurrentRow(current + 1)
        elif self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def autocomplete(self):
        current_item = self.results_list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(item_data, AppInfo):
                app_name = item_data.name.lower().replace(" ", "")
                self.search_input.setText(f".{app_name}")
    
    def execute_selected(self):
        current_item = self.results_list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.ItemDataRole.UserRole)
            if item_data:
                self.item_executed.emit(item_data)
                self.hide_launcher()
    
    def hide_launcher(self):
        if platform.system() == "Windows":
            self._hide_complete()
        else:
            self.opacity_animation.setStartValue(1.0)
            self.opacity_animation.setEndValue(0.0)
            self.opacity_animation.finished.connect(self._hide_complete)
            self.opacity_animation.start()
    
    def _hide_complete(self):
        self.hide()
        if self.overlay:
            self.overlay.hide()
        self.search_input.clear()
        self.setWindowOpacity(1.0)
        if hasattr(self.opacity_animation, 'finished'):
            try:
                self.opacity_animation.finished.disconnect()
            except:
                pass
    
    def force_focus(self, widget):
        widget.setFocus(Qt.FocusReason.OtherFocusReason)
        widget.clearFocus()
        widget.setFocus(Qt.FocusReason.OtherFocusReason)

    def show_launcher(self):
        if platform.system() != "Windows":
            if not self.overlay:
                self.overlay = OverlayWindow()
            else:
                self.overlay.show()

        if platform.system() == "Windows":
            self.setWindowOpacity(1.0)
            self.show()
        else:
            self.setWindowOpacity(0.0)
            self.show()
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        
        self.raise_()
        self.activateWindow()
        self.center_window()
        self.search_input.clear()
        
        if platform.system() != "Windows":
            self.opacity_animation.setStartValue(0.0)
            self.opacity_animation.setEndValue(1.0)
            self.opacity_animation.start()
        
        QTimer.singleShot(150, lambda: self.force_focus(self.search_input))
        
        self.search_requested.emit("")
        
    def toggle_visibility(self):
        if self.isVisible():
            self.hide_launcher()
        else:
            self.show_launcher()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide_launcher()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if getattr(self, "_drag_active", False) and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
