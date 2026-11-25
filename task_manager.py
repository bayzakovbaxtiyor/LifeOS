import json
import os
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAYL_NOMI = os.path.join(BASE_DIR, "data", "tasks.json")
FILE_LOCK = threading.Lock()


def _vazifalarni_yuklash_qulf_ichida():
    if not os.path.exists(FAYL_NOMI):
        return []
    with open(FAYL_NOMI, "r", encoding="utf-8") as f:
        return json.load(f)


def _vazifalarni_saqlash_qulf_ichida(vazifalar):
    os.makedirs(os.path.dirname(FAYL_NOMI), exist_ok=True)
    vaqtinchalik = FAYL_NOMI + ".tmp"
    try:
        with open(vaqtinchalik, "w", encoding="utf-8") as f:
            json.dump(vazifalar, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(vaqtinchalik, FAYL_NOMI)
    finally:
        if os.path.exists(vaqtinchalik):
            os.remove(vaqtinchalik)


def vazifalarni_yuklash():
    with FILE_LOCK:
        return _vazifalarni_yuklash_qulf_ichida()


def vazifalarni_saqlash(vazifalar):
    with FILE_LOCK:
        _vazifalarni_saqlash_qulf_ichida(vazifalar)


def vazifa_qoshish(nom, soha):
    with FILE_LOCK:
        vazifalar = _vazifalarni_yuklash_qulf_ichida()
        yangi_vazifa = {"nom": nom, "soha": soha, "bajarildi": False}
        vazifalar.append(yangi_vazifa)
        _vazifalarni_saqlash_qulf_ichida(vazifalar)
        return yangi_vazifa


def vazifani_bajarildi_deb_belgilash(indeks):
    with FILE_LOCK:
        vazifalar = _vazifalarni_yuklash_qulf_ichida()
        if indeks < 0 or indeks >= len(vazifalar):
            return None
        vazifalar[indeks]["bajarildi"] = True
        _vazifalarni_saqlash_qulf_ichida(vazifalar)
        return vazifalar[indeks]


def vazifa_holatini_almashtirish(indeks):
    with FILE_LOCK:
        vazifalar = _vazifalarni_yuklash_qulf_ichida()
        if indeks < 0 or indeks >= len(vazifalar):
            return None
        vazifalar[indeks]["bajarildi"] = not vazifalar[indeks].get("bajarildi", False)
        _vazifalarni_saqlash_qulf_ichida(vazifalar)
        return vazifalar[indeks]


def vazifani_tahrirlash(indeks, yangi_nom, yangi_soha=None):
    with FILE_LOCK:
        vazifalar = _vazifalarni_yuklash_qulf_ichida()
        if indeks < 0 or indeks >= len(vazifalar):
            return None
        vazifalar[indeks]["nom"] = yangi_nom
        if yangi_soha:
            vazifalar[indeks]["soha"] = yangi_soha
        _vazifalarni_saqlash_qulf_ichida(vazifalar)
        return vazifalar[indeks]


def vazifani_ochirish(indeks):
    with FILE_LOCK:
        vazifalar = _vazifalarni_yuklash_qulf_ichida()
        if indeks < 0 or indeks >= len(vazifalar):
            return None
        ochirilgan = vazifalar.pop(indeks)
        _vazifalarni_saqlash_qulf_ichida(vazifalar)
        return ochirilgan


def main():
    while True:
        print("\n=== LIFEOS VAZIFALAR BOSHQARUVI v1.1 ===")
        print("1. Vazifa qo'shish")
        print("2. Vazifalarni ko'rish")
        print("3. Vazifani bajarildi deb belgilash")
        print("4. Vazifani tahrirlash")
        print("5. Vazifani o'chirish")
        print("0. Chiqish")
        tanlov = input("Tanlovingiz (0-5): ").strip()

        if tanlov == "1":
            soha = input("Soha (masalan, Kod, Universitet, Trading): ").strip() or "Umumiy"
            nom = input("Vazifa nomi: ").strip()
            if nom:
                vazifa_qoshish(nom, soha)
                print("Vazifa saqlandi!")
            else:
                print("Xato: vazifa nomi bo'sh bo'lmasligi kerak.")
        elif tanlov == "2":
            vazifalar = vazifalarni_yuklash()
            if not vazifalar:
                print("Vazifalar ro'yxati bo'sh.")
            for i, v in enumerate(vazifalar, start=1):
                holat = "[x]" if v.get("bajarildi") else "[ ]"
                print(f"{i}. {holat} [{v.get('soha', 'Umumiy')}] {v.get('nom')}")
        elif tanlov == "3":
            vazifalar = vazifalarni_yuklash()
            raqam = input("Bajarilgan vazifa raqami: ").strip()
            if not raqam.isdigit() or not vazifani_bajarildi_deb_belgilash(int(raqam) - 1):
                print("Xato: bunday raqamli vazifa topilmadi.")
            else:
                print("Vazifa bajarildi deb belgilandi!")
        elif tanlov == "4":
            raqam = input("Tahrirlanadigan vazifa raqami: ").strip()
            if raqam.isdigit():
                yangi_soha = input("Yangi soha (o'zgartirmaslik uchun Enter): ").strip()
                yangi_nom = input("Yangi vazifa nomi: ").strip()
                if yangi_nom and vazifani_tahrirlash(int(raqam) - 1, yangi_nom, yangi_soha or None):
                    print("Vazifa tahrirlandi!")
                else:
                    print("Xato: vazifa nomi bo'sh yoki raqam noto'g'ri.")
            else:
                print("Xato: vazifa raqamini kiriting.")
        elif tanlov == "5":
            raqam = input("O'chiriladigan vazifa raqami: ").strip()
            if raqam.isdigit():
                ochirilgan = vazifani_ochirish(int(raqam) - 1)
                if ochirilgan:
                    print(f"O'chirildi: {ochirilgan['nom']}")
                else:
                    print("Xato: bunday raqamli vazifa topilmadi.")
            else:
                print("Xato: vazifa raqamini kiriting.")
        elif tanlov == "0":
            print("Barcha ma'lumotlar data/tasks.json faylida saqlandi. Xayr!")
            break


if __name__ == "__main__":
    main()
