# Orqa fon bot

Rasmning orqa fonini olib tashlaydigan va yangi fon qo'shadigan Telegram bot.

## Imkoniyatlar

- 🗑 **Fonni olib tashlash** — rasmning orqa fonini butunlay olib tashlaydi (shaffof PNG qaytaradi).
- 🖼 **Fon qo'shish** — orqa foni olib tashlangan rasmga yangi fon qo'shadi.
- 🔁 **Fonni almashtirish** — bitta amalda: avval fonni olib tashlaydi, so'ng yangi fon qo'shadi.
- ⚙️ **Orqa fonni sozlash** — o'zingizga doimiy fon rasmini saqlab qo'yasiz, keyingi safar "Fon qo'shish" / "Fonni almashtirish"da uni qayta yuklamasdan tanlashingiz mumkin.
- Birinchi `/start`da telefon raqami so'raladi va shu raqam bilan ro'yxatdan o'tkaziladi.
- Bepul foydalanishda **5 ta urinish** beriladi (barcha amallar uchun umumiy hisob). Urinishlar tugagach, botda ko'rsatilgan karta raqamiga to'lov qilib, o'z ID'ini adminga yuborish kerak.
- Admin `/addcredit`, `/block`, `/unblock`, `/userinfo`, `/stats` buyruqlari orqali foydalanuvchilarni boshqaradi.

## O'rnatish

**Diqqat:** `rembg` (fon olib tashlovchi kutubxona) hozircha Python 3.14'ni qo'llab-quvvatlamaydi (`numba` bog'liqligi sabab). **Python 3.11 yoki 3.12** ishlatilishi kerak. Agar kompyuteringizda faqat yangiroq Python bo'lsa, [python.org](https://www.python.org/downloads/)dan 3.12'ni o'rnating (mavjud versiyalarga tegmaydi) va `py -3.12` orqali chaqiring.

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

`.env.example` faylidan nusxa ko'chirib `.env` deb saqlang va o'z qiymatlaringizni kiriting:

```bash
copy .env.example .env
```

`.env` faylida:

- `BOT_TOKEN` — @BotFather'dan olingan token. **Diqqat:** token hech qachon kodga yoki chatga ochiq yozilmasligi kerak, faqat shu faylda saqlanadi.
- `ADMIN_ID` — admin sifatida limit/blok huquqiga ega yagona chat ID. **Majburiy** — to'ldirilmasa bot ishga tushmaydi.
- `ADMIN_CONTACT` — to'lovdan keyin foydalanuvchilar murojaat qiladigan admin username (masalan `@username`). **Majburiy**.
- `PAYMENT_CARD` — foydalanuvchiga ko'rsatiladigan to'lov karta raqami. **Majburiy**.
- `FREE_ATTEMPTS` — bepul urinishlar soni (standart: `5`).
- `PRICE_SOM`, `PRICE_ATTEMPTS` — faqat matn sifatida ko'rsatiladigan narx ma'lumoti (hisob-kitob admin tomonidan qo'lda `/addcredit` orqali amalga oshiriladi).
- `REMBG_MODEL` — `u2net` (sifatli, standart) yoki `u2netp` (yengil/tez, kuchsiz serverlar uchun).

Barcha "Majburiy" deb belgilangan qiymatlar to'ldirilmasa, bot xato bilan to'xtaydi va qaysi qiymat yetishmayotganini ko'rsatadi.

## Ishga tushirish

```bash
python -m bot.main
```

Birinchi ishga tushirishda `rembg` modeli (bir necha o'n MB) avtomatik yuklab olinadi — internet aloqasi kerak.

## Admin buyruqlari

Faqat `ADMIN_ID`dagi foydalanuvchi ishlata oladi:

- `/addcredit <chat_id> <son>` — foydalanuvchiga urinish qo'shish (to'lov tushgach qo'lda beriladi, masalan 10 so'm → 60 ta urinish uchun `/addcredit 123456789 60`).
- `/block <chat_id>` — foydalanuvchini bloklash.
- `/unblock <chat_id>` — blokdan chiqarish.
- `/userinfo <chat_id>` — telefon raqami, qolgan urinishlar, blok holati.
- `/stats` — umumiy foydalanuvchilar soni va bloklanganlar soni.

## Railway'ga deploy qilish

Loyihada `railway.json` fayli bor — Railway'ning avtomatik aniqlagichi (Railpack) ildizda `main.py` topa olmay xato berishining oldini olish uchun ishga tushirish buyrug'i (`python -m bot.main`) shu faylda aniq ko'rsatilgan, qo'shimcha sozlash shart emas.

Railway loyihasida **Variables** bo'limiga `.env`dagi barcha qiymatlarni qo'shing: `BOT_TOKEN`, `ADMIN_ID`, `ADMIN_CONTACT`, `PAYMENT_CARD` (majburiy), va xohlasangiz `FREE_ATTEMPTS`, `PRICE_SOM`, `PRICE_ATTEMPTS`, `REMBG_MODEL`.

**Muhim — doimiy saqlash (Volume):** Railway konteyneri qayta ishga tushganda (deploy, restart) standart fayl tizimi o'chib ketadi — bu holda foydalanuvchilar bazasi, saqlangan fon rasmlari va yuklab olingan AI-model (~170MB) har safar yo'qolib, qaytadan yuklanadi. Buning oldini olish uchun:

1. Railway loyihangizda **Volume** qo'shing va uni masalan `/data` yo'liga ulang.
2. Variables'ga `APP_DATA_DIR=/data` qo'shing.

Shundan so'ng baza (`data/bot.db`), saqlangan fonlar (`storage/`) va rembg modeli shu Volume ichida saqlanadi va qayta ishga tushirishlarda yo'qolmaydi.

## Loyihaning tuzilishi

```
bot/
  main.py            — kirish nuqtasi (polling)
  config.py          — .env sozlamalari
  db.py              — SQLite (aiosqlite) — foydalanuvchilar, urinishlar, blok holati
  states.py          — FSM holatlari
  keyboards.py        — inline/reply klaviaturalar
  services/
    bg_remove.py      — rembg orqali fon olib tashlash
    bg_compose.py      — Pillow orqali fon qo'shish
  handlers/
    start.py          — /start va ro'yxatdan o'tish (telefon raqami)
    menu.py            — 4 ta asosiy tugma va rasm/fon jarayonlari
    admin.py           — admin buyruqlari
data/                — SQLite baza fayli (avtomatik yaratiladi, gitignore'da)
storage/
  backgrounds/        — har bir foydalanuvchining saqlangan foni
  tmp/                — vaqtinchalik fayllar (jarayon davomida)
```

## Eslatma

- Telegramga oddiy "photo" sifatida yuborilgan rasmlar JPEG'ga siqiladi va shaffoflikni yo'qotadi. Shaffof PNG (masalan, "Fonni olib tashlash" natijasi) yuborayotganda uni albatta **fayl/hujjat** sifatida yuboring, aks holda shaffoflik yo'qolishi mumkin.
- `data/` va `storage/` papkalari `.gitignore`ga qo'shilgan — ularda shaxsiy foydalanuvchi ma'lumotlari (telefon raqami, rasmlar) saqlanadi, git repozitoriyga tushmasligi kerak.
