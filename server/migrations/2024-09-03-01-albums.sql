CREATE TABLE albums(catalog TEXT PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    discogs_release_id TEXT UNIQUE,
                    descriptor TEXT,
                    created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL);
