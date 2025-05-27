-- Video Editor Database Schema
-- Based on Peewee models for video editing application
-- SQLite compatible with PostgreSQL/MySQL adaptations noted

-- Enable foreign key constraints (SQLite specific)
PRAGMA foreign_keys = ON;

-- =============================================
-- DROP TABLES (for clean recreation)
-- =============================================
DROP TABLE IF EXISTS brand_kit_transitions;
DROP TABLE IF EXISTS api_keys;
DROP TABLE IF EXISTS captions;
DROP TABLE IF EXISTS auto_intro_settings;
DROP TABLE IF EXISTS brand_kits;
DROP TABLE IF EXISTS transitions;
DROP TABLE IF EXISTS voices;

-- =============================================
-- CORE TABLES
-- =============================================

-- Voices table for TTS configuration
CREATE TABLE voices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider VARCHAR(50) NOT NULL CHECK (provider IN (
        'edge_tts', 'minimax_t2a_turbo', 'replicate'
    )),
    language VARCHAR(10) NULL,  -- e.g., 'en-US', 'ru-RU'
    voice_id VARCHAR(100) NOT NULL,
    speed REAL NOT NULL DEFAULT 1.0 CHECK (speed >= 0.1 AND speed <= 5.0),

    -- Unique constraint on provider + voice_id combination
    UNIQUE(provider, voice_id)
);

-- Transitions table for video transition effects
CREATE TABLE transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL CHECK (name IN (
        'none', 'fade', 'dissolve', 'pixelize', 'radial', 'hblur', 'distance',
        'wipeleft', 'wiperight', 'wipeup', 'wipedown',
        'slideleft', 'slideright', 'slideup', 'slidedown',
        'diagtl', 'diagtr', 'diagbl', 'diagbr',
        'hlslice', 'hrslice', 'vuslice', 'vdslice',
        'circlecrop', 'rectcrop', 'circleopen', 'circleclose',
        'fadeblack', 'fadewhite', 'fadegrays'
    )),
    description VARCHAR(100) NULL
);

-- Main brand kits table
CREATE TABLE brand_kits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,

    -- Media file paths
    intro_clip_path VARCHAR(500) NULL,
    watermark_path VARCHAR(500) NULL,
    avatar_clip_path VARCHAR(500) NULL,
    subscribe_cta_path VARCHAR(500) NULL,
    music_path VARCHAR(500) NULL,
    lut_path VARCHAR(500) NULL,
    mask_effect_path VARCHAR(500) NULL,

    -- Configuration options
    randomize_clips BOOLEAN NOT NULL DEFAULT 0,
    watermark_position VARCHAR(20) NOT NULL DEFAULT 'top_right' CHECK (watermark_position IN (
        'top_left', 'top_center', 'top_right',
        'middle_left', 'middle_center', 'middle_right',
        'bottom_left', 'bottom_center', 'bottom_right'
    )),
    avatar_position VARCHAR(20) NOT NULL DEFAULT 'bottom_left' CHECK (avatar_position IN (
        'top_left', 'top_center', 'top_right',
        'middle_left', 'middle_center', 'middle_right',
        'bottom_left', 'bottom_center', 'bottom_right'
    )),
    subscribe_cta_interval INTEGER NOT NULL DEFAULT 120,

    -- Audio and video settings
    voice_id INTEGER NULL REFERENCES voices(id) ON DELETE SET NULL,
    aspect_ratio VARCHAR(10) NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('16:9', '9:16')),
    music_volume INTEGER NOT NULL DEFAULT 20 CHECK (music_volume >= 0 AND music_volume <= 100),
    transition_duration REAL NOT NULL DEFAULT 0.5,

    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Auto intro settings (1-to-1 with brand_kits)
CREATE TABLE auto_intro_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_kit_id INTEGER UNIQUE NOT NULL REFERENCES brand_kits(id) ON DELETE CASCADE,

    enabled BOOLEAN NOT NULL DEFAULT 1,
    title_font VARCHAR(50) NOT NULL DEFAULT 'Arial' CHECK (title_font IN (
        'Arial', 'Verdana', 'Tahoma', 'Georgia', 'Times New Roman',
        'Courier New', 'Impact', 'Comic Sans MS', 'Roboto'
    )),
    title_font_size INTEGER NOT NULL DEFAULT 48 CHECK (title_font_size >= 8 AND title_font_size <= 200),
    title_font_color CHAR(6) NOT NULL DEFAULT 'FFFFFF' CHECK (
        length(title_font_color) = 6 AND
        title_font_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
    ),

    title_background_type VARCHAR(10) NOT NULL DEFAULT 'color' CHECK (title_background_type IN (
        'color', 'image', 'video'
    )),
    title_background_value VARCHAR(500) NOT NULL DEFAULT '000000',

    typewriter_speed INTEGER NOT NULL DEFAULT 50 CHECK (typewriter_speed >= 1 AND typewriter_speed <= 1000)
);

-- Caption settings (1-to-1 with brand_kits)
CREATE TABLE captions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_kit_id INTEGER UNIQUE NOT NULL REFERENCES brand_kits(id) ON DELETE CASCADE,

    font VARCHAR(50) NOT NULL DEFAULT 'Arial' CHECK (font IN (
        'Arial', 'Verdana', 'Tahoma', 'Georgia', 'Times New Roman',
        'Courier New', 'Impact', 'Comic Sans MS', 'Roboto'
    )),
    font_size INTEGER NOT NULL DEFAULT 24,
    font_color CHAR(6) NOT NULL DEFAULT 'FFFFFF' CHECK (
        length(font_color) = 6 AND
        font_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
    ),
    stroke_width INTEGER NOT NULL DEFAULT 2,
    stroke_color CHAR(6) NOT NULL DEFAULT '000000' CHECK (
        length(stroke_color) = 6 AND
        stroke_color GLOB '[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'
    ),
    position VARCHAR(20) NOT NULL DEFAULT 'bottom_center' CHECK (position IN (
        'top_left', 'top_center', 'top_right',
        'middle_left', 'middle_center', 'middle_right',
        'bottom_left', 'bottom_center', 'bottom_right'
    )),
    max_words_per_line INTEGER NOT NULL DEFAULT 7 CHECK (max_words_per_line >= 1 AND max_words_per_line <= 20)
);

-- Junction table for brand_kits <-> transitions (many-to-many)
CREATE TABLE brand_kit_transitions (
    brand_kit_id INTEGER NOT NULL REFERENCES brand_kits(id) ON DELETE CASCADE,
    transition_id INTEGER NOT NULL REFERENCES transitions(id) ON DELETE CASCADE,

    PRIMARY KEY (brand_kit_id, transition_id)
);

-- API Keys table for external services
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name VARCHAR(50) NOT NULL CHECK (service_name IN (
        'edge_tts', 'minimax_t2a_turbo', 'replicate'
    )),
    api_key_plaintext VARCHAR(500) UNIQUE NOT NULL,  -- Should be encrypted in production
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Index on brand_kits name for fast lookups
CREATE INDEX idx_brand_kits_name ON brand_kits(name);

-- Index on brand_kits timestamps for sorting
CREATE INDEX idx_brand_kits_created_at ON brand_kits(created_at);
CREATE INDEX idx_brand_kits_updated_at ON brand_kits(updated_at);

-- Index on voices provider for filtering
CREATE INDEX idx_voices_provider ON voices(provider);

-- Index on transitions name for lookups
CREATE INDEX idx_transitions_name ON transitions(name);

-- Index on api_keys service and active status
CREATE INDEX idx_api_keys_service_active ON api_keys(service_name, is_active);

-- =============================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =============================================

-- Update timestamp trigger for brand_kits
CREATE TRIGGER update_brand_kits_timestamp
    AFTER UPDATE ON brand_kits
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at  -- Only update if not manually set
BEGIN
    UPDATE brand_kits SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =============================================
-- INITIAL DATA POPULATION
-- =============================================

-- Populate transitions table with all available transition types
INSERT INTO transitions (name, description) VALUES
    ('none', 'None'),
    ('fade', 'Fade'),
    ('dissolve', 'Dissolve'),
    ('pixelize', 'Pixelize'),
    ('radial', 'Radial'),
    ('hblur', 'Horizontal Blur'),
    ('distance', 'Distance'),
    ('wipeleft', 'Wipe Left'),
    ('wiperight', 'Wipe Right'),
    ('wipeup', 'Wipe Up'),
    ('wipedown', 'Wipe Down'),
    ('slideleft', 'Slide Left'),
    ('slideright', 'Slide Right'),
    ('slideup', 'Slide Up'),
    ('slidedown', 'Slide Down'),
    ('diagtl', 'Diagonal Top-Left'),
    ('diagtr', 'Diagonal Top-Right'),
    ('diagbl', 'Diagonal Bottom-Left'),
    ('diagbr', 'Diagonal Bottom-Right'),
    ('hlslice', 'Horizontal Slice'),
    ('hrslice', 'Horizontal Reverse Slice'),
    ('vuslice', 'Vertical Slice'),
    ('vdslice', 'Vertical Reverse Slice'),
    ('circlecrop', 'Circle Crop'),
    ('rectcrop', 'Rectangle Crop'),
    ('circleopen', 'Circle Open'),
    ('circleclose', 'Circle Close'),
    ('fadeblack', 'Fade to Black'),
    ('fadewhite', 'Fade to White'),
    ('fadegrays', 'Fade to Grays');

-- Insert some default voices for common TTS providers
INSERT INTO voices (provider, language, voice_id, speed) VALUES
    -- Edge TTS voices (free tier)
    ('edge_tts', 'en-US', 'AriaNeural', 1.0),
    ('edge_tts', 'en-US', 'GuyNeural', 1.0),
    ('edge_tts', 'en-US', 'JennyNeural', 1.0),
    ('edge_tts', 'en-GB', 'LibbyNeural', 1.0),
    ('edge_tts', 'en-GB', 'RyanNeural', 1.0),

    -- Example entries for other providers (would need actual voice IDs)
    ('minimax_t2a_turbo', 'en-US', 'voice-001', 1.0),
    ('replicate', 'en-US', 'cloned-voice-001', 1.0);

-- =============================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================

-- Create a sample brand kit
INSERT INTO brand_kits (name, aspect_ratio, music_volume, voice_id) VALUES
    ('Default Brand Kit', '16:9', 20, 1);

-- Get the ID of the created brand kit for related records
-- Note: In a real scenario, you'd use the actual ID returned from the INSERT

-- Create related auto intro settings
INSERT INTO auto_intro_settings (brand_kit_id, enabled, title_font, title_font_size, title_font_color) VALUES
    (1, 1, 'Arial', 48, 'FFFFFF');

-- Create related caption settings
INSERT INTO captions (brand_kit_id, font, font_size, font_color, position) VALUES
    (1, 'Arial', 24, 'FFFFFF', 'bottom_center');

-- Assign some transitions to the brand kit
INSERT INTO brand_kit_transitions (brand_kit_id, transition_id) VALUES
    (1, (SELECT id FROM transitions WHERE name = 'fade')),
    (1, (SELECT id FROM transitions WHERE name = 'dissolve')),
    (1, (SELECT id FROM transitions WHERE name = 'slideleft'));

-- =============================================
-- VIEWS FOR CONVENIENT DATA ACCESS
-- =============================================

-- View to get brand kits with their voice information
CREATE VIEW brand_kits_with_voice AS
SELECT
    bk.id,
    bk.name,
    bk.aspect_ratio,
    bk.music_volume,
    bk.created_at,
    bk.updated_at,
    v.provider as voice_provider,
    v.language as voice_language,
    v.voice_id,
    v.speed as voice_speed
FROM brand_kits bk
LEFT JOIN voices v ON bk.voice_id = v.id;

-- View to get brand kit transitions
CREATE VIEW brand_kit_transition_details AS
SELECT
    bk.id as brand_kit_id,
    bk.name as brand_kit_name,
    t.id as transition_id,
    t.name as transition_name,
    t.description as transition_description
FROM brand_kits bk
JOIN brand_kit_transitions bkt ON bk.id = bkt.brand_kit_id
JOIN transitions t ON bkt.transition_id = t.id
ORDER BY bk.name, t.name;

-- =============================================
-- USEFUL QUERIES FOR APPLICATION
-- =============================================

/*
-- Get all brand kits with their complete configuration
SELECT
    bk.*,
    ais.enabled as intro_enabled,
    ais.title_font as intro_font,
    c.font as caption_font,
    c.position as caption_position,
    v.provider as voice_provider,
    v.voice_id
FROM brand_kits bk
LEFT JOIN auto_intro_settings ais ON bk.id = ais.brand_kit_id
LEFT JOIN captions c ON bk.id = c.brand_kit_id
LEFT JOIN voices v ON bk.voice_id = v.id;

-- Get all transitions available for a specific brand kit
SELECT t.name, t.description
FROM transitions t
JOIN brand_kit_transitions bkt ON t.id = bkt.transition_id
WHERE bkt.brand_kit_id = ?;

-- Get active API keys by service
SELECT service_name, api_key_plaintext
FROM api_keys
WHERE is_active = 1
ORDER BY service_name;
*/
