DROP TABLE IF EXISTS model;
DROP TABLE IF EXISTS model_measure;
DROP TABLE IF EXISTS model_prediction;
DROP TABLE IF EXISTS model_run;

-- --Model:
CREATE TABLE model (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  author VARCHAR(100)
);

INSERT INTO model(model_name, author)
VALUES('arima', 'Melanie Singh');

-- Measure:
CREATE TABLE model_measure (
  id SERIAL PRIMARY KEY,
  measure_name VARCHAR(100) NOT NULL,
  measure_description VARCHAR(100)
);

INSERT INTO model_measure(measure_name)
VALUES('Mean Temperature (Degree Celcius)');

INSERT INTO model_measure(measure_name)
VALUES('Upper Bound Temperature (Degree Celcius)');

INSERT INTO model_measure(measure_name)
VALUES('Lower Bound Temperature (Degree Celcius)');

-- Record run:
CREATE TABLE model_run (
  id SERIAL PRIMARY KEY,
  sensor_id INTEGER NOT NULL,
  measure_id INTEGER NOT NULL,
  time_created timestamp default current_timestamp NOT NULL
);

INSERT INTO model_run(sensor_id, measure_id)
VALUES(27, 0);

-- Prdiction value:
CREATE TABLE model_prediction (
  id SERIAL PRIMARY KEY,
  prediction_value FLOAT NOT NULL
);

INSERT INTO model_prediction(prediction_value)
VALUES(15);
