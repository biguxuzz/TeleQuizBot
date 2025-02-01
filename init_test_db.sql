CREATE USER test_user WITH PASSWORD 'test_password';
CREATE DATABASE test_db WITH OWNER = test_user;
GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;

\c test_db

-- Создаем схему для тестов
CREATE SCHEMA IF NOT EXISTS test_schema;
GRANT ALL ON SCHEMA test_schema TO test_user; 