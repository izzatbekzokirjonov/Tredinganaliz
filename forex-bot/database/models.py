"""
PostgreSQL jadval sxemalari (DDL).
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(64),
    first_name VARCHAR(128),
    subscription VARCHAR(16) NOT NULL DEFAULT 'free',
    subscription_expires_at TIMESTAMP NULL,
    referrals INTEGER NOT NULL DEFAULT 0,
    referred_by BIGINT NULL,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

CREATE_SIGNALS_TABLE = """
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    pair VARCHAR(16) NOT NULL,
    direction VARCHAR(8) NOT NULL,
    entry NUMERIC(18,6) NOT NULL,
    tp NUMERIC(18,6) NOT NULL,
    sl NUMERIC(18,6) NOT NULL,
    comment TEXT,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

CREATE_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    tier VARCHAR(16) NOT NULL,
    granted_by VARCHAR(32) NOT NULL,
    starts_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

CREATE_REFERRALS_TABLE = """
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

CREATE_ANALYSIS_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    pair VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

# ─────────────────────────── KANALLAR ───────────────────────────

CREATE_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(128),
    title VARCHAR(256) NOT NULL,
    type VARCHAR(32) NOT NULL DEFAULT 'mandatory',
    -- type qiymatlari: 'mandatory' | 'signal' | 'lesson' | 'info'
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    added_by BIGINT NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

# Har bir foydalanuvchi + kanal juftligining so'nggi tekshirish natijasi
CREATE_USER_CHANNEL_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS user_channel_status (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    is_member BOOLEAN NOT NULL DEFAULT FALSE,
    checked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (telegram_id, channel_id)
);
"""

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_SIGNALS_TABLE,
    CREATE_SUBSCRIPTIONS_TABLE,
    CREATE_REFERRALS_TABLE,
    CREATE_ANALYSIS_LOGS_TABLE,
    CREATE_CHANNELS_TABLE,
    CREATE_USER_CHANNEL_STATUS_TABLE,
]
