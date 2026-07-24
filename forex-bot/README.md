# 📊 Forex Analiz Bot V1

Telegram bot — real vaqtda forex/kripto tahlil, screenshot tahlili, signallar, risk kalkulyator va premium tizimi.

---

## ⚙️ Texnologiyalar

| Komponent | Texnologiya |
|---|---|
| Bot framework | aiogram 3.x |
| Database | PostgreSQL + asyncpg |
| Forex narxlar | Twelve Data API |
| Kripto narxlar | Binance Public API |
| AI izohi | OpenAI GPT-4o-mini |
| Screenshot tahlil | OpenAI GPT-4o Vision |

---

## 🚀 Ishga tushirish

### 1. Repozitoriyani klonlash
```bash
git clone <repo_url>
cd forex_bot
```

### 2. Virtual muhit
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
```

### 3. Kutubxonalar
```bash
pip install -r requirements.txt
```

### 4. .env fayli
```bash
cp .env.example .env
nano .env   # o'z qiymatlaringizni kiriting
```

### 5. PostgreSQL database yaratish
```bash
psql -U postgres -c "CREATE DATABASE forex_bot;"
```

### 6. Botni ishga tushirish
```bash
python app.py
```

Jadvallar birinchi ishga tushirishda avtomatik yaratiladi.

---

## 📁 Loyiha strukturasi

```
forex_bot/
├── app.py                  # Kirish nuqtasi
├── config.py               # Sozlamalar
├── requirements.txt
├── .env.example
│
├── database/
│   ├── db.py               # PostgreSQL pool
│   ├── models.py           # DDL (jadval sxemalari)
│   ├── queries.py          # Asosiy SQL so'rovlar
│   └── channel_queries.py  # Kanal SQL so'rovlari
│
├── handlers/
│   ├── start.py            # /start, referal
│   ├── analysis.py         # Tahlil + screenshot
│   ├── signals.py          # Signallar
│   ├── calculator.py       # Risk kalkulyator (FSM)
│   ├── profile.py          # Profil
│   ├── premium.py          # Premium tariflar
│   ├── channels.py         # Admin: kanal boshqaruv
│   ├── admin_user.py       # Admin: /user, /members
│   └── admin.py            # Admin: ban, broadcast, signal...
│
├── keyboards/
│   ├── main_menu.py
│   ├── profile_menu.py
│   ├── premium_menu.py
│   └── admin_menu.py
│
├── services/
│   ├── market_service.py   # Twelve Data + Binance + texnik tahlil
│   ├── ai_service.py       # OpenAI izohi
│   ├── vision_service.py   # GPT-4o Vision (screenshot)
│   ├── signal_service.py   # Signal formatlash + broadcast
│   ├── channel_service.py  # Kanal a'zolik tekshiruvi
│   ├── payment_service.py  # Premium berish/olish
│   └── referral_service.py # Referal tizimi
│
├── middlewares/
│   ├── auth.py             # Ban tekshiruvi
│   └── subscription.py     # Majburiy kanal tekshiruvi
│
├── states/
│   ├── analysis_state.py
│   └── calculator_state.py
│
└── utils/
    ├── logger.py
    ├── helpers.py
    └── validators.py
```

---

## 📋 Asosiy buyruqlar

### Foydalanuvchilar
| Buyruq | Vazifasi |
|---|---|
| `/start` | Botni boshlash |
| `/premium` | Tariflar |

### Admin
| Buyruq | Vazifasi |
|---|---|
| `/admin` | Admin panel |
| `/stats` | Statistika |
| `/broadcast` | Hammaga xabar |
| `/signal` | Signal yuborish |
| `/premium_give` | Premium berish |
| `/premium_remove` | Premium olish |
| `/ban [ID]` | Ban |
| `/unban [ID]` | Unban |
| `/addchannel` | Kanal qo'shish |
| `/removechannel` | Kanalni o'chirish |
| `/channels` | Kanallar ro'yxati |
| `/channelstats [ID]` | Kanal statistikasi |
| `/user [ID]` | Foydalanuvchi holati |
| `/members` | A'zolik ro'yxati |

---

## 📈 Tahlil limitleri

| Tarif | Kunlik limit |
|---|---|
| 🆓 Free | 5 ta |
| ⭐ Pro | 50 ta |
| 💎 VIP | Cheksiz |

Screenshot tahlili ham shu limitga kiradi.

---

## 🔗 Referal tizimi

- **3 referal** → 1 kunlik Pro
- **10 referal** → 7 kunlik Pro

Muddat uzaytirib beriladi (mavjud muddatga qo'shiladi).

---

## ⚠️ Muhim eslatmalar

1. **Bot kanallarda admin bo'lishi kerak** — kanal a'zoligini tekshirish uchun.
2. **Screenshot tahlili** `gpt-4o` modelini talab qiladi (`.env` da `OPENAI_MODEL=gpt-4o`).
3. **Twelve Data** bepul planda minutiga 8 ta so'rov — ko'p foydalanuvchi bo'lsa Pro plan oling.
