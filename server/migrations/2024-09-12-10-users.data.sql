INSERT INTO users(username, password) VALUES
-- password is password
('testuser', 'scrypt:32768:8:1$40jMXD1xDZqBjImU$dac60f5b2420688aecd1991f2b7c29e288139fb5e797800e15d2e7bb77c667fc38fc08045459d9080711434d8b2273ed37dd485a4f79adacb0a8588bd4d91039'),
-- password is empty
('emptyuser', 'scrypt:32768:8:1$x3fU5r5raUv8d0Ou$8e0277bfb811e7d433673e4121a37f22ad8798d9a1e9e171b96025a65ab9ac0cc3a7583562a4863a839a3016f0128e7288a8cb4e398425068e293e3485eebf51');
