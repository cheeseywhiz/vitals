CREATE TABLE db_metadata(version TEXT,
                         has_real_data BOOLEAN NOT NULL,
                         has_test_data BOOLEAN NOT NULL,
                         created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL);

INSERT INTO db_metadata(has_real_data, has_test_data) VALUES ('no', 'no') ON CONFLICT DO NOTHING;
