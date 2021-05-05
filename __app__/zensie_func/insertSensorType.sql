-- Alter table description to take more characters
ALTER TABLE sensor_types
Alter COLUMN description type CHARACTER VARYING(200)
Alter COLUMN data type CHARACTER VARYING(200)

ALTER TABLE sensor_types
Alter COLUMN data type CHARACTER VARYING(200)

-- Insert rows into table 'sensor_types'
INSERT INTO sensor_types
( -- columns to insert data into
 sensor_type, source, origin, frequency, data, description, time_created
)
VALUES
( -- first row: values for the columns in the list above
 '30MHz Weather', 
 '30MHz Zensie',  
 'Zensie API', 
 '60 mins', 
 'temperature,rain_probability,relative_humidity, rain, radiation, wind_speed,air_pressure,wind_direction',
 'https://api.30mhz.com/api/stats/check/i-b9bf5432-9436-11ea-b286-79ffe41fb933/from/YYYY-MM-DDTHH:MM:SSZ/until/YYYY-MM-DDTHH:MM:SSZ?statisticType=averages&intervalSize=60m',
 '2021-05-04 00:00:00.00'
)
-- add more rows here

-- Insert rows into table 'TableName'
INSERT INTO sensors
( -- columns to insert data into
 type_id, device_id, name
)
VALUES
( -- first row: values for the columns in the list above
 11, 'i-b9bf5432-9436-11ea-b286-79ffe41fb933', 'i_weathers'
)
-- add more rows here


ALTER TABLE iweather
ADD COLUMN sensor_id INTEGER NOT NULL DEFAULT 47,
RENAME COLUMN time_collected to timestamp,
ADD time_created TIMESTAMP NULL,
ADD time_updated TIMESTAMP NULL;  