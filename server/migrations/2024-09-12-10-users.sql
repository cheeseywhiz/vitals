CREATE TABLE users(username TEXT PRIMARY KEY,
                   password TEXT NOT NULL,
                   created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                   current_album TEXT,
                   FOREIGN KEY (current_album) REFERENCES albums (catalog));
