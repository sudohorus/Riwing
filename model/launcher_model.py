import os
import winreg
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union
import win32ui
import win32gui
import win32con
import win32api
from PIL import Image
import tempfile
import math
import re

class AppInfo:
    def __init__(self, name: str, path: str, icon_path: str = None):
        self.name = name
        self.path = path
        self.icon_path = icon_path
        self.type = "app"

class FileInfo:
    def __init__(self, name: str, path: str, size: int = 0):
        self.name = name
        self.path = path
        self.size = size
        self.type = "file"

class WebInfo:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.type = "web"

class CommandInfo:
    def __init__(self, name: str, command: str):
        self.name = name
        self.command = command
        self.type = "command"

class MathInfo:
    def __init__(self, expression: str, result: str):
        self.expression = expression
        self.result = result
        self.name = f"{expression} = {result}"
        self.type = "math"

class FolderInfo:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.type = "folder"

class AppModel:
    def __init__(self):
        self.apps_cache: List[AppInfo] = []
        self.icon_cache: Dict[str, str] = {}
        self.temp_dir = tempfile.mkdtemp()
        
    def load_installed_apps(self):
        self.apps_cache = []
        
        system_apps = [
            {"name": "Calculadora", "path": "calc.exe"},
            {"name": "Bloco de Notas", "path": "notepad.exe"},
            {"name": "Paint", "path": "mspaint.exe"},
            {"name": "Explorador de Arquivos", "path": "explorer.exe"},
            {"name": "Prompt de Comando", "path": "cmd.exe"},
            {"name": "PowerShell", "path": "powershell.exe"},
            {"name": "Painel de Controle", "path": "control.exe"},
            {"name": "Gerenciador de Tarefas", "path": "taskmgr.exe"},
            {"name": "Configurações", "path": "ms-settings:"},
        ]
        
        for app in system_apps:
            icon_path = self.extract_icon(app["path"])
            app_info = AppInfo(app["name"], app["path"], icon_path)
            self.apps_cache.append(app_info)
        
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, subkey_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                app_info = self.get_app_info(app_key)
                                if app_info:
                                    self.apps_cache.append(app_info)
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                print(f"Erro ao acessar registry {subkey_path}: {e}")
                continue
        
        self.load_start_menu_apps()
        
        seen_paths = set()
        unique_apps = []
        for app in self.apps_cache:
            real_path = os.path.realpath(app.path).lower()
            if real_path not in seen_paths and os.path.exists(app.path):
                seen_paths.add(real_path)
                unique_apps.append(app)
        
        self.apps_cache = sorted(unique_apps, key=lambda x: x.name.lower())
    
    def extract_icon(self, exe_path: str) -> Optional[str]:
        if exe_path in self.icon_cache:
            return self.icon_cache[exe_path]
        
        icon_path = None
        
        try:
            icon_path = self._extract_with_shgetfileinfo(exe_path)
            if icon_path:
                self.icon_cache[exe_path] = icon_path
                return icon_path
            
            icon_path = self._extract_with_extracticon(exe_path)
            if icon_path:
                self.icon_cache[exe_path] = icon_path
                return icon_path
                
            icon_path = self._extract_from_registry(exe_path)
            if icon_path:
                self.icon_cache[exe_path] = icon_path
                return icon_path
        
        except Exception as e:
            print(f"Erro ao extrair ícone de {exe_path}: {e}")
        
        return None

    def _extract_with_shgetfileinfo(self, exe_path: str) -> Optional[str]:
        try:
            import ctypes
            from ctypes import wintypes, windll
            
            class SHFILEINFO(ctypes.Structure):
                _fields_ = [
                    ("hIcon", wintypes.HANDLE),
                    ("iIcon", ctypes.c_int),
                    ("dwAttributes", wintypes.DWORD),
                    ("szDisplayName", wintypes.WCHAR * 260),
                    ("szTypeName", wintypes.WCHAR * 80),
                ]

            shfileinfo = SHFILEINFO()
            SHGFI_ICON = 0x000000100
            SHGFI_LARGEICON = 0x000000000
            
            ret = windll.shell32.SHGetFileInfoW(
                exe_path, 0, ctypes.byref(shfileinfo),
                ctypes.sizeof(shfileinfo), SHGFI_ICON | SHGFI_LARGEICON
            )
            
            if ret and shfileinfo.hIcon:
                icon_path = self._hicon_to_image(shfileinfo.hIcon, exe_path, "shgetfileinfo")
                windll.user32.DestroyIcon(shfileinfo.hIcon)
                return icon_path
                
        except Exception:
            pass
        return None

    def _extract_with_extracticon(self, exe_path: str) -> Optional[str]:
        try:
            if exe_path in ['calc.exe', 'notepad.exe', 'mspaint.exe']:
                sys_path = os.path.join(os.environ['WINDIR'], 'System32', exe_path)
                if os.path.exists(sys_path):
                    exe_path = sys_path
            
            for icon_index in range(6):
                try:
                    large, small = win32gui.ExtractIconEx(exe_path, icon_index)
                    if large:
                        icon_path = self._hicon_to_image(large[0], exe_path, f"extracticon_{icon_index}")
                        
                        for icon in large:
                            if icon: win32gui.DestroyIcon(icon)
                        if small:
                            for icon in small:
                                if icon: win32gui.DestroyIcon(icon)
                        
                        if icon_path:
                            return icon_path
                except Exception:
                    continue
                    
        except Exception:
            pass
        return None

    def _extract_from_registry(self, exe_path: str) -> Optional[str]:
        try:
            import winreg
            
            _, ext = os.path.splitext(exe_path)
            if not ext:
                ext = '.exe'
            
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as key:
                file_type = winreg.QueryValue(key, '')
                
            if file_type:
                icon_key = f"{file_type}\\DefaultIcon"
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, icon_key) as key:
                        icon_info = winreg.QueryValue(key, '')
                        if ',' in icon_info:
                            icon_file = icon_info.split(',')[0].strip('"')
                        else:
                            icon_file = icon_info.strip('"')
                        
                        if os.path.exists(icon_file):
                            return self._extract_with_extracticon(icon_file)
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def _hicon_to_image(self, hicon: int, exe_path: str, method: str) -> Optional[str]:
        try:
            ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
            ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
            
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            hdc = hdc.CreateCompatibleDC()
            
            hdc.SelectObject(hbmp)
            hdc.FillSolidRect((0, 0, ico_x, ico_y), 0xFFFFFF)
            hdc.DrawIcon((0, 0), hicon)
            
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer('RGBA', (ico_x, ico_y), bmpstr, 'raw', 'BGRA', 0, 1)
            
            icon_filename = f"icon_{hash(exe_path)}_{method}.png"
            icon_path = os.path.join(self.temp_dir, icon_filename)
            img.save(icon_path)
            
            return icon_path
            
        except Exception as e:
            print(f"Erro ao converter ícone: {e}")
        return None
    
    def get_app_info(self, app_key) -> Optional[AppInfo]:
        try:
            name = None
            path = None
            
            try:
                name = winreg.QueryValueEx(app_key, "DisplayName")[0]
            except:
                return None
                
            try:
                path = winreg.QueryValueEx(app_key, "DisplayIcon")[0]
                if not path.endswith('.exe'):
                    try:
                        install_location = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                        if install_location and os.path.exists(install_location):
                            for file in os.listdir(install_location):
                                if file.endswith('.exe'):
                                    path = os.path.join(install_location, file)
                                    break
                    except:
                        pass
            except:
                try:
                    install_location = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                    if install_location and os.path.exists(install_location):
                        for file in os.listdir(install_location):
                            if file.endswith('.exe'):
                                path = os.path.join(install_location, file)
                                break
                except:
                    return None
            
            if not name or not path:
                return None
                
            skip_names = ['uninstall', 'update', 'setup', 'install', 'redist', 'vcredist', 
                         'microsoft visual c++', 'directx', '.net framework']
            
            if any(skip in name.lower() for skip in skip_names):
                return None
                
            if ',' in path:
                path = path.split(',')[0].strip('"')
            
            icon_path = self.extract_icon(path)
            return AppInfo(name, path, icon_path)
            
        except Exception:
            return None
    
    def load_start_menu_apps(self):
        start_menu_paths = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs")
        ]
        
        for start_path in start_menu_paths:
            if os.path.exists(start_path):
                self.scan_directory_for_shortcuts(start_path)
    
    def scan_directory_for_shortcuts(self, directory):
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.lnk'):
                        shortcut_path = os.path.join(root, file)
                        app_info = self.resolve_shortcut(shortcut_path)
                        if app_info:
                            self.apps_cache.append(app_info)
        except Exception as e:
            print(f"Erro ao escanear {directory}: {e}")
    
    def resolve_shortcut(self, shortcut_path) -> Optional[AppInfo]:
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            
            target_path = shortcut.Targetpath
            name = os.path.splitext(os.path.basename(shortcut_path))[0]
            
            if target_path and target_path.endswith('.exe') and os.path.exists(target_path):
                icon_path = self.extract_icon(target_path)
                return AppInfo(name, target_path, icon_path)
                
        except Exception:
            name = os.path.splitext(os.path.basename(shortcut_path))[0]
            return AppInfo(name, shortcut_path, None)
            
        return None
    
    def search_files(self, query: str, max_results: int = 10) -> List[Union[FileInfo, 'FolderInfo']]:
        results = []
        search_paths = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
        ]
        
        for search_path in search_paths:
            if len(results) >= max_results:
                break
                
            try:
                for item in os.listdir(search_path):
                    if len(results) >= max_results:
                        break
                        
                    if query.lower() in item.lower():
                        full_path = os.path.join(search_path, item)
                        try:
                            if os.path.isdir(full_path):
                                results.append(FolderInfo(item, full_path))
                            else:
                                size = os.path.getsize(full_path)
                                results.append(FileInfo(item, full_path, size))
                        except:
                            continue
                
                for subdir in os.listdir(search_path):
                    if len(results) >= max_results:
                        break
                        
                    subdir_path = os.path.join(search_path, subdir)
                    if os.path.isdir(subdir_path):
                        try:
                            for item in os.listdir(subdir_path):
                                if len(results) >= max_results:
                                    break
                                    
                                if query.lower() in item.lower():
                                    full_path = os.path.join(subdir_path, item)
                                    try:
                                        if os.path.isdir(full_path):
                                            results.append(FolderInfo(item, full_path))
                                        else:
                                            size = os.path.getsize(full_path)
                                            results.append(FileInfo(item, full_path, size))
                                    except:
                                        continue
                        except:
                            continue
                            
            except PermissionError:
                continue
                
        return results
    
    def get_web_suggestions(self, query: str) -> List[WebInfo]:
        popular_sites = [
            ("Google", f"https://www.google.com/search?q={query}"),
            ("YouTube", f"https://www.youtube.com/results?search_query={query}"),
            ("Wikipedia", f"https://en.wikipedia.org/wiki/{query}"),
            ("GitHub", f"https://github.com/search?q={query}"),
            ("Stack Overflow", f"https://stackoverflow.com/search?q={query}"),
        ]
        
        return [WebInfo(name, url) for name, url in popular_sites]

    def evaluate_math(self, expression: str) -> Optional[MathInfo]:
        try:
            expression = expression.strip()
            allowed_functions = {
                'sqrt', 'log', 'log10', 'log2', 'ln',
                'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh',
                'exp', 'pow', 'abs', 'ceil', 'floor', 'round',
                'degrees', 'radians'
            }
            allowed_chars = set('0123456789+-*/.()^, ')
            temp_expr = expression.lower()
            for func in allowed_functions:
                temp_expr = temp_expr.replace(func, '')
            
            if not all(c in allowed_chars for c in temp_expr):
                return None
            
            function_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            functions_found = re.findall(function_pattern, expression.lower())
            
            for func in functions_found:
                if func not in allowed_functions:
                    return None
            
            safe_dict = {
                "__builtins__": {},
                "sqrt": math.sqrt,
                "log": math.log,
                "log10": math.log10,
                "log2": math.log2,
                "ln": math.log,  
                "exp": math.exp,
                "pow": math.pow,
                "abs": abs,
                "round": round,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "ceil": math.ceil,
                "floor": math.floor,
                "degrees": math.degrees,
                "radians": math.radians,
                "pi": math.pi,
                "e": math.e,
            }
            
            expression = expression.replace('^', '**')
            
            result = eval(expression, safe_dict, {})
            
            if isinstance(result, float):
                if result.is_integer():
                    result_str = str(int(result))
                else:
                    result_str = f"{result:.10g}"
            else:
                result_str = str(result)
            
            return MathInfo(expression, result_str)
            
        except ZeroDivisionError:
            return None  
        except ValueError:
            return None  
        except OverflowError:
            return None  
        except:
            return None
        
    def cleanup(self):
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass