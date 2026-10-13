-- MySQL schema for SmartPack AI.
-- Usage (cmd):  mysql -u root -p < database\schema.sql
-- The Flask backend also creates these tables itself on start-up and seeds the
-- reference rows, so this file is mainly for viewing/documentation or manual setup.

CREATE DATABASE IF NOT EXISTS smartpack CHARACTER SET utf8mb4;
USE smartpack;

CREATE TABLE IF NOT EXISTS foods (
  food_id           INT AUTO_INCREMENT PRIMARY KEY,
  food_name         VARCHAR(50) UNIQUE NOT NULL,
  emoji             VARCHAR(8),
  category          VARCHAR(30),
  moisture_level    VARCHAR(10),
  fat_level         VARCHAR(10),
  ph_category       VARCHAR(10),
  ph_min            FLOAT,
  ph_max            FLOAT,
  respiration_level VARCHAR(10),
  default_storage   VARCHAR(60),
  temp_min          FLOAT,
  temp_max          FLOAT,
  note_key          VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS packaging_materials (
  packaging_id        VARCHAR(10) PRIMARY KEY,
  material_name       VARCHAR(80) NOT NULL,
  oxygen_barrier      VARCHAR(15),
  otr_value           VARCHAR(40),
  moisture_barrier    VARCHAR(15),
  wvtr_value          VARCHAR(40),
  thickness           VARCHAR(40),
  sealability         VARCHAR(15),
  mechanical_strength VARCHAR(15),
  map_suitability     TINYINT(1),
  sustainability      VARCHAR(15),
  cost_level          VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS predictions (
  prediction_id         INT AUTO_INCREMENT PRIMARY KEY,
  food                  VARCHAR(50),
  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  shelf_life            INT,
  storage_type          VARCHAR(15),
  transportation        VARCHAR(15),
  temperature           FLOAT,
  recommended_packaging VARCHAR(80),
  method                VARCHAR(10)
);
