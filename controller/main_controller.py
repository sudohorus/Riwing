from PyQt6.QtCore import QTimer, QObject
from model.system_info import SystemInfo
from model.media_detector import MediaDetector

class MainController(QObject):
    def __init__(self, topbar):
        super().__init__()
        self.topbar = topbar
        self.system_info = SystemInfo()
        self.media_detector = MediaDetector()
        
        # Configuração dos timers
        self.setup_timers()
        
        # Atualização inicial
        self.update_all()

    def setup_timers(self):
        """Configura os timers para atualizações periódicas"""
        
        # Timer para data/hora (atualiza a cada segundo)
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_info)
        self.time_timer.start(1000)
        
        # Timer para CPU/RAM (atualiza a cada 2 segundos)
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.update_system_info)
        self.system_timer.start(2000)
        
        # Timer para mídia (atualiza a cada 3 segundos para não sobrecarregar)
        self.media_timer = QTimer()
        self.media_timer.timeout.connect(self.update_media_info)
        self.media_timer.start(3000)

    def update_all(self):
        """Atualiza todas as informações imediatamente"""
        self.update_time_info()
        self.update_system_info()
        self.update_media_info()

    def update_time_info(self):
        """Atualiza data e hora"""
        try:
            current_time = self.system_info.get_time()
            current_date = self.system_info.get_date_short()
            
            self.topbar.update_time(current_time)
            self.topbar.update_date(current_date)
        except Exception as e:
            print(f"Erro ao atualizar informações de tempo: {e}")

    def update_system_info(self):
        """Atualiza informações do sistema (CPU/RAM)"""
        try:
            ram_usage = self.system_info.get_ram_usage()
            cpu_usage = self.system_info.get_cpu_usage()
            
            self.topbar.update_ram_usage(ram_usage)
            self.topbar.update_cpu_usage(cpu_usage)
        except Exception as e:
            print(f"Erro ao atualizar informações do sistema: {e}")

    def update_media_info(self):
        """Atualiza informações de mídia"""
        try:
            media_info = self.media_detector.get_current_media()
            
            if media_info:
                # Formatar o texto para exibição
                media_text = self.media_detector.format_media_text(media_info, max_length=60)
                self.topbar.update_media_info(media_text)
            else:
                # Limpar o display se não há mídia
                self.topbar.update_media_info("")
                
        except Exception as e:
            print(f"Erro ao detectar mídia: {e}")
            self.topbar.update_media_info("")

    def cleanup(self):
        """Cleanup dos timers e recursos"""
        try:
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'system_timer'):
                self.system_timer.stop()
            if hasattr(self, 'media_timer'):
                self.media_timer.stop()
        except Exception as e:
            print(f"Erro durante cleanup: {e}")