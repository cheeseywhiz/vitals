CREATE TABLE albums(catalog TEXT PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    discogs_release_id TEXT UNIQUE,
                    album_cover_url TEXT,
                    descriptor TEXT,
                    created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL);
