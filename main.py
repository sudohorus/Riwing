import sys
import signal
import atexit
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSlot
from view.topbar_view import TopBar
from controller.main_controller import MainController
from model.launcher_model import AppModel
from controller.search_controller import SearchController
from view.launcher_view import LauncherView

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
        
        self.topbar = TopBar()
        self.controller = MainController(self.topbar)
        
        self.launcher = RiwingLauncher()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)
        
        atexit.register(self.cleanup)
        
    def signal_handler(self, signum, frame):
        print("\nFinalizando aplicação...")
        self.cleanup()
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
        except:
            pass
            
    def run(self):
        try:
            self.topbar.show()
            self.launcher.view.hide()
            
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