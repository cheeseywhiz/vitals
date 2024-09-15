CREATE TABLE collections(username TEXT NOT NULL,
                         catalog TEXT NOT NULL,
                         synced TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                         PRIMARY KEY (username, catalog),
                         FOREIGN KEY (username) REFERENCES users (username),
                         FOREIGN KEY (catalog) REFERENCES albums (catalog));
