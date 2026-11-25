import logging
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from dotenv import load_dotenv
from task_manager import (
    vazifalarni_yuklash,
    vazifa_qoshish,
    vazifani_bajarildi_deb_belgilash,
    vazifa_holatini_almashtirish,
    vazifani_tahrirlash,
    vazifani_ochirish,
)
from ai_planner import kunlik_reja_tuzish

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID", "").strip()

if not BOT_TOKEN:
    raise ValueError("Xato: .env faylida TELEGRAM_BOT_TOKEN topilmadi!")
if ALLOWED_USER_ID and not ALLOWED_USER_ID.isdigit():
    raise ValueError("Xato: .env faylidagi ALLOWED_USER_ID faqat raqamlardan iborat bo'lishi kerak!")

bot = telebot.TeleBot(BOT_TOKEN)
logger = logging.getLogger("lifeos.telegram_bot")
TELEGRAM_XABAR_ENG_KATTA = 3800


def ruxsat_bormi(user_id):
    return bool(ALLOWED_USER_ID) and str(user_id) == ALLOWED_USER_ID


def ruxsat_yoq(message):
    bot.reply_to(message, "Ruxsat yo'q")


def telegram_matnni_bolaklash(matn, limit=TELEGRAM_XABAR_ENG_KATTA):
    matn = (matn or "").strip()
    if not matn:
        return ["AI reja matni bo'sh qaytdi."]

    bolaklar = []
    boshlanish = 0
    while boshlanish < len(matn):
        oxiri = boshlanish
        oxirgi_qulay_joy = None
        birliklar = 0

        while oxiri < len(matn):
            belgi = matn[oxiri]
            belgi_birligi = 2 if ord(belgi) > 0xFFFF else 1
            if birliklar + belgi_birligi > limit:
                break
            birliklar += belgi_birligi
            oxiri += 1
            if belgi in ("\n", " ") and birliklar >= limit // 2:
                oxirgi_qulay_joy = oxiri

        if oxiri < len(matn) and oxirgi_qulay_joy:
            oxiri = oxirgi_qulay_joy
        if oxiri == boshlanish:
            oxiri += 1

        bolak = matn[boshlanish:oxiri]
        if bolak:
            bolaklar.append(bolak)
        boshlanish = oxiri

    return bolaklar


def telegramdagi_reja_xatosini_qayd_et(xato, amal):
    logger.warning(
        "Telegramga reja yuborilmadi: amal=%s, kod=%s, xato_turi=%s",
        amal,
        getattr(xato, "error_code", "noma'lum"),
        type(xato).__name__,
    )


def rejani_telegramga_chiqarish(message, kutish_xabari, reja):
    bolaklar = telegram_matnni_bolaklash(reja)
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=kutish_xabari.message_id,
            text=bolaklar[0],
        )
    except ApiTelegramException as xato:
        if "message is not modified" in str(xato).lower():
            return
        telegramdagi_reja_xatosini_qayd_et(xato, "kutish_xabarini_tahrirlash")
        try:
            bot.send_message(
                message.chat.id,
                "Rejani Telegramga yuborib bo'lmadi. Birozdan keyin /plan buyrug'ini qayta yuboring.",
            )
        except ApiTelegramException as yuborish_xatosi:
            telegramdagi_reja_xatosini_qayd_et(yuborish_xatosi, "xato_xabarini_yuborish")
        return

    for bolak in bolaklar[1:]:
        try:
            bot.send_message(message.chat.id, bolak)
        except ApiTelegramException as xato:
            telegramdagi_reja_xatosini_qayd_et(xato, "reja_bolagini_yuborish")
            try:
                bot.send_message(
                    message.chat.id,
                    "Rejaning qolgan qismini yuborib bo'lmadi. Birozdan keyin /plan buyrug'ini qayta yuboring.",
                )
            except ApiTelegramException as yuborish_xatosi:
                telegramdagi_reja_xatosini_qayd_et(yuborish_xatosi, "xato_xabarini_yuborish")
            return


@bot.message_handler(commands=["myid"])
def telegram_idni_korsat(message):
    # Ruxsat etilgan ID hali sozlanmagan paytda faqat yuboruvchining o'z ID-sini ko'rsatadi.
    if ALLOWED_USER_ID and not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    bot.reply_to(message, str(message.from_user.id))


def royxat_va_tugmalar():
    vazifalar = vazifalarni_yuklash()
    if not vazifalar:
        return "📭 Hozircha vazifalar ro'yxati bo'sh.\nYangi qo'shish: /add Soha | Vazifa nomi", None

    qatorlar = ["📋 LIFEOS VAZIFALAR RO'YXATI:\n"]
    klaviatura = InlineKeyboardMarkup(row_width=3)

    for i, v in enumerate(vazifalar, start=1):
        bajarildi = v.get("bajarildi", False)
        holat = "✅" if bajarildi else "⏳"
        qatorlar.append(f"{i}. {holat} [{v.get('soha', 'Umumiy')}] {v.get('nom')}")

        holat_tugma = InlineKeyboardButton(
            text=f"{i}. {'↩️' if bajarildi else '✅'}",
            callback_data=f"toggle_{i - 1}",
        )
        tahrir_tugma = InlineKeyboardButton(
            text=f"{i}. ✏️",
            callback_data=f"edit_{i - 1}",
        )
        ochirish_tugma = InlineKeyboardButton(
            text=f"{i}. 🗑",
            callback_data=f"del_{i - 1}",
        )
        klaviatura.add(holat_tugma, tahrir_tugma, ochirish_tugma)

    qatorlar.append("\n👇 Boshqarish uchun pastdagi tugmalarni bosing:")
    return "\n".join(qatorlar), klaviatura


@bot.message_handler(commands=["start", "help"])
def boshlash(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    matn = (
        f"Salom, {message.from_user.first_name}! LifeOS v1.1 shaxsiy yordamchisi tayyor.\n"
        f"Sizning Telegram ID: {message.from_user.id}\n\n"
        "Mavjud buyruqlar:\n"
        "/tasks — Vazifalar ro'yxati va boshqaruv tugmalari (✅ ✏️ 🗑)\n"
        "/add Soha | Vazifa nomi — Yangi vazifa qo'shish\n"
        "/edit 1 Soha | Yangi nom — Vazifani tahrirlash (yoki /edit 1 Yangi nom)\n"
        "/del 1 — Vazifani o'chirish\n"
        "/done 1 — Vazifani bajarildi deb belgilash\n"
        "/plan — sun'iy intellekt yordamida bugungi reja tuzish"
    )
    bot.reply_to(message, matn)


@bot.message_handler(commands=["tasks"])
def vazifalar_royxati(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    matn, klaviatura = royxat_va_tugmalar()
    bot.reply_to(message, matn, reply_markup=klaviatura)


@bot.message_handler(commands=["add"])
def vazifa_qoshish_tg(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    qism = message.text.replace("/add", "", 1).strip()
    if "|" not in qism:
        bot.reply_to(
            message,
            "Format xato. Quyidagicha yozing:\n/add Soha | Vazifa nomi\nMisol: /add IELTS | Reading test ishlash",
        )
        return

    soha, nom = [x.strip() for x in qism.split("|", 1)]
    if not soha or not nom:
        bot.reply_to(message, "Soha va vazifa nomi bo'sh bo'lmasligi kerak.")
        return

    vazifa_qoshish(nom, soha)
    bot.reply_to(message, f"✅ Saqlandi: [{soha}] {nom}")


@bot.message_handler(commands=["edit"])
def vazifa_tahrirlash_tg(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    qism = message.text.replace("/edit", "", 1).strip()
    bolaklar = qism.split(" ", 1)
    if len(bolaklar) < 2 or not bolaklar[0].isdigit():
        bot.reply_to(
            message,
            "Format xato. Quyidagicha yozing:\n"
            "/edit 1 Savdo | Narx hajmi tahlilini o'rganish\n"
            "yoki sohani o'zgartirmasdan:\n"
            "/edit 1 Volume Profile o'rganish",
        )
        return

    indeks = int(bolaklar[0]) - 1
    yangi_qism = bolaklar[1].strip()

    if "|" in yangi_qism:
        yangi_soha, yangi_nom = [x.strip() for x in yangi_qism.split("|", 1)]
    else:
        yangi_soha, yangi_nom = None, yangi_qism

    if not yangi_nom:
        bot.reply_to(message, "Yangi vazifa nomi bo'sh bo'lmasligi kerak.")
        return

    yangilangan = vazifani_tahrirlash(indeks, yangi_nom, yangi_soha or None)
    if not yangilangan:
        bot.reply_to(message, "Bunday raqamli vazifa topilmadi. Avval /tasks ni ko'ring.")
        return

    bot.reply_to(
        message,
        f"✏️ Tahrirlandi (#{indeks + 1}): [{yangilangan['soha']}] {yangilangan['nom']}",
    )


@bot.message_handler(commands=["del", "delete"])
def vazifa_ochirish_tg(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    qism = message.text.split(" ", 1)
    if len(qism) < 2 or not qism[1].strip().isdigit():
        bot.reply_to(message, "Vazifa raqamini kiriting. Misol: /del 1")
        return

    indeks = int(qism[1].strip()) - 1
    ochirilgan = vazifani_ochirish(indeks)
    if not ochirilgan:
        bot.reply_to(message, "Bunday raqamli vazifa topilmadi. Avval /tasks ni ko'ring.")
        return

    bot.reply_to(message, f"🗑 O'chirildi: [{ochirilgan.get('soha', 'Umumiy')}] {ochirilgan['nom']}")


@bot.message_handler(commands=["done"])
def vazifa_bajarildi_tg(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    qism = message.text.replace("/done", "", 1).strip()
    if not qism.isdigit():
        bot.reply_to(message, "Vazifa raqamini kiriting. Misol: /done 1")
        return

    indeks = int(qism) - 1
    bajarilgan_vazifa = vazifani_bajarildi_deb_belgilash(indeks)
    if bajarilgan_vazifa is None:
        bot.reply_to(message, "Bunday raqamli vazifa topilmadi. Avval /tasks ni ko'ring.")
        return

    bot.reply_to(message, f"🎉 Bajarildi deb belgilandi: {bajarilgan_vazifa['nom']}")


@bot.callback_query_handler(func=lambda call: True)
def tugma_bosilganda(call):
    if not ruxsat_bormi(call.from_user.id):
        bot.answer_callback_query(call.id, "Ruxsat yo'q", show_alert=True)
        return

    if not isinstance(call.data, str) or "_" not in call.data:
        bot.answer_callback_query(call.id, "Tugma ma'lumoti noto'g'ri.", show_alert=True)
        return

    amal, indeks_str = call.data.split("_", 1)
    if amal not in {"toggle", "edit", "del"} or not indeks_str.isdigit():
        bot.answer_callback_query(call.id, "Tugma ma'lumoti noto'g'ri.", show_alert=True)
        return
    indeks = int(indeks_str)
    vazifalar = vazifalarni_yuklash()

    if indeks < 0 or indeks >= len(vazifalar):
        bot.answer_callback_query(call.id, "Bu vazifa topilmadi yoki o'chirilgan.", show_alert=True)
        return

    if amal == "toggle":
        yangilangan_vazifa = vazifa_holatini_almashtirish(indeks)
        if yangilangan_vazifa is None:
            bot.answer_callback_query(call.id, "Bu vazifa topilmadi yoki o'chirilgan.", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Holat yangilandi!")
        matn, klaviatura = royxat_va_tugmalar()
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=matn,
                reply_markup=klaviatura,
            )
        except ApiTelegramException:
            pass

    elif amal == "del":
        ochirilgan = vazifani_ochirish(indeks)
        if ochirilgan is None:
            bot.answer_callback_query(call.id, "Bu vazifa topilmadi yoki o'chirilgan.", show_alert=True)
            return
        bot.answer_callback_query(call.id, f"O'chirildi: {ochirilgan['nom']}")
        matn, klaviatura = royxat_va_tugmalar()
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=matn,
                reply_markup=klaviatura,
            )
        except ApiTelegramException:
            pass

    elif amal == "edit":
        bot.answer_callback_query(call.id)
        joriy = vazifalar[indeks]
        sorov = bot.send_message(
            call.message.chat.id,
            f"✏️ #{indeks + 1} vazifani tahrirlash:\n"
            f"Hozirgi: [{joriy.get('soha', 'Umumiy')}] {joriy.get('nom')}\n\n"
            "Yangi matnni yuboring (masalan: `Savdo | Tarixiy ma'lumotlarda sinash` yoki yangi nomning o'zi).\n"
            "Bekor qilish uchun /cancel yozing.",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(sorov, tahrirni_saqlash, indeks)


def tahrirni_saqlash(message, indeks):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    if not message.text:
        bot.reply_to(message, "Faqat matn yuboring. Tahrirlash bekor qilindi.")
        return

    matn = message.text.strip()
    if matn.lower() == "/cancel":
        bot.reply_to(message, "❌ Tahrirlash bekor qilindi.")
        return

    if "|" in matn:
        yangi_soha, yangi_nom = [x.strip() for x in matn.split("|", 1)]
    else:
        yangi_soha, yangi_nom = None, matn

    if not yangi_nom:
        bot.reply_to(message, "Vazifa nomi bo'sh bo'lmasligi kerak. Qaytadan urinib ko'ring.")
        return

    yangilangan = vazifani_tahrirlash(indeks, yangi_nom, yangi_soha or None)
    if not yangilangan:
        bot.reply_to(message, "Vazifa topilmadi.")
        return

    royxat_matn, klaviatura = royxat_va_tugmalar()
    bot.send_message(
        message.chat.id,
        f"✅ Tahrirlandi: [{yangilangan['soha']}] {yangilangan['nom']}\n\n{royxat_matn}",
        reply_markup=klaviatura,
    )


@bot.message_handler(commands=["plan"])
def ai_reja_tg(message):
    if not ruxsat_bormi(message.from_user.id):
        ruxsat_yoq(message)
        return
    kutish_xabari = bot.reply_to(message, "⏳ LifeOS sun'iy intellekti vazifalarni tahlil qilmoqda...")
    try:
        reja = kunlik_reja_tuzish()
    except Exception as xato:
        logger.warning("AI reja funksiyasi xato berdi: xato_turi=%s", type(xato).__name__)
        reja = "AI rejasini hozir tuzib bo'lmadi. Birozdan keyin /plan buyrug'ini qayta yuboring."
    rejani_telegramga_chiqarish(message, kutish_xabari, reja)


if __name__ == "__main__":
    print("LifeOS Telegram yordamchisi v1.1 ishga tushdi. To'xtatish uchun Ctrl + C bosing.")
    bot.infinity_polling(skip_pending=True)
