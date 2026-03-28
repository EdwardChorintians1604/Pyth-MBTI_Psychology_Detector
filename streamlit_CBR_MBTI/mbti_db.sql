    -- SQL Script untuk membuat database dan tabel untuk aplikasi MBTI CBR
    -- Dibuat berdasarkan konfigurasi di CBR.py

    -- 1. Buat database jika belum ada
    CREATE DATABASE IF NOT EXISTS mbti_db;

    -- 2. Gunakan database yang telah dibuat
    USE mbti_db;

    -- 3. Hapus tabel jika sudah ada (opsional, untuk pengembangan/reset)
    -- DROP TABLE IF EXISTS users;
    -- DROP TABLE IF EXISTS case_base;

    -- 4. Buat tabel 'users'
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nama VARCHAR(255) NOT NULL,
        umur INT NOT NULL,
        q1 INT,
        q2 INT,
        q3 INT,
        q4 INT,
        mbti_result TEXT,
        tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 5. Buat tabel 'case_base'
    CREATE TABLE IF NOT EXISTS case_base (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mbti_type VARCHAR(10) NOT NULL,
        q1 INT,
        q2 INT,
        q3 INT,
        q4 INT
    );

    -- 6. Masukkan data prototipe ke tabel 'case_base'
    -- q1(I/E), q2(S/N), q3(T/F), q4(J/P) -- Skala 1 (Kiri) sampai 5 (Kanan)
    INSERT INTO case_base (mbti_type, q1, q2, q3, q4) VALUES
    ('INTJ', 1, 5, 1, 1),
    ('INTP', 1, 5, 1, 5),
    ('ENTJ', 5, 5, 1, 1),
    ('ENTP', 5, 5, 1, 5),
    ('INFJ', 1, 5, 5, 1),
    ('INFP', 1, 5, 5, 5),
    ('ENFJ', 5, 5, 5, 1),
    ('ENFP', 5, 5, 5, 5),
    ('ISTJ', 1, 1, 1, 1),
    ('ISTP', 1, 1, 1, 5),
    ('ESTJ', 5, 1, 1, 1),
    ('ESTP', 5, 1, 1, 5),
    ('ISFJ', 1, 1, 5, 1),
    ('ISFP', 1, 1, 5, 5),
    ('ESFJ', 5, 1, 5, 1),
    ('ESFP', 5, 1, 5, 5);