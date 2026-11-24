vazifalar = []

while True:
    print("\n--- LIFEOS VAZIFALAR RO'YXATI ---")
    print("1. Vazifa qo'shish")
    print("2. Vazifalarni ko'rish")
    print("3. Vazifani bajarildi deb belgilash")
    print("0. Chiqish")

    tanlov = input("Tanlovingiz (0-3): ")

    if tanlov == "1":
        nom = input("Vazifa nomi: ")
        soha = input("Soha (Universitet / IELTS / Trading / Kod): ")
        vazifalar.append({"nom": nom, "soha": soha, "bajarildi": False})
        print("Vazifa qo'shildi!")

    elif tanlov == "2":
        if len(vazifalar) == 0:
            print("Hozircha vazifalar yo'q.")
        else:
            for indeks, v in enumerate(vazifalar, start=1):
                belgi = "[+]" if v["bajarildi"] else "[ ]"
                print(f"{indeks}. {belgi} {v['nom']} ({v['soha']})")

    elif tanlov == "3":
        raqam = int(input("Bajarilgan vazifa raqamini kiriting: "))
        if 1 <= raqam <= len(vazifalar):
            vazifalar[raqam - 1]["bajarildi"] = True
            print("Bajarildi deb belgilandi!")
        else:
            print("Noto'g'ri raqam!")

    elif tanlov == "0":
        print("Dastur yakunlandi.")
        break
    else:
        print("Faqat 0 dan 3 gacha raqam kiriting.")