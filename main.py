import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from view.topbar_view import TopBar
from controller.main_controller import MainController

class OptimizedApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Evita fechar acidentalmente
        
        # Configurações de otimização para PyQt6
        # High DPI é habilitado por padrão no PyQt6
        
        self.topbar = TopBar()
        self.controller = MainController(self.topbar)
        
        # Signal handler para cleanup adequado
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Timer para permitir Ctrl+C
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)

    def signal_handler(self, signum, frame):
        """Handle para sinais do sistema"""
        print("\nFinalizando aplicação...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Cleanup completo da aplicação"""
        try:
            if hasattr(self, 'controller'):
                self.controller.cleanup()
            if hasattr(self, 'timer'):
                self.timer.stop()
            if hasattr(self, 'topbar'):
                self.topbar.close()
        except:
            pass

    def run(self):
        """Executa a aplicação"""
        try:
            self.topbar.show()
            return self.app.exec()
        except KeyboardInterrupt:
            self.cleanup()
            return 0
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app_instance = OptimizedApp()
        exit_code = app_instance.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)