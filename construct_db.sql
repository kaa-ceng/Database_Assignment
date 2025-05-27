
CREATE TABLE Country(
  Name VARCHAR(50) NOT NULL UNIQUE,
  Code VARCHAR(4) PRIMARY KEY,
  Capital VARCHAR(50),
  Area DECIMAL,
  Population DECIMAL
);

CREATE TABLE City(
  Name VARCHAR(50),
  Country VARCHAR(4) REFERENCES Country(Code),
  Population DECIMAL,
  Elevation DECIMAL,
  PRIMARY KEY (Name, Country)
);

CREATE TABLE Economy(
  Country VARCHAR(4) PRIMARY KEY REFERENCES Country(Code),
  GDP DECIMAL,
  Agriculture DECIMAL,
  Industry DECIMAL,
  Service DECIMAL,
  Inflation DECIMAL,
  Unemployment DECIMAL
);

CREATE TABLE Religion
(
  Country VARCHAR(4) REFERENCES Country(Code),
  Name VARCHAR(50),
  Percentage DECIMAL,
  PRIMARY KEY (Name, Country)
);

CREATE TABLE Spoken(
  Country VARCHAR(4) REFERENCES Country(Code),
  Language VARCHAR(50),
  Percentage DECIMAL,
  PRIMARY KEY (Country, Language)
);

CREATE TABLE Continent(
  Name VARCHAR(20) PRIMARY KEY,
  Area DECIMAL(10)
);


CREATE TABLE encompasses(
  Country VARCHAR(4) NOT NULL REFERENCES Country(Code),
  Continent VARCHAR(20) NOT NULL REFERENCES Continent(Name),
  Percentage DECIMAL,
  PRIMARY KEY (Country,Continent)
); 

CREATE TABLE AccessLevels (
    level_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    max_parallel_sessions INTEGER NOT NULL
);

CREATE TABLE Administrators (
    admin_id VARCHAR(50) PRIMARY KEY,
    password VARCHAR(100) NOT NULL,
    session_count INTEGER DEFAULT 0,
    level_id INTEGER NOT NULL,
    FOREIGN KEY (level_id) REFERENCES AccessLevels(level_id)
);

CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    current_query_count INTEGER DEFAULT 0 CHECK (current_query_count >= 0),
    max_query_limit INTEGER DEFAULT 10000 CHECK (max_query_limit = 10000)
);
