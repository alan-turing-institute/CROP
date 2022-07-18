SELECT DISTINCT sensors.name, aranet_trh_data.temperature,aranet_trh_data.timestamp
FROM sensors, aranet_trh_data
WHERE sensors.id = aranet_trh_data.sensor_id
AND sensors.id = 18
AND aranet_trh_data.timestamp >= '2021-04-26 00:00:10'
AND aranet_trh_data.timestamp < '2021-04-26 16:00:10'
order by aranet_trh_data.timestamp asc
