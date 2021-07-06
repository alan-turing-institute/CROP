DROP TABLE IF EXISTS model;
DROP TABLE IF EXISTS measure;
DROP TABLE IF EXISTS prediction;

-- Model:
CREATE TABLE model (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  author VARCHAR(100)
);

INSERT INTO model(model_name, author)
VALUES('arima', 'Melanie Singh')

-- Measure:
CREATE TABLE measure (
  id SERIAL PRIMARY KEY,
  measure_name VARCHAR(100) NOT NULL,
  description VARCHAR(100)
);

INSERT INTO measure(measure_name)
VALUES('Mean Temperature (Degree Celcius)')

INSERT INTO measure(measure_name)
VALUES('Upper Bound Temperature (Degree Celcius)')

INSERT INTO measure(measure_name)
VALUES('Lower Bound Temperature (Degree Celcius)')

CREATE TABLE run_output (
  id SERIAL PRIMARY KEY,
  sensor_id INTEGER NOT NULL,
  measure_id INTEGER NOT NULL,
  timestamp timestamp default current_timestamp NOT NULL
);

CREATE TABLE prediction (
  id SERIAL PRIMARY KEY,
  prediction_value FLOAT NOT NULL,
  unit VARCHAR(100) NOT NULL
);
