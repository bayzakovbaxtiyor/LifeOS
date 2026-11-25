import json
import logging
import os

import httpx2
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from task_manager import vazifalarni_yuklash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

PROFIL_FILE = os.path.join(BASE_DIR, "data", "profil.json")
PLAN_FILE = os.path.join(BASE_DIR, "data", "daily_plan.txt")
MODEL_NOMI = "gemini-3.5-flash"
SOROV_VAQTI_MS = 20_000

logger = logging.getLogger("lifeos.ai_planner")


def profilni_yuklash():
    if not os.path.exists(PROFIL_FILE):
        return {"ism": "Baxtiyor"}
    try:
        with open(PROFIL_FILE, "r", encoding="utf-8") as fayl:
            return json.load(fayl)
    except (OSError, json.JSONDecodeError):
        logger.warning("Profil faylini o'qib bo'lmadi; standart profil ishlatiladi.")
        return {"ism": "Baxtiyor"}


def rejani_atomik_saqlash(matn):
    vaqtinchalik_fayl = PLAN_FILE + ".tmp"
    try:
        with open(vaqtinchalik_fayl, "w", encoding="utf-8") as fayl:
            fayl.write(matn)
            fayl.flush()
            os.fsync(fayl.fileno())
        os.replace(vaqtinchalik_fayl, PLAN_FILE)
    finally:
        if os.path.exists(vaqtinchalik_fayl):
            os.remove(vaqtinchalik_fayl)


def xatoni_aniqlash(xato):
    if isinstance(xato, errors.APIError):
        kod = xato.code
        if kod in (401, 403):
            return "autentifikatsiya", kod, "Gemini API kalitini tekshiring."
        if kod == 429:
            return "kvota", kod, "AI xizmati so'rovlar chegarasiga yetdi. Birozdan keyin yana urinib ko'ring."
        if 500 <= kod <= 599:
            return "server", kod, "AI xizmati vaqtincha ishlamayapti. Birozdan keyin yana urinib ko'ring."
        if kod == 404:
            return "model", kod, "AI modeli topilmadi yoki foydalanish mumkin emas. Model sozlamasini tekshiring."
        return "api", kod, "AI so'rovini bajarib bo'lmadi. Sozlamalarni tekshiring."

    if isinstance(xato, (httpx2.TimeoutException, TimeoutError)):
        return "vaqt_tugadi", "noma'lum", "AI javobi 20 soniya ichida kelmadi. Birozdan keyin qayta urinib ko'ring."
    if isinstance(xato, httpx2.RequestError):
        return "tarmoq", "noma'lum", "Internet yoki AI xizmatiga ulanishda muammo bor. Ulanishni tekshirib, qayta urinib ko'ring."
    return "noma'lum", "noma'lum", "Kutilmagan xato yuz berdi. Birozdan keyin qayta urinib ko'ring."


def kunlik_reja_tuzish():
    api_kalit = os.getenv("LLM_API_KEY", "").strip()
    if not api_kalit:
        return "AI reja tuzilmadi: .env faylida LLM_API_KEY sozlanmagan."

    try:
        vazifalar = vazifalarni_yuklash()
    except (OSError, json.JSONDecodeError):
        logger.warning("Vazifalar faylini o'qib bo'lmadi.")
        return "Vazifalar faylini o'qib bo'lmadi. Fayl mazmunini tekshiring."

    bajarilmaganlar = [v for v in vazifalar if not v.get("bajarildi", False)]
    if not bajarilmaganlar:
        return "Hozir bajarilmagan vazifalar yo'q. Yangi vazifa qo'shish uchun /add buyrug'idan foydalaning."

    profil = profilni_yuklash()
    prompt = f"""
Sen LifeOS shaxsiy rejalashtiruvchi yordamchisisan.
Foydalanuvchi profili: {json.dumps(profil, ensure_ascii=False)}
Bajarilmagan vazifalar: {json.dumps(bajarilmaganlar, ensure_ascii=False)}

Qoidalar:
1. Bugun uchun eng muhim uchta vazifani tanla va sababini qisqa yoz.
2. Uchtasiga vaqt oralig'i bilan kunlik jadval tuz.
3. Haqiqiy pul bilan savdo bo'yicha moliyaviy tavsiya berma; faqat o'quv va tahlil intizomini eslat.
4. O'zbek lotin yozuvida, Telegram uchun qulay va aniq javob ber.
"""

    client = None
    try:
        qayta_urinish = types.HttpRetryOptions(
            attempts=2,
            initial_delay=0.5,
            max_delay=1.0,
            jitter=0.0,
            http_status_codes=[408, 429, 500, 502, 503, 504],
        )
        client = genai.Client(
            api_key=api_kalit,
            http_options=types.HttpOptions(
                timeout=SOROV_VAQTI_MS,
                retry_options=qayta_urinish,
            ),
        )
        javob = client.models.generate_content(model=MODEL_NOMI, contents=prompt)
        natija = (javob.text or "").strip()
        if not natija:
            logger.warning("AI bo'sh javob qaytardi.")
            return "AI bo'sh javob qaytardi. Birozdan keyin /plan buyrug'ini qayta yuboring."

        rejani_atomik_saqlash(natija)
        return f"=== LIFEOS KUNLIK REJASI ===\n\n{natija}"
    except Exception as xato:
        toifa, kod, foydalanuvchi_xabari = xatoni_aniqlash(xato)
        logger.warning(
            "AI so'rovi bajarilmadi: toifa=%s, kod=%s, xato_turi=%s",
            toifa,
            kod,
            type(xato).__name__,
        )
        return foydalanuvchi_xabari
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as xato:
                logger.warning("AI mijozini yopishda xato: turi=%s", type(xato).__name__)


if __name__ == "__main__":
    print(kunlik_reja_tuzish())
