import customtkinter as ctk
import threading

class ScannerPage(ctk.CTkFrame):
    def __init__(self, master, logic, archive_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.logic = logic
        self.archive_callback = archive_callback
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # GAUCHE : Affichage Live
        self.main_container = ctk.CTkFrame(self, fg_color="#101010")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.title_lbl = ctk.CTkLabel(self.main_container, text="SCANNER PRÊT (F8)", font=("Impact", 35), text_color="#3b8ed0")
        self.title_lbl.pack(pady=20)

        self.results_scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.results_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # DROITE : Historique
        self.side_panel = ctk.CTkFrame(self, fg_color="#0a0a0a")
        self.side_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.side_panel, text="HISTORIQUE", font=("Impact", 20)).pack(pady=10)
        
        self.history_scroll = ctk.CTkScrollableFrame(self.side_panel, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True)

    def render_price_grid(self, container, data, is_compact=False):
        """Fonction universelle pour afficher la grille des prix (Villes + Qualités)"""
        for q in range(1, 6):
            q_data = [p for p in data if p['quality'] == q]
            if not q_data: continue

            q_name = self.logic.quality_names.get(q, f"Qualité {q}")
            font_size = 10 if is_compact else 12
            
            sep = ctk.CTkFrame(container, fg_color="#1a1a1a", height=25)
            sep.pack(fill="x", pady=(10, 0))
            ctk.CTkLabel(sep, text=q_name.upper(), font=("Arial", font_size, "bold"), text_color="#3b8ed0").pack()

            grid = ctk.CTkFrame(container, fg_color="transparent")
            grid.pack(fill="x", pady=5)
            # 2 colonnes pour l'historique (compact), 3 pour le principal
            cols = 2 if is_compact else 3
            grid.columnconfigure(list(range(cols)), weight=1)

            for i, p in enumerate(q_data):
                card = ctk.CTkFrame(grid, fg_color="#181818", border_width=1, border_color="#333")
                card.grid(row=i//cols, column=i%cols, padx=2, pady=2, sticky="nsew")
                
                city = p['city'].replace("Fort Sterling", "F. Sterling")
                ctk.CTkLabel(card, text=city.upper(), font=("Arial", 8 if is_compact else 9), text_color="#888").pack()
                
                price = f"{p['sell_price_min']:,}".replace(",", " ")
                ctk.CTkLabel(card, text=price, font=("Consolas", 11 if is_compact else 14, "bold"), text_color="#4CAF50").pack()

    def update_scanner(self, nom, item_id, enchant, data):
        status_text = f"{nom} (.{enchant})" if enchant > 0 else nom
        self.title_lbl.configure(text=status_text.upper())
        for w in self.results_scroll.winfo_children(): w.destroy()

        if data:
            self.render_price_grid(self.results_scroll, data)
        else:
            ctk.CTkLabel(self.results_scroll, text="⚠️ AUCUNE DONNÉE API").pack(pady=20)

        self.add_to_history(nom, enchant, item_id)

    def add_to_history(self, nom, enchant, item_id):
        h_item = ctk.CTkFrame(self.history_scroll, fg_color="#1a1a1a")
        h_item.pack(fill="x", pady=2, padx=5)
        
        header = ctk.CTkFrame(h_item, fg_color="transparent")
        header.pack(fill="x")

        display_txt = f"▶ {nom} (.{enchant})" if enchant > 0 else f"▶ {nom}"
        btn_toggle = ctk.CTkButton(header, text=display_txt, font=("Arial", 10), anchor="w", fg_color="transparent", hover_color="#2b2b2b")
        btn_toggle.pack(side="left", fill="x", expand=True)

        h_item.details = ctk.CTkFrame(h_item, fg_color="#0f0f0f")
        h_item.is_open = False
        
        btn_toggle.configure(command=lambda: self.toggle_history(h_item, item_id, btn_toggle, display_txt))
        ctk.CTkButton(header, text="📁", width=25, command=lambda: self.archive_callback(h_item, nom, enchant, item_id)).pack(side="right", padx=2)

    def toggle_history(self, card, item_id, btn, txt):
        if not card.is_open:
            card.is_open = True
            btn.configure(text=txt.replace("▶", "▼"))
            card.details.pack(fill="x", padx=2, pady=2)
            for w in card.details.winfo_children(): w.destroy()
            ctk.CTkLabel(card.details, text="API...").pack()
            threading.Thread(target=self.api_thread, args=(card, item_id, True), daemon=True).start()
        else:
            card.is_open = False
            btn.configure(text=txt.replace("▼", "▶"))
            card.details.pack_forget()

    def api_thread(self, card, item_id, is_compact):
        data = self.logic.fetch_prices(item_id)
        self.after(0, lambda: self.finish_render(card, data, is_compact))

    def finish_render(self, card, data, is_compact):
        for w in card.details.winfo_children(): w.destroy()
        if data: self.render_price_grid(card.details, data, is_compact)
        else: ctk.CTkLabel(card.details, text="Erreur API").pack()