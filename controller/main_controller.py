from PyQt6.QtCore import QTimer, QObject, QThread
from model.system_info import SystemInfo
from model.media_detector import MediaDetector
from worker.worker_system_info import SystemInfoWorker
from worker.worker_media_info import MediaInfoWorker

class MainController(QObject):
    def __init__(self, topbar):
        super().__init__()
        self.topbar = topbar
        self.system_info = SystemInfo()
        self.media_detector = MediaDetector()

        self.setup_system_thread()
        self.setup_media_thread()
        self.setup_timers()
        self.update_all()

    def setup_timers(self):
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_info)
        self.time_timer.start(1000)

        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.start_system_worker)
        self.system_timer.start(2000)

        self.media_timer = QTimer()
        self.media_timer.timeout.connect(self.start_media_worker)
        self.media_timer.start(3000)

    def setup_system_thread(self):
        self.system_thread = QThread()
        self.system_worker = SystemInfoWorker(self.system_info)
        self.system_worker.moveToThread(self.system_thread)

        self.system_thread.started.connect(self.system_worker.run)
        self.system_worker.result.connect(self.on_system_info_updated)
        self.system_worker.result.connect(self.system_thread.quit)

    def start_system_worker(self):
        if not self.system_thread.isRunning():
            self.system_thread.start()

    def on_system_info_updated(self, ram_usage, cpu_usage):
        self.topbar.update_ram_usage(ram_usage)
        self.topbar.update_cpu_usage(cpu_usage)

    def setup_media_thread(self):
        self.media_thread = QThread()
        self.media_worker = MediaInfoWorker(self.media_detector)
        self.media_worker.moveToThread(self.media_thread)

        self.media_thread.started.connect(self.media_worker.run)
        self.media_worker.result.connect(self.on_media_info_updated)
        self.media_worker.result.connect(self.media_thread.quit)

    def start_media_worker(self):
        if not self.media_thread.isRunning():
            self.media_thread.start()

    def on_media_info_updated(self, media_text):
        self.topbar.update_media_info(media_text)

    def update_time_info(self):
        try:
            current_time = self.system_info.get_time()
            current_date = self.system_info.get_date_short()

            self.topbar.update_time(current_time)
            self.topbar.update_date(current_date)
        except Exception as e:
            print(f"Erro ao atualizar informações de tempo: {e}")

    def update_all(self):
        self.update_time_info()
        self.start_system_worker()
        self.start_media_worker()

    def cleanup(self):
        try:
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'system_timer'):
                self.system_timer.stop()
            if hasattr(self, 'media_timer'):
                self.media_timer.stop()
            if self.system_thread.isRunning():
                self.system_thread.quit()
                self.system_thread.wait()
            if self.media_thread.isRunning():
                self.media_thread.quit()
                self.media_thread.wait()
        except Exception as e:
            print(f"Erro durante cleanup: {e}")
