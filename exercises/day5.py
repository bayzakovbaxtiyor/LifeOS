import json

profil = {
    "ism": "Baxtiyor",
    "maqsad": "AI Agent",
    "progress": "12/21",
}

with open("profil.json", "w", encoding="utf-8") as fayl:
    json.dump(profil, fayl, ensure_ascii=False, indent=4)

with open("profil.json", "r", encoding="utf-8") as fayl:
    oqilgan_profil = json.load(fayl)
    print(oqilgan_profil)