@'
# LifeOS — Shaxsiy AI Agent va Vazifalar Boshqaruvchisi (v1.1)

LifeOS — kunlik vazifalarni boshqarish, Gemini AI orqali Top-3 muhim vazifa (MIT) hamda vaqt jadvali (Time Blocking) tuzish uchun mo'ljallangan shaxsiy Telegram bot va CLI tizimi.

## Asosiy imkoniyatlar
- **Xavfsiz kirish nazorati:** Bot faqat `.env` faylida belgilangan `ALLOWED_USER_ID` egasiga javob beradi.
- **Vazifalar boshqaruvi:** `/tasks`, `/add`, `/done`, `/edit`, `/del` buyruqlari hamda interaktiv inline tugmalar (`✅`, `✏️`, `🗑`).
- **Atomar saqlash:** `threading.Lock` va vaqtinchalik `.tmp` fayl orqali `data/tasks.json` buzilishining oldini olish.
- **Gemini AI Planner:** `/plan` buyrug'i orqali kunlik reja tuzish, xatolarni tasniflash va uzun xabarlarni bo'laklab yuborish.

## O'rnatish va ishga tushirish (Windows PowerShell)

1. Virtual muhitni yaratish va faollashtirish:
   ```powershell
   python -m venv .venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   .\.venv\Scripts\Activate.ps1