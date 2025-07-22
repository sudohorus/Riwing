from PyQt6.QtCore import QObject, pyqtSignal

class MediaInfoWorker(QObject):
    result = pyqtSignal(str)

    def __init__(self, media_detector):
        super().__init__()
        self.media_detector = media_detector

    def run(self):
        try:
            media_info = self.media_detector.get_current_media()
            if media_info:
                media_text = self.media_detector.format_media_text(media_info, max_length=60)
                self.result.emit(media_text)
            else:
                self.result.emit("")
        except Exception as e:
            print(f"[MediaInfoWorker] Erro: {e}")
            self.result.emit("")
