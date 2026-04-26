-- ═══════════════════════════════════════════════════════════
-- PROJETO MIRAI - Schema do banco de dados
-- ═══════════════════════════════════════════════════════════

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    name            TEXT    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login      TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Tabela preparada para futuras medições de poluição luminosa
-- (ainda não usada, fica pronta pro próximo passo)
CREATE TABLE IF NOT EXISTS measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    latitude        REAL    NOT NULL,
    longitude       REAL    NOT NULL,
    radiance        REAL,
    bortle_class    INTEGER,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_meas_coords ON measurements(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_meas_user   ON measurements(user_id);
