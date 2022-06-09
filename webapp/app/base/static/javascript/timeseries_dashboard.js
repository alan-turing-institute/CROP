let startDate = undefined;
let endDate = undefined;

function setDateRange(start, end) {
  startDate = start;
  endDate = end;
}

$("#reportrange").on("apply.daterangepicker", function (ev, picker) {
  setDateRange(picker.startDate, picker.endDate);
});

function requestTimeSeries(download) {
  const sensorIds = document.getElementById("sensorIdInput").value;
  if (sensorIds === undefined) {
    alert("Please give a list of sensor IDs.");
    return null;
  }
  if (startDate === undefined || endDate === undefined) {
    alert("Please set start and end date.");
    return null;
  }
  if (!/^\d[\d;, ]*$/.test(sensorIds)) {
    alert("Invalid list of sensor IDs.");
    return null;
  }
  const startStr = encodeURIComponent(startDate.format("YYYYMMDD"));
  const endStr = encodeURIComponent(endDate.format("YYYYMMDD"));
  const idsStr = encodeURIComponent(sensorIds);
  const url = "/dashboards/timeseries_dashboard";
  const params =
    "startDate=" + startStr + "&endDate=" + endStr + "&sensorIds=" + idsStr;
  if (download) {
    // A clunky way to trigger a download: Make a form that generates a POST request.
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url + "?" + params;
    document.body.appendChild(form);
    form.submit();
  } else {
    location.replace(url + "?" + params);
  }
}

const plotConfigTemplate = {
  type: "line",
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      yAxes: [
        {
          scaleLabel: {
            display: true,
            fontSize: 18,
          },
        },
      ],
      xAxes: [
        {
          type: "time",
        },
      ],
    },
  },
};

// blue to red
const colouramp_redblue = [
  "rgba(63,103,126,1)",
  "rgba(27,196,121,1)",
  "rgba(137,214,11,1)",
  "rgba(207,19,10,1)",
];
const colouramp_blue = [
  "rgba(27,55,74,1)",
  "rgba(0,96,196,1)",
  "rgba(0,129,196,1)",
  "rgba(141,245,252,1)",
];

function makePlot(data, yDataName, yLabel, canvasName) {
  const datasets = [];
  const sensorIds = Object.keys(data);
  const numSensors = sensorIds.length;
  for (let i = 0; i < numSensors; i++) {
    const sensorId = sensorIds[i];
    let colour = colouramp_redblue[Math.min(i, numSensors - 1)];
    let pointRadius = 1;
    let borderWidth = 1;
    // Make the line for mean look a bit different
    if (sensorId === "mean") {
      pointRadius = 0;
      borderWidth *= 4;
      colour = "#111111";
    }
    datasets.push({
      label: sensorId,
      data: data[sensorId].map((row) => {
        return { x: row["timestamp"], y: row[yDataName] };
      }),
      pointRadius: pointRadius,
      borderWidth: borderWidth,
      borderColor: colour,
    });
  }
  const config = JSON.parse(JSON.stringify(plotConfigTemplate)); // Make a copy
  config.options.scales.yAxes[0].scaleLabel.labelString = yLabel;
  config.data = { datasets: datasets };
  const ctx = document.getElementById(canvasName);
  new Chart(ctx, config);
}

function makePlots(data) {
  makePlot(data, "temperature", "Temperature", "temperatureCanvas");
  makePlot(data, "humidity", "Relative humidity", "humidityCanvas");
}
