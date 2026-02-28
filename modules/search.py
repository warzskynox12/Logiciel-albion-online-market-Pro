import customtkinter as ctk
import threading
import difflib

class SearchPage(ctk.CTkFrame):
    def __init__(self, master, logic, **kwargs):
        super().__init__(master, **kwargs)
        self.logic = logic
        
        # --- LES 16 CATÉGORIES EXACTES DE TON IMAGE ---
        self.categories = {
            "Armes": ["Arc", "Arbalète", "Dague", "Gants de guerre", "Hache", "Lance", "Masse", "Marteau", "Bâton éthéré", "Bâton de feu", "Bâton de glace", "Bâton de nature", "Bâton maudit", "Bâton sacré", "Épée", "Bâton de Changeforme"],
            "Armure de Poitrine": ["Tissu", "Cuir", "Plaque"],
            "Armure de Tête": ["Tissu", "Cuir", "Plaque"],
            "Armure de Pieds": ["Tissu", "Cuir", "Plaque"],
            "Armes Secondaires": ["Bouclier", "Livre", "Torche"],
            "Capes": ["Cape normale", "Cape de faction"],
            "Sacs": ["Sac", "Sac de récolte"],
            "Monture": ["Cheval", "Boeuf", "Sanglier", "Loup", "Ours", "Bélier", "Moa"],
            "Consommable": ["Plat", "Potion"],
            "Équipement de Récolte": ["Pioche", "Hache", "Faucille", "Couteau", "Masse"],
            "Fabrication": ["Outil", "Matériau"],
            "Artefact": ["Arme", "Armure", "Accessoire"],
            "Agriculture": ["Graine", "Animal", "Plante"],
            "Mobilier": ["Coffre", "Table", "Chaise"],
            "Cosmétique": ["Apparence"],
            "Autre": ["Jeton", "Luxe", "Livre"]
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- BARRE DE RECHERCHE ---
        self.search_bar = ctk.CTkFrame(self, fg_color="#1a1a1a", height=80)
        self.search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # 1. Catégorie principale (Les 16 de l'image)
        self.cat_var = ctk.StringVar(value="Tout")
        self.cat_menu = ctk.CTkOptionMenu(self.search_bar, values=list(self.categories.keys()), 
                                         command=self.update_sub_categories, width=170)
        self.cat_menu.pack(side="left", padx=10, pady=20)

        # 2. Sous-catégorie (Type)
        self.sub_cat_var = ctk.StringVar(value="Tout")
        self.sub_cat_menu = ctk.CTkOptionMenu(self.search_bar, values=["Tout"], 
                                              variable=self.sub_cat_var, width=150)
        self.sub_cat_menu.pack(side="left", padx=5)

        # 3. Niveau (Tier 1-8)
        self.tier_var = ctk.StringVar(value="Niveau 8")
        self.tier_menu = ctk.CTkOptionMenu(self.search_bar, values=[f"Niveau {i}" for i in range(1, 9)], 
                                          variable=self.tier_var, width=110)
        self.tier_menu.pack(side="left", padx=5)

        # 4. Enchantement (.0 à .4)
        self.ench_var = ctk.StringVar(value="Enchantement .0")
        self.ench_menu = ctk.CTkOptionMenu(self.search_bar, values=[f"Enchantement .{i}" for i in range(5)], 
                                          variable=self.ench_var, width=140)
        self.ench_menu.pack(side="left", padx=5)

        # Bouton RECHERCHER
        self.btn_search = ctk.CTkButton(self.search_bar, text="RECHERCHER", command=self.start_manual_search, 
                                        fg_color="#2eb82e", font=("Arial", 12, "bold"), width=120)
        self.btn_search.pack(side="right", padx=15)

        # --- ZONE DE RÉSULTATS ---
        self.results_scroll = ctk.CTkScrollableFrame(self, fg_color="#0f0f0f")
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    def update_sub_categories(self, choice):
        """Met à jour les types dynamiquement"""
        new_values = ["Tout"] + self.categories.get(choice, [])
        self.sub_cat_menu.configure(values=new_values)
        self.sub_cat_var.set("Tout")

    def start_manual_search(self):
        """Lancement de la requête API"""
        keyword = self.sub_cat_var.get()
        if keyword == "Tout": 
            keyword = self.cat_var.get()
        
        for w in self.results_scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.results_scroll, text="📡 Accès au Marché d'Albion...", font=("Arial", 14)).pack(pady=40)
        
        threading.Thread(target=self.perform_search, args=(keyword,), daemon=True).start()

    def perform_search(self, keyword):
        """Conversion ID et requête"""
        matches = [name for name in self.logic.noms_connus if keyword.lower() in name.lower()]
        
        if not matches:
            self.after(0, lambda: self.show_error(f"Aucun item '{keyword}' trouvé."))
            return

        nom_trouve = matches[0]
        base_id = self.logic.dict_items[nom_trouve].split('@')[0]
        
        # Adaptation Tier (T1-T8)
        tier_num = self.tier_var.get().split()[-1]
        final_id = base_id
        if final_id.startswith("T"):
            final_id = f"T{tier_num}" + final_id[2:]
            
        # Adaptation Enchantement
        enchant = self.ench_var.get().split('.')[-1]
        if enchant != "0":
            final_id = f"{final_id}@{enchant}"

        data = self.logic.fetch_prices(final_id)
        self.after(0, lambda: self.display_results(nom_trouve, final_id, data))

    def display_results(self, nom, item_id, data):
        """Affichage identique au scanner"""
        for w in self.results_scroll.winfo_children(): w.destroy()
        
        display_name = f"{nom} ({self.tier_var.get()}{self.ench_var.get()})"
        ctk.CTkLabel(self.results_scroll, text=display_name.upper(), font=("Impact", 22), text_color="#3b8ed0").pack(pady=15)

        if data:
            for q in range(1, 6):
                q_data = [p for p in data if p['quality'] == q]
                if not q_data: continue

                q_name = self.logic.quality_names.get(q, f"Qualité {q}")
                sep = ctk.CTkFrame(self.results_scroll, fg_color="#1a1a1a", height=30)
                sep.pack(fill="x", pady=(15, 0))
                ctk.CTkLabel(sep, text=q_name.upper(), font=("Arial", 12, "bold"), text_color="#2eb82e").pack()

                grid = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
                grid.pack(fill="x", pady=5)
                grid.columnconfigure((0, 1, 2), weight=1)

                for i, p in enumerate(q_data):
                    card = ctk.CTkFrame(grid, fg_color="#181818", border_width=1, border_color="#333")
                    card.grid(row=i//3, column=i%3, padx=3, pady=3, sticky="nsew")
                    
                    city = p['city'].replace("Fort Sterling", "F. Sterling")
                    ctk.CTkLabel(card, text=city.upper(), font=("Arial", 10), text_color="#888").pack(pady=2)
                    
                    val = f"{p['sell_price_min']:,}".replace(",", " ")
                    ctk.CTkLabel(card, text=val, font=("Consolas", 16, "bold"), text_color="#4CAF50").pack(pady=5)
        else:
            self.show_error(f"Aucune donnée pour {item_id}.")

    def show_error(self, msg):
        for w in self.results_scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.results_scroll, text=msg, text_color="#cc3333", font=("Arial", 14, "bold")).pack(pady=100)