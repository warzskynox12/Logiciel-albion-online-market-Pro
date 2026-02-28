import customtkinter as ctk
import threading, time, keyboard
from logic import AlbionLogic
from modules.scanner import ScannerPage
from modules.archives import ArchivePage
from modules.search import SearchPage # Import de la nouvelle page

class AlbionUltimateERP(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialisation de la logique
        self.logic = AlbionLogic()
        
        # Configuration de la fenêtre
        self.title("ALBION SCANNER PRO")
        self.geometry("1200x800")
        self.after(0, lambda: self.state('zoomed'))
        
        # Système d'onglets
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Création des onglets
        self.tab_scan = self.tabs.add("📊 SCANNER")
        self.tab_search = self.tabs.add("🔍 RECHERCHE MANUELLE")
        self.tab_arch = self.tabs.add("📂 ARCHIVES")

        # Page Archives
        self.archive_page = ArchivePage(self.tab_arch, self.logic, "archives.json")
        self.archive_page.pack(fill="both", expand=True)

        # Page Scanner (on lui passe la fonction d'archivage)
        self.scanner_page = ScannerPage(self.tab_scan, self.logic, self.archive_page.add_archive_manually)
        self.scanner_page.pack(fill="both", expand=True)
        
        # Page Recherche Manuelle
        self.search_page = SearchPage(self.tab_search, self.logic)
        self.search_page.pack(fill="both", expand=True)

        # Configuration du raccourci clavier
        keyboard.add_hotkey('f8', self.trigger)

    def trigger(self):
        """Lance le scan dans un thread séparé pour ne pas geler l'interface"""
        threading.Thread(target=self.work, daemon=True).start()

    def work(self):
        """Logique de traitement du scan"""
        time.sleep(0.1) # Petit délai pour éviter les conflits de capture
        
        # Capture et analyse via logic.py
        nom, item_id, enchant = self.logic.capture_and_process()
        
        # Récupération des prix via l'API
        data = self.logic.fetch_prices(item_id)
        
        # Mise à jour de l'interface sur le thread principal
        self.after(0, lambda: self.scanner_page.update_scanner(nom, item_id, enchant, data))

if __name__ == "__main__":
    # Paramètres de thème
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = AlbionUltimateERP()
    app.mainloop()