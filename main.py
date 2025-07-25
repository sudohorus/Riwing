import sys
import signal
import atexit
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSlot
from PyQt6.QtGui import QIcon, QAction
from view.topbar_view import TopBar
from controller.main_controller import MainController
from model.launcher_model import AppModel
from controller.search_controller import SearchController
from view.launcher_view import LauncherView

os.environ["PYTHONIOENCODING"] = "utf-8"

class SystemTrayManager:
    def __init__(self, main_app):
        self.main_app = main_app
        
        self.tray_icon = QSystemTrayIcon()
        
        icon_paths = [
            "icon.ico",
            "media/icon.ico", 
            os.path.join(os.path.dirname(__file__), "icon.ico"),
            os.path.join(sys._MEIPASS, "icon.ico") if getattr(sys, 'frozen', False) else None
        ]
        
        icon_set = False
        for path in icon_paths:
            if path and os.path.exists(path):
                self.tray_icon.setIcon(QIcon(path))
                icon_set = True
                break
        
        if not icon_set:
            self.tray_icon.setIcon(self.main_app.app.style().standardIcon(
                self.main_app.app.style().StandardPixmap.SP_ComputerIcon
            ))
        
        self.setup_tray_menu()
        self.tray_icon.show()
        
    
    def setup_tray_menu(self):
        menu = QMenu()
        
        about_action = QAction("Sobre", menu)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Sair", menu)
        quit_action.triggered.connect(self.main_app.quit_application)
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("Riwing")
    
    
    def show_about(self):
        
        msg = QMessageBox()
        msg.setWindowTitle("Sobre Riwing")
        msg.setText("Riwing v0.1\nAplicativo para personalização do Windows.\n© 2025 sudohorus")
        msg.setIcon(QMessageBox.Icon.Information)
        if not self.tray_icon.icon().isNull():
            msg.setIconPixmap(self.tray_icon.icon().pixmap(64, 64))
        msg.exec()

class RiwingLauncher(QObject):
    def __init__(self):
        super().__init__()
        
        self.model = AppModel()
        self.controller = SearchController(self.model)
        self.view = LauncherView()
        
        self.view.search_requested.connect(self.on_search_requested)
        self.view.item_executed.connect(self.controller.execute_item)
        
        self.model.load_installed_apps()
   
    @pyqtSlot(str)
    def on_search_requested(self, query: str):
        results = self.controller.search(query)
        self.view.update_results(results)
   
    def cleanup(self):
        self.model.cleanup()

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  
        
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", 
                               "System tray não está disponível neste sistema.")
            sys.exit(1)
        
        self.topbar = TopBar()
        self.controller = MainController(self.topbar)
        self.launcher = RiwingLauncher()
        
        self.tray_manager = SystemTrayManager(self)
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)
        
        atexit.register(self.cleanup)
    
    def signal_handler(self, signum, frame):
        print("\nFinalizando aplicação...")
        self.quit_application()
        
    def quit_application(self):
        self.cleanup()
        self.app.quit()
        sys.exit(0)
        
    def cleanup(self):
        try:
            if hasattr(self, 'controller'):
                self.controller.cleanup()
            if hasattr(self, 'launcher'):
                self.launcher.cleanup()
            if hasattr(self, 'timer'):
                self.timer.stop()
            if hasattr(self, 'topbar'):
                self.topbar.close()
            if hasattr(self, 'tray_manager') and self.tray_manager.tray_icon:
                self.tray_manager.tray_icon.hide()
        except:
            pass
            
    def run(self):
        try:
            self.topbar.show()
            self.launcher.view.hide()
            
            if self.tray_manager.tray_icon.supportsMessages():
                self.tray_manager.tray_icon.showMessage(
                    "Riwing",
                    "Aplicativo iniciado com sucesso - Executando em segundo plano",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
            
            return self.app.exec()
            
        except KeyboardInterrupt:
            self.cleanup()
            return 0
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app_instance = App()
        exit_code = app_instance.run()
        sys.exit(exit_code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Erro fatal: {e}")
        sys.exit(1)