-- DROP TABLE IF EXISTS model CASCADE;
-- DROP TABLE IF EXISTS model_measure CASCADE;
DROP TABLE IF EXISTS model_run CASCADE;
DROP TABLE IF EXISTS model_prediction CASCADE;

-- --Model:
CREATE TABLE model (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  author VARCHAR(100)
);

-- INSERT INTO model(model_name, author)
-- VALUES('arima', 'Melanie Singh');

-- INSERT INTO model(model_name, author)                            
-- values ('Bayesian Structural Time Series (BSTS)', 'Melanie Singh')

-- -- Measure:
CREATE TABLE model_measure (
  id SERIAL PRIMARY KEY,
  measure_name VARCHAR(100) NOT NULL,
  measure_description VARCHAR(100)
);

-- INSERT INTO model_measure(measure_name)
-- VALUES('Mean Temperature (Degree Celcius)');

-- INSERT INTO model_measure(measure_name)
-- VALUES('Upper Bound Temperature (Degree Celcius)');

-- INSERT INTO model_measure(measure_name)
-- VALUES('Lower Bound Temperature (Degree Celcius)');

-- insert into model_measure (measure_name) 
-- values ('Median Temperature (Degree Celcius)');

-- Record run:
CREATE TABLE model_run (
  id SERIAL PRIMARY KEY,
  sensor_id INTEGER REFERENCES sensors(id),
  model_id INTEGER REFERENCES model(id),
  time_forecast timestamp NOT NULL,
  time_created timestamp default current_timestamp NOT NULL
);

-- insert into model

CREATE TABLE model_product (
  id SERIAL PRIMARY KEY,
  run_id INTEGER REFERENCES model_run(id),
  measure_id INTEGER REFERENCES model_measure(id)
);


-- INSERT INTO model_product (sensor_id, measure_id, model_id)
-- VALUES(18, 1, 1);

-- Prdiction value:
CREATE TABLE model_value (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES model_product(id),
  prediction_value FLOAT NOT NULL,
  prediction_index INTEGER NOT NULL
);

-- INSERT INTO model_prediction(run_id,prediction_value, prediction_index)
-- VALUES(1, 11, 1),
-- (1, 12, 2),
-- (1, 13, 3),
-- (1, 14, 4),
-- (1, 15, 5),
-- (1, 16, 6),
-- (1, 17, 7),
-- (1, 18, 8),
-- (1, 19, 9),
-- (1, 20, 10),
-- (1, 21, 11),
-- (1, 22, 12);

CREATE TABLE parameter (
  id SERIAL PRIMARY KEY,
  model_id INTEGER REFERENCES model(id),
  parameter_name VARCHAR(100) NOT NULL,
);

INSERT INTO parameter(model_id, parameter_name)
VALUES(2, 'length_out'),
(2, 'ACH'),
(2, 'IAS');

CREATE TABLE model_parameter (
  id SERIAL PRIMARY KEY,
  time_created timestamp default current_timestamp NOT NULL,
  parameter_id INTEGER REFERENCES parameter(id),
  parameter_index INTEGER NOT NULL,
  parameter_value FLOAT NOT NULL
);

INSERT INTO model_parameter(parameter_id, parameter_value)
VALUES (2, 0, 0.4594613726254301), 
(2, 1, 0.763604572422916), 
(2, 2, 0.7340651592924317), 
(2, 3, 0.7047730309779485), 
(2, 4, 0.4595117250921914)

SELECT model.id, model.model_name, model_run.sensor_id, model_run.time_forecast, model_product.run_id, model_value.prediction_index, model_value.prediction_value 
FROM model, model_run, model_measure, model_product, model_value 
WHERE model.id =1 
AND model_run.model_id = model.id  
AND model_product.run_id = 133 
AND model_product.measure_id = model_measure.id 
AND model_value.product_id = model_product.id 

SELECT model.id, model.model_name, 
  model_run.id, model_run.sensor_id, model_run.time_forecast,
  model_product.id,
  model_value.product_id,
  model_value.prediction_value
FROM model, model_run, model_product, model_value, model_measure
WHERE model.id = 1 
  AND model_run.model_id = model.id 
  AND model_run.id=133
  AND model_product.measure_id=99
  AND model_value.product_id=model_product.id 
LIMIT 5

SELECT model.id as model_id, model.model_name, 
  model_run.id, model_run.sensor_id, model_run.time_forecast,
  model_product.id,
  model_value.product_id,
  model_value.prediction_value
FROM model, model_run, model_product, model_value, model_measure
WHERE model.id = 1 
  AND model_run.model_id = model.id 
  AND model_run.id=133
  AND model_value.product_id=model_product.id 
LIMIT 5

SELECT model.id as m_id, 
  model.model_name as m_name, 
  model_run.id as run, 
  model_run.sensor_id as sensor, 
  model_run.time_forecast as forecast,
  model_product.id as product,
  model_value.product_id as value_product,
  model_value.prediction_value as p_value,
  model_value.prediction_index as p_index,
  model_value.id as p_id,
  model_measure.measure_name
FROM model, model_run, model_product, model_value, model_measure
WHERE model.id = 1 
  AND model_run.model_id = model.id 
  AND model_run.id=133
  AND model_product.run_id = model_run.id
  AND model_product.measure_id = 1
  AND model_value.product_id = model_product.id
  AND model_measure.id = model_product.measure_id
ORDER BY model_value.prediction_index asc
