SELECT DISTINCT sensors.name, zensie_trh_data.temperature,zensie_trh_data.timestamp
FROM sensors, zensie_trh_data
WHERE sensors.id = zensie_trh_data.sensor_id
AND sensors.id = 18
AND zensie_trh_data.timestamp >= '2021-04-26 00:00:10'
AND zensie_trh_data.timestamp < '2021-04-26 16:00:10'
order by zensie_trh_data.timestamp asc

-- https://api.30mhz.com/api/stats/check/i-876a4911-8557-11ea-81a1-ab96f62e46e1/from/2021-04-26T00:00:31Z/until/2021-04-26T16:00:31Z?statisticType=averages&intervalSize=10m