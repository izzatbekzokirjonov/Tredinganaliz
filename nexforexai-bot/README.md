# NexForexAI — Telegram Bot MVP

AI yordamida forex signal tahlili beruvchi Telegram bot. Bu **NexForexAI Enterprise
Blueprint**dagi 36 ta bo'limning ishga tushiriladigan birinchi qismi: Telegram Bot +
AI Analysis Engine + Signal Engine + Subscription/Payment + Database.

## Nima qiladi

1. Foydalanuvchi `/start` bosadi, valyuta juftligini tanlaydi (EUR/USD, XAU/USD va h.k.)
2. Bot Twelve Data API orqali so'nggi narx sham (candle) ma'lumotlarini oladi
3. RSI, EMA20/50, MACD hisoblanadi va ovoz berish (voting) usulida BUY/SELL/HOLD
   signal + ishonch foizi chiqariladi
4. Claude API orqali signal foydalanuvchiga tabiiy tilda tushuntiriladi
5. Har bir foydalanuvchi PostgreSQL'da saqlanadi, kunlik signal limiti reja
   (Free/Premium/Pro) bo'yicha tekshiriladi
6. `/premium` — Telegram Payments orqali reja sotib olish; `/promo` — promo kod
   bilan faollashtirish; `/status` — joriy hisobot
7. Har doim risk ogohlantirishi bilan birga yuboriladi

## Loyiha tuzilishi

```
nexforexai_mvp/
├── bot.py                    # Telegram bot (aiogram) — barcha handlerlar
├── config.py                  # Sozlamalar: juftliklar, rejalar, admin ID'lar
├── db/
│   ├── database.py            # Async SQLAlchemy engine/session, init_db()
│   └── models.py               # User, Payment, PromoCode, SignalHistory
├── services/
│   ├── market_data.py          # Twelve Data'dan narx olish
│   ├── indicators.py           # RSI / EMA / MACD hisob-kitobi
│   ├── ai_analysis.py           # Claude orqali matnli tushuntirish
│   ├── subscription.py         # Kunlik limit, reja faollashtirish, promo kod
│   └── payments.py              # Telegram invoice qurish
├── create_promocode.py        # CLI: promo kod yaratish
├── Dockerfile
├── docker-compose.yml          # bot + Postgres
├── requirements.txt
└── .env.example
```

## Lokal o'rnatish (Docker'siz)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env faylni to'ldiring (quyida tushuntirilgan)

# Lokal Postgres bo'lishi kerak, yoki DATABASE_URL'ni docker-compose'dagi
# db xizmatiga yo'naltiring.

python bot.py
```

## Docker bilan ishga tushirish (tavsiya etiladi)

```bash
cp .env.example .env
# .env faylni to'ldiring

docker compose up -d --build
docker compose logs -f bot
```

Bu `db` (Postgres) va `bot` konteynerlarini ishga tushiradi. Jadvallar bot
birinchi marta ishga tushganda avtomatik yaratiladi (`init_db()`).

## .env sozlamalari

| O'zgaruvchi | Tavsif |
|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather'dan olinadi |
| `TWELVE_DATA_API_KEY` | https://twelvedata.com (bepul reja yetarli, kuniga 800 so'rov) |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `DATABASE_URL` | Postgres ulanish satri (docker-compose avtomatik sozlaydi) |
| `PAYMENT_PROVIDER_TOKEN` | @BotFather → Payments orqali ulangan provayder (Payme/Click/Stripe) |
| `ADMIN_IDS` | `/grant` buyrug'ini ishlatishga ruxsat etilgan Telegram ID'lar (vergul bilan) |

## To'lov tizimi haqida

Bot Telegram'ning o'z **Payments API**'sidan foydalanadi (`send_invoice`,
`pre_checkout_query`, `successful_payment`). Buni ishlatish uchun
@BotFather'da botingizga to'lov provayderini ulashingiz kerak:

- CIS mintaqasi uchun: Payme, Click kabi provayderlar Telegram bilan integratsiyaga ega
- Xalqaro uchun: Stripe

`PAYMENT_PROVIDER_TOKEN` sozlanmagan bo'lsa, bot foydalanuvchiga buni aytadi va
o'rniga `/promo` orqali promo kod bilan faollashtirishni taklif qiladi.

### Promo kod yaratish

```bash
python create_promocode.py SUMMER30 premium 30 100
# SUMMER30 kodi -> premium reja, 30 kunga, 100 marta ishlatilishi mumkin
```

### Foydalanuvchiga rejani qo'lda berish (admin)

Telegram'da: `/grant <telegram_id> <plan> <days>` — masalan `/grant 123456 pro 30`
(faqat `.env`dagi `ADMIN_IDS` ro'yxatida bo'lgan foydalanuvchilar uchun ishlaydi).

## Rejalar (MVP darajasida)

| Reja | Kunlik signal limiti | Narx |
|---|---|---|
| Free | 3 | — |
| Premium | 30 | $9.99/oy |
| Pro | Amalda cheksiz | $29.99/oy |

Narxlar `config.py` ichida `PLAN_PRICES_USD` orqali oson o'zgartiriladi.

## Serverga (VPS) joylashtirish

1. VPS'ga Docker va Docker Compose o'rnating
2. Repozitoriyani serverga ko'chiring, `.env` faylni to'ldiring
3. `docker compose up -d --build`
4. Monitoring uchun: `docker compose logs -f`, qayta ishga tushirish uchun
   `docker compose restart bot`
5. Zaxira nusxa: `pgdata` volume'ni muntazam backup qiling
   (`docker exec <db-container> pg_dump -U nexforex nexforexai > backup.sql`)

Ishonchli production uchun keyingi qadam: Nginx + HTTPS orqali webhook rejimiga
o'tish (hozir polling rejimida ishlaydi — kichik/o'rta yuklama uchun yetarli).

## Keyingi qadamlar (blueprint bo'yicha)

- [x] PostgreSQL: foydalanuvchi, to'lov, promo kod, signal tarixi jadvallari
- [x] Obuna (Free/Premium/Pro) va Telegram Payments integratsiyasi
- [x] Docker/Docker Compose orqali deploy
- [ ] Signal Engine'ga ranking va performance tracking qo'shish (bo'lim 10)
- [ ] Grafik/rasm yuklab, chart recognition (bo'lim 13)
- [ ] Ko'p tillilik: ru/en/ar (bo'lim 34)
- [ ] Web-based admin panel (bo'lim 24) — hozircha faqat `/grant` buyrug'i orqali
- [ ] Alembic migratsiyalari (hozir `create_all` bilan soddalashtirilgan)

## Muhim eslatma

Bu bot moliyaviy maslahat bermaydi — faqat texnik ko'rsatkichlar asosidagi
avtomatik tahlildir. Signal va to'lov xizmatlari ko'rsatish ba'zi
mamlakatlarda litsenziya (moliyaviy xizmatlar/reklama qoidalari) talab qilishi
mumkin — ishga tushirishdan oldin yurisdiktsiyangizdagi qoidalarni tekshiring.
