select * from energy_data where timestamp>='2020-04-27 00:00:00' AND timestamp <= '2020-04-27 01:00:00';

select * from energy_data where (timestamp='2020-04-27 00:00:00');

select * from energy_data where timestamp='2020-04-27 00:30:00';

select * from energy_data 
WHERE timestamp>'2020-10-25 00:00:00' 
AND sensor_id=17
limit 4;

UPDATE energy_data
SET electricity_consumption = 29.77
where id=17714

UPDATE energy_data
SET electricity_consumption = 29.56
where id=17763

select * from energy_data
WHERE timestamp>='2020-10-25 00:00:00' 
AND sensor_id=17
ORDER BY timestamp ASC
LIMIT 8

select * from energy_data
WHERE sensor_id=17
ORDER BY timestamp ASC
LIMIT 8

select * from energy_data
WHERE timestamp>='2021-03-28 00:00:00' 
AND sensor_id=17
ORDER BY timestamp ASC
LIMIT 8