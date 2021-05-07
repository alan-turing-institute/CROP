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
WHERE timestamp>='2021-05-05 01:00:00' 
AND timestamp<='2021-05-05 05:00:00' 
AND sensor_id=17
ORDER BY timestamp ASC
LIMIT 8

\COPY utc_energy_data (timestamp, electricity_consumption) FROM '/Users/myong/Downloads/energy.csv' WITH CSV HEADER;

select * from utc_energy_data                                                                                
WHERE timestamp>='2021-05-05 01:00:00'                                                                                
AND timestamp<='2021-05-05 05:00:00'                                                                                  
AND sensor_id=17                                                                                                      
ORDER BY timestamp ASC                                                                                                
LIMIT 8;

|      timestamp      | electricity_consumption |    time_created     | time_updated | sensor_id |  id   
---------------------|-------------------------|---------------------|--------------|-----------|-------
 2021-05-05 01:00:00 |                   27.32 | 2021-05-06 21:00:00 |              |        17 | 17906
 2021-05-05 01:30:00 |                   27.25 | 2021-05-06 21:00:00 |              |        17 | 17907
 2021-05-05 02:00:00 |                   27.32 | 2021-05-06 21:00:00 |              |        17 | 17908
 2021-05-05 02:30:00 |                   27.16 | 2021-05-06 21:00:00 |              |        17 | 17909
 2021-05-05 03:00:00 |                   27.14 | 2021-05-06 21:00:00 |              |        17 | 17910
 2021-05-05 03:30:00 |                   27.23 | 2021-05-06 21:00:00 |              |        17 | 17911
 2021-05-05 04:00:00 |                   27.14 | 2021-05-06 21:00:00 |              |        17 | 17912
 2021-05-05 04:30:00 |                   27.06 | 2021-05-06 21:00:00 |              |        17 | 17913
