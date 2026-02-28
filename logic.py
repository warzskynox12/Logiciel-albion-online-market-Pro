import pytesseract
import mss
from PIL import Image, ImageEnhance
import numpy as np
import difflib
import requests
import json
import os
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class AlbionLogic:
    def __init__(self):
        self.cities = ["Caerleon", "Bridgewatch", "Martlock", "Lymhurst", "Thetford", "Fort Sterling", "Brecilien"]
        self.quality_names = {1: "Normale", 2: "Acceptable", 3: "Admirable", 4: "Formidable", 5: "Exceptionnelle"}
        self.dict_items = {}
        self.noms_connus = []
        self.target_w = 599
        self.target_h = 594
        
        if os.path.exists("dictionnaire_items.json"):
            with open("dictionnaire_items.json", "r", encoding="utf-8") as f:
                self.dict_items = json.load(f)
                self.noms_connus = list(self.dict_items.keys())

    def analyser_enchantement(self, img_item):
        """Analyse haute précision (Seuil 250 pixels)"""
        w, h = img_item.size
        zone = img_item.crop((35, h - 85, 250, h - 5))
        hsv = np.array(zone.convert('HSV'))
        H, S, V = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]

        mask4 = ((H < 35) | (H > 240)) & (S > 180) & (V > 150)
        mask3 = (H >= 170) & (H <= 220) & (S > 100) & (V > 80)
        mask2 = (H >= 120) & (H <= 165) & (S > 100) & (V > 100)
        mask1 = (H >= 45) & (H <= 95) & (S > 80) & (V > 100)

        p4, p3, p2, p1 = np.sum(mask4), np.sum(mask3), np.sum(mask2), np.sum(mask1)
        seuil = 250 

        if p4 > seuil: return 4
        if p3 > seuil: return 3
        if p2 > seuil: return 2
        if p1 > seuil: return 1
        return 0

    def capture_and_process(self):
        with mss.mss() as sct:
            img_full = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", img_full.size, img_full.bgra, "raw", "BGRX")
            
            left = (img.width - self.target_w) // 2
            top = (img.height - self.target_h) // 2
            img_item = img.crop((left, top, left + self.target_w, top + self.target_h))

            enhancer = ImageEnhance.Contrast(img_item.convert('L'))
            img_ocr = enhancer.enhance(2.5).point(lambda x: 0 if x < 190 else 255, '1')
            
            texte = pytesseract.image_to_string(img_ocr, lang='fra+eng')
            nom_f, id_f, enchant = "Inconnu", "Inconnu", 0
            
            lines = [re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', l).strip() for l in texte.split('\n') if len(l.strip()) > 3]
            for line in lines:
                match = difflib.get_close_matches(line, self.noms_connus, n=1, cutoff=0.6)
                if match:
                    nom_f = match[0]
                    # On récupère l'ID de base et on enlève TOUT ce qui suit un '@' déjà présent
                    base_id = self.dict_items[nom_f].split('@')[0]
                    
                    # --- FILTRE EXCLUSION : Montures et Consommables ---
                    mots_sans_ench = ["Sanglier", "Cheval", "Boeuf", "Sac", "Mouton", "Ours", "Loup", "Bélier", "Ragoût", "Soupe", "Omelette", "Sandwich", "Potion"]
                    
                    if any(mot.lower() in nom_f.lower() for mot in mots_sans_ench):
                        enchant = 0
                    else:
                        enchant = self.analyser_enchantement(img_item)
                    
                    # Reconstruction propre de l'ID
                    id_f = f"{base_id}@{enchant}" if enchant > 0 else base_id
                    break
            
            return nom_f, id_f, enchant

    def fetch_prices(self, item_id):
        if item_id == "Inconnu": return None
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{item_id}?locations={','.join(self.cities)}"
        try:
            r = requests.get(url, timeout=5)
            return [p for p in r.json() if p['sell_price_min'] > 0]
        except: return None