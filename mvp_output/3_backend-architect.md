# 🏗️ 後端架構師交付成果
我們規劃了資料庫與 API 合約。

[FILE: src/db/schema.sql]
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
[FILE_END]
