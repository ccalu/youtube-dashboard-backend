-- Migration 028: Auth users table for JWT authentication
-- 2026-03-06

CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    username_lower TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed 4 users with bcrypt hash of "vpb123"
INSERT INTO auth_users (username, username_lower, display_name, password_hash) VALUES
    ('cellibs', 'cellibs', 'Cellibs', '$2b$12$i6sdvYc/5J7M3rujJO4HJ.Qs.s1s5GFvbRfjjdGjgIj8Vg9N0X3Pa'),
    ('micha', 'micha', 'Micha', '$2b$12$i6sdvYc/5J7M3rujJO4HJ.Qs.s1s5GFvbRfjjdGjgIj8Vg9N0X3Pa'),
    ('lucca', 'lucca', 'Lucca', '$2b$12$i6sdvYc/5J7M3rujJO4HJ.Qs.s1s5GFvbRfjjdGjgIj8Vg9N0X3Pa'),
    ('joao', 'joao', 'Joao', '$2b$12$i6sdvYc/5J7M3rujJO4HJ.Qs.s1s5GFvbRfjjdGjgIj8Vg9N0X3Pa')
ON CONFLICT (username_lower) DO NOTHING;
