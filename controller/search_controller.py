import os
import subprocess
import webbrowser
from typing import List, Union
from model.launcher_model import AppModel, AppInfo, FileInfo, WebInfo, CommandInfo, MathInfo, FolderInfo

class SearchController:
    def __init__(self, model: AppModel):
        self.model = model
        
    def search(self, query: str) -> List[Union[AppInfo, FileInfo, WebInfo, CommandInfo, MathInfo]]:
        if not query:
            return self.model.apps_cache[:20]
            
        if query.startswith('.'):
            return self.search_apps(query[1:])
        elif query.startswith('?'):
            return self.search_files(query[1:])
        elif query.startswith('/'):
            return self.search_web(query[1:])
        elif query.startswith('!'):
            return self.create_command(query[1:])
        else:
            math_result = self.model.evaluate_math(query)
            if math_result:
                return [math_result]
            
            return self.search_apps(query)
    
    def search_apps(self, query: str) -> List[AppInfo]:
        if not query.strip():
            return self.model.apps_cache[:20]
            
        results = []
        query_lower = query.lower()
        
        for app in self.model.apps_cache:
            if query_lower in app.name.lower():
                results.append(app)
                
        return sorted(results, key=lambda x: x.name.lower())[:15]
    
    def search_files(self, query: str) -> List[Union[FileInfo, FolderInfo]]:
        if not query.strip():
            return []
            
        return self.model.search_files(query.strip(), max_results=8)  # Limitar ainda mais
    
    def search_web(self, query: str) -> List[WebInfo]:
        if not query.strip():
            return []
            
        return self.model.get_web_suggestions(query.strip())
    
    def create_command(self, command: str) -> List[CommandInfo]:
        if not command.strip():
            return []
            
        return [CommandInfo(f"Executar: {command}", command.strip())]
    
    def execute_item(self, item: Union[AppInfo, FileInfo, WebInfo, CommandInfo, MathInfo, FolderInfo]):
        try:
            if isinstance(item, AppInfo):
                self.launch_app(item.path)
            elif isinstance(item, FileInfo):
                self.open_file(item.path)
            elif isinstance(item, FolderInfo):
                self.open_folder(item.path)
            elif isinstance(item, WebInfo):
                self.open_website(item.url)
            elif isinstance(item, CommandInfo):
                self.execute_command(item.command)
            elif isinstance(item, MathInfo):
                self.copy_to_clipboard(item.result)
        except Exception as e:
            print(f"Erro ao executar item: {e}")
            
    def open_folder(self, folder_path: str):
        try:
            os.startfile(folder_path)
        except Exception as e:
            print(f"Erro ao abrir pasta {folder_path}: {e}")
    
    def launch_app(self, app_path: str):
        try:
            if app_path.startswith("ms-"):
                os.startfile(app_path)
            elif app_path.endswith('.lnk'):
                os.startfile(app_path)
            else:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_NORMAL
                
                subprocess.Popen(
                    app_path,
                    shell=False,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo
                )
        except Exception as e:
            try:
                os.startfile(app_path)
            except Exception as e2:
                print(f"Erro ao executar {app_path}: {e2}")
    
    def open_file(self, file_path: str):
        try:
            os.startfile(file_path)
        except Exception as e:
            print(f"Erro ao abrir arquivo {file_path}: {e}")
    
    def open_website(self, url: str):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Erro ao abrir website {url}: {e}")
    
    def execute_command(self, command: str):
        try:
            subprocess.Popen(
                f'start cmd /k "{command}"',
                shell=True
            )
        except Exception as e:
            print(f"Erro ao executar comando {command}: {e}")
    
    def copy_to_clipboard(self, text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"Resultado copiado para clipboard: {text}")
        except ImportError:
            print(f"Resultado: {text} (instale pyperclip para copiar automaticamente)")
        except Exception as e:
            print(f"Erro ao copiar para clipboard: {e}")