import sys
import os
from PyQt6.QtCore import QObject, pyqtSlot
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