CREATE TABLE listening_history(
    username TEXT NOT NULL,
    catalog TEXT NOT NULL,
    side INTEGER NOT NULL,
    time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (username) REFERENCES users (username),
    FOREIGN KEY (catalog) REFERENCES albums (catalog)
);
