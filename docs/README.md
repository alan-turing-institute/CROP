# Infrastructure

A schematic representation of the CROP infrastructure:
![](infrastructure.png)
Image is created using draw.io, source file: `infrastructure.drawio`


- **(1)** (*Outside action*) Sensor data is uploaded to the Azure storage account.

  We recommend that this should be done using the `utils/upload_sensor_data` script.

  It is possible to upload (access) the data in the storage account using other ways, such as `Storage explorer`. However, it is less secure, especially if the person is not familiar with the tools, and should be avoided.

- **(2)** (*Triggered*) Data ingress

  Once a new data file is uploaded to one of the blob storage containers with name ending with "rawdata" (e.g. advantixrawdata), it will be automatically processed by the system (via one of the Function Apps).

  The data ingress process first reads in the uploaded file and checks it for correctness, i.e. checks for missing values, makes sure that values are within specified limits, etc. If an error is identified during the checks, data ingress process is stopped and action **(4)** is triggered.

  Once the data from the file has been processed, the uploaded file will automatically be moved from a `___rawdata` container to a `___processed` container, where `___` is the type of a sensor.

- **(4)** (*Triggered*) Email notification

  If an error occurs during the data ingress process, an automatic email will be generated and sent to specified email addresses.

  Note: free plan allows sending 25’000 emails per month.
