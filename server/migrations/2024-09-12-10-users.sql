CREATE TABLE users(username TEXT PRIMARY KEY,
                   password TEXT NOT NULL,
                   created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL);
