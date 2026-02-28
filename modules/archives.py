import customtkinter as ctk
import json, os, threading

class ArchivePage(ctk.CTkFrame):
    def __init__(self, master, logic, save_file, **kwargs):
        super().__init__(master, **kwargs)
        self.logic = logic
        self.save_file = save_file
        
        ctk.CTkLabel(self, text="📂 ARCHIVES COMPLÈTES", font=("Impact", 24), text_color="#2eb82e").pack(pady=10)
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.load()

    def render_price_grid(self, container, data):
        """Grille identique au scanner principal pour les archives"""
        for q in range(1, 6):
            q_data = [p for p in data if p['quality'] == q]
            if not q_data: continue

            q_name = self.logic.quality_names.get(q, f"Qualité {q}")
            sep = ctk.CTkFrame(container, fg_color="#1a1a1a", height=25)
            sep.pack(fill="x", pady=(10, 0))
            ctk.CTkLabel(sep, text=q_name.upper(), font=("Arial", 11, "bold"), text_color="#2eb82e").pack()

            grid = ctk.CTkFrame(container, fg_color="transparent")
            grid.pack(fill="x", pady=5)
            grid.columnconfigure((0, 1, 2), weight=1)

            for i, p in enumerate(q_data):
                card = ctk.CTkFrame(grid, fg_color="#181818", border_width=1, border_color="#333")
                card.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="nsew")
                
                city = p['city'].replace("Fort Sterling", "F. Sterling")
                ctk.CTkLabel(card, text=city.upper(), font=("Arial", 9), text_color="#888").pack()
                
                price = f"{p['sell_price_min']:,}".replace(",", " ")
                ctk.CTkLabel(card, text=price, font=("Consolas", 13, "bold"), text_color="#4CAF50").pack()

    def add_entry(self, nom, enchant, item_id):
        f = ctk.CTkFrame(self.list_frame, fg_color="#1e1e1e")
        f.pack(fill="x", pady=2, padx=5)
        f.item_data = {"nom": nom, "enchant": enchant, "id": item_id}
        f.is_open = False

        header = ctk.CTkFrame(f, fg_color="transparent")
        header.pack(fill="x")

        txt = f"▶ {nom} (.{enchant})" if enchant > 0 else f"▶ {nom}"
        btn = ctk.CTkButton(header, text=txt, font=("Arial", 12, "bold"), anchor="w", fg_color="transparent", hover_color="#2b2b2b")
        btn.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(header, text="❌", width=30, fg_color="#552222", command=lambda: [f.destroy(), self.save()]).pack(side="right", padx=10)

        f.details = ctk.CTkFrame(f, fg_color="#0f0f0f")
        btn.configure(command=lambda: self.toggle_archive(f, item_id, btn, txt))

    def toggle_archive(self, frame, item_id, btn, txt):
        if not frame.is_open:
            frame.is_open = True
            btn.configure(text=txt.replace("▶", "▼"), text_color="#2eb82e")
            frame.details.pack(fill="x", padx=10, pady=5)
            for w in frame.details.winfo_children(): w.destroy()
            ctk.CTkLabel(frame.details, text="Chargement API...").pack()
            threading.Thread(target=self.api_thread, args=(frame, item_id), daemon=True).start()
        else:
            frame.is_open = False
            btn.configure(text=txt.replace("▼", "▶"), text_color="white")
            frame.details.pack_forget()

    def api_thread(self, frame, item_id):
        data = self.logic.fetch_prices(item_id)
        self.after(0, lambda: self.draw_prices(frame, data))

    def draw_prices(self, frame, data):
        for w in frame.details.winfo_children(): w.destroy()
        if data: self.render_price_grid(frame.details, data)
        else: ctk.CTkLabel(frame.details, text="Erreur API").pack()

    def add_archive_manually(self, card_src, nom, enchant, item_id):
        """Vérifie les doublons avant d'ajouter l'item aux archives"""
        
        # 1. On vérifie si l'item_id existe déjà dans les archives actuelles
        deja_present = False
        for card in self.list_frame.winfo_children():
            if hasattr(card, "item_data"):
                if card.item_data["id"] == item_id:
                    deja_present = True
                    break
        
        if deja_present:
            print(f"⚠️ [ARCHIVE] L'item {nom} (ID: {item_id}) est déjà dans les archives. Annulation.")
            # Optionnel : On détruit quand même la carte du scanner pour nettoyer
            if card_src: card_src.destroy()
            return # On sort de la fonction sans ajouter le doublon

        # 2. Si c'est un nouvel item, on procède normalement
        print(f"📥 [ARCHIVE] Nouvel item détecté : {nom}. Archivage en cours...")
        if card_src: 
            card_src.destroy()
            
        self.add_entry(nom, enchant, item_id)
        self.save()

    def save(self):
        self.after(100, self._do_save)

    def _do_save(self):
        data = [c.item_data for c in self.list_frame.winfo_children() if hasattr(c, "item_data")]
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self):
        if os.path.exists(self.save_file):
            with open(self.save_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    self.add_entry(item['nom'], item['enchant'], item['id'])