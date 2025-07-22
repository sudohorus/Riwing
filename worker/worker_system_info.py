from PyQt6.QtCore import QObject, pyqtSignal

class SystemInfoWorker(QObject):
    result = pyqtSignal(float, float) 

    def __init__(self, system_info):
        super().__init__()
        self.system_info = system_info

    def run(self):
        try:
            ram = self.system_info.get_ram_usage()
            cpu = self.system_info.get_cpu_usage()
            self.result.emit(ram, cpu)
        except Exception as e:
            print(f"[SystemInfoWorker] Erro: {e}")
