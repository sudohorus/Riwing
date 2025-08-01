import subprocess
import platform
import re
from typing import Optional, Dict
import time

class MediaDetector:
    def __init__(self):
        self.system = platform.system()
        self._last_track = None
        self._cache = {'data': None, 'timestamp': 0}
        self._cache_duration = 2 
        
    def get_current_media(self) -> Optional[Dict[str, str]]:
        current_time = time.time()
        if (self._cache['data'] is not None and 
            current_time - self._cache['timestamp'] < self._cache_duration):
            return self._cache['data']
            
        result = None
        if self.system == "Windows":
            result = self._get_windows_media()
            
        self._cache['data'] = result
        self._cache['timestamp'] = current_time
        return result
    
    def _get_windows_media(self) -> Optional[Dict[str, str]]:
        try:
            ps_script = '''
            $processes = Get-Process -Name "Spotify" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne "" -and $_.MainWindowTitle -ne "Spotify" -and $_.MainWindowTitle -ne "Spotify Free" -and $_.MainWindowTitle -ne "Spotify Premium"}
            
            if ($processes) {
                $title = $processes[0].MainWindowTitle
                if ($title -match "^(.+?)\\s*[-–—]\\s*(.+?)$") {
                    $artist = $matches[1].Trim()
                    $song = $matches[2].Trim()
                    Write-Output "$artist|$song|Spotify"
                } else {
                    Write-Output "Unknown Artist|$title|Spotify"
                }
            }
            '''
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run([
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", 
                "-WindowStyle", "Hidden", "-Command", ps_script
            ], capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
            
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split('\n')[0]  
                if '|' in line:
                    parts = line.split('|', 2)
                    if len(parts) >= 3:
                        artist = parts[0].strip()
                        title = parts[1].strip()
                        app = parts[2].strip()
                        
                        if artist and title:
                            return {
                                'artist': artist,
                                'title': title,
                                'app': app
                            }
                            
        except subprocess.TimeoutExpired:
            return self._get_windows_media_simple()
        except Exception as e:
            print(f"Erro na detecção Windows: {e}")
            
        return None
    
    def _get_windows_media_simple(self) -> Optional[Dict[str, str]]:
        try:
            result = subprocess.run([
                "tasklist", "/FI", "IMAGENAME eq Spotify.exe", "/FO", "CSV", "/V"
            ], capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]: 
                    if 'Spotify.exe' in line:
                        fields = line.split('","')
                        if len(fields) >= 9:
                            window_title = fields[-1].replace('"', '').strip()
                            if (window_title and window_title != "N/A" and 
                                window_title not in ["Spotify", "Spotify Free", "Spotify Premium"]):
                                
                                match = re.match(r'^(.+?)\s*[-–—]\s*(.+?)$', window_title)
                                if match:
                                    return {
                                        'artist': match.group(1).strip(),
                                        'title': match.group(2).strip(),
                                        'app': 'Spotify'
                                    }
                                else:
                                    return {
                                        'artist': 'Unknown Artist',
                                        'title': window_title,
                                        'app': 'Spotify'
                                    }
                                    
        except Exception as e:
            print(f"Erro no método alternativo: {e}")
            
        return None
    
    def format_media_text(self, media_info: Dict[str, str], max_length: int = 50) -> str:
        if not media_info:
            return ""
            
        artist = media_info.get('artist', 'Unknown')
        title = media_info.get('title', 'Unknown')
        
        title = re.sub(r'\s*\([^)]*\)\s*', '', title)  
        title = re.sub(r'\s*\[[^\]]*\]\s*', '', title) 
        
        text = f"{artist} - {title}"
        
        if len(text) > max_length:
            available = max_length - len(f"🎵 {artist} - ...") 
            if available > 10:  
                truncated_title = title[:available-3] + "..."
                text = f"{artist} - {truncated_title}"
            else:  
                text = text[:max_length-3] + "..."
                
        return text
    
    def is_media_playing(self) -> bool:
        return self.get_current_media() is not None
    
    def clear_cache(self):
        self._cache = {'data': None, 'timestamp': 0}