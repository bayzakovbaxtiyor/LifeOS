import json
import os

FAYL_NOMI = "tasks.json"


def vazifalarni_yuklash():
    if not os.path.exists(FAYL_NOMI):
        return []
    with open(FAYL_NOMI, "r", encoding="utf-8") as f:
        return json.load(f)


def vazifalarni_saqlash(vazifalar):
    with open(FAYL_NOMI, "w", encoding="utf-8") as f:
        json.dump(vazifalar, f, ensure_ascii=False, indent=2)


def vazifa_qoshish(vazifalar):
    nom = input("Vazifa nomi: ").strip()
    soha = input("Soha (Universitet / IELTS / Trading / Kod): ").strip()
    vazifalar.append({"nom": nom, "soha": soha, "bajarildi": False})
    vazifalarni_saqlash(vazifalar)
    print("Vazifa faylga saqlandi!")


def vazifalarni_korish(vazifalar):
    if not vazifalar:
        print("Hozircha vazifalar yo'q.")
        return
    print("\n--- SAQLANGAN VAZIFALAR ---")
    for i, v in enumerate(vazifalar, start=1):
        holat = "[+]" if v["bajarildi"] else "[ ]"
        print(f"{i}. {holat} {v['nom']} ({v['soha']})")


def vazifani_bajarish(vazifalar):
    vazifalarni_korish(vazifalar)
    if not vazifalar:
        return
    try:
        raqam = int(input("Bajarilgan vazifa raqami: "))
        if 1 <= raqam <= len(vazifalar):
            vazifalar[raqam - 1]["bajarildi"] = True
            vazifalarni_saqlash(vazifalar)
            print("Holat yangilandi va saqlandi!")
        else:
            print("Noto'g'ri raqam!")
    except ValueError:
        print("Faqat raqam kiriting!")


def main():
    vazifalar = vazifalarni_yuklash()
    while True:
        print("\n=== LIFEOS TASK MANAGER v1.0 ===")
        print("1. Vazifa qo'shish")
        print("2. Vazifalarni ko'rish")
        print("3. Vazifani bajarildi deb belgilash")
        print("0. Chiqish")

        tanlov = input("Tanlovingiz (0-3): ").strip()
        if tanlov == "1":
            vazifa_qoshish(vazifalar)
        elif tanlov == "2":
            vazifalarni_korish(vazifalar)
        elif tanlov == "3":
            vazifani_bajarish(vazifalar)
        elif tanlov == "0":
            print("Barcha ma'lumotlar tasks.json faylida saqlandi. Xayr!")
            break
        else:
            print("Noto'g'ri tanlov!")


main()