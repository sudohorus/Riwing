import psutil
from datetime import datetime
import locale
import platform

class SystemInfo:
    _boot_time = None
    _cpu_count = None
    _locale_set = False
    _meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
              'jul', 'ago', 'set', 'out', 'nov', 'dez']
    
    @classmethod
    def _setup_locale(cls):
        if not cls._locale_set:
            try:
                if platform.system() == "Windows":
                    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
                else:
                    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except:
                pass
            cls._locale_set = True

    @staticmethod
    def get_time():
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    def get_date(cls):
        cls._setup_locale()
        now = datetime.now()
        try:
            return now.strftime("%d de %B")
        except:
            return now.strftime("%d/%m/%Y")

    @classmethod
    def get_date_short(cls):
        now = datetime.now()
        return f"{now.day} {cls._meses[now.month-1]}"

    @staticmethod
    def get_ram_usage():
        return psutil.virtual_memory().percent

    @staticmethod
    def get_cpu_usage():
        return psutil.cpu_percent(interval=0.5)

    @staticmethod
    def get_ram_info():
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percentage': memory.percent
        }

    @classmethod
    def get_cpu_info(cls):
        if cls._cpu_count is None:
            cls._cpu_count = psutil.cpu_count()
        
        cpu_freq = psutil.cpu_freq()
        return {
            'percentage': psutil.cpu_percent(interval=0.5),
            'cores': cls._cpu_count,
            'frequency': cpu_freq.current if cpu_freq else 0
        }

    @classmethod
    def get_system_uptime(cls):
        if cls._boot_time is None:
            cls._boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        uptime = datetime.now() - cls._boot_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def get_network_usage():
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }

    @staticmethod
    def format_bytes(bytes_value):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        for unit in units:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"