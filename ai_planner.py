import concurrent.futures
import json
import os
from dotenv import load_dotenv
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TASKS_FILE = os.path.join(BASE_DIR, "data", "tasks.json")
PROFIL_FILE = os.path.join(BASE_DIR, "data", "profil.json")
PLAN_FILE = os.path.join(BASE_DIR, "data", "daily_plan.txt")

# API kalitingizda tasdiqlangan ishchi modellar ro'yxati
MODELLAR = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


def json_oqish(fayl_yoli, standart_qiymat):
    if not os.path.exists(fayl_yoli):
        return standart_qiymat
    with open(fayl_yoli, "r", encoding="utf-8") as f:
        return json.load(f)


def sorov_yuborish(client, model_nomi, prompt, kutish_vaqti=20):
    def _chaqiruv():
        return client.models.generate_content(
            model=model_nomi,
            contents=prompt,
        )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_chaqiruv)
    try:
        return future.result(timeout=kutish_vaqti)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def kunlik_reja_tuzish():
    api_kalit = os.getenv("LLM_API_KEY", "").strip()
    if not api_kalit:
        print("Xato: .env faylida LLM_API_KEY topilmadi!")
        return

    vazifalar = json_oqish(TASKS_FILE, [])
    profil = json_oqish(PROFIL_FILE, {"ism": "Baxtiyor"})

    bajarilmaganlar = [v for v in vazifalar if not v.get("bajarildi", False)]
    if not bajarilmaganlar:
        print("Barcha vazifalar bajarilgan! Avval task_manager.py orqali yangi vazifa qo'shing.")
        return

    prompt = f"""
Sen LifeOS (BAXZAKOV-OS-2026-2027) tizimining shaxsiy AI rejalashtiruvchi agentisan.
Foydalanuvchi profili: {json.dumps(profil, ensure_ascii=False)}
Bajarilmagan vazifalar ro'yxati: {json.dumps(bajarilmaganlar, ensure_ascii=False)}

Tizim qoidalari:
1. Daily Planning: Ro'yxatdan bugun uchun ENG MUHIM 3 TA vazifani (Top-3 MIT) tanla va sababini qisqa izohla.
2. Time Blocking: Tanlangan 3 ta vazifa uchun aniq vaqt bloklari (masalan, 09:00-10:30) bilan kunlik jadval tuz.
3. Trading bo'yicha hech qanday moliyaviy yoki real savdo tavsiyasi berma, faqat o'quv/tahlil intizomini qo'lla.
4. Javobni o'zbek tilida, aniq, qisqa va amaliy ko'rinishda ber.
"""

    client = genai.Client(api_key=api_kalit, http_options={"timeout": 20000})
    print("LifeOS AI Planner vazifalarni tahlil qilmoqda...\n")

    for indeks, model_nomi in enumerate(MODELLAR, start=1):
        print(f"[{indeks}/{len(MODELLAR)}] Ulanmoqda: {model_nomi}...")
        try:
            javob = sorov_yuborish(client, model_nomi, prompt, kutish_vaqti=20)
            natija = javob.text
            with open(PLAN_FILE, "w", encoding="utf-8") as f:
                f.write(natija)

            print(f"\n=== LIFEOS KUNLIK AI REJA ({model_nomi}) ===")
            print(natija)
            print(f"\nReja saqlandi: {PLAN_FILE}")
            return
        except concurrent.futures.TimeoutError:
            print(f"[{model_nomi}] 20 soniyada javob bermadi. Keyingi modelga o'tilmoqda...")
        except Exception as xato:
            print(f"[{model_nomi}] O'tkazib yuborildi: {str(xato)[:120]}")

    print("\nBarcha modellar hozircha band. 1 daqiqadan so'ng qayta urinib ko'ring.")


if __name__ == "__main__":
    kunlik_reja_tuzish()