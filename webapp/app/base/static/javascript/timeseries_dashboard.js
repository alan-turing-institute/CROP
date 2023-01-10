let startDate = undefined;
let endDate = undefined;

function setDateRange(start, end) {
  startDate = start;
  endDate = end;
}

$("#reportrange").on("apply.daterangepicker", function (ev, picker) {
  setDateRange(picker.startDate, picker.endDate);
});

function getCheckedSensorIds() {
  const sensorCheckboxesDiv = document.getElementById("sensorCheckboxesDiv");
  const sensorIds = [];
  for (const childElement of sensorCheckboxesDiv.children) {
    const id = childElement.children[0].value;
    const checked = childElement.children[0].checked;
    if (checked) sensorIds.push(id);
  }
  return sensorIds;
}

function getSelectedSensorTypeStr() {
  const sensorTypeSelector = document.getElementById("sensorTypeSelector");
  const sensorType = sensorTypeSelector.value;
  const sensorTypeStr = encodeURIComponent(sensorType);
  return sensorTypeStr;
}

function changeSensorType() {
  const sensorTypeStr = getSelectedSensorTypeStr();
  const url = "/dashboards/timeseries_dashboard";
  const params = "sensorType=" + sensorTypeStr;
  location.replace(url + "?" + params);
}

function requestTimeSeries(download) {
  const sensorIds = getCheckedSensorIds();
  if (sensorIds === undefined || sensorIds.length === 0) {
    alert("Please select sensors to plot/download data for.");
    return null;
  }
  if (startDate === undefined || endDate === undefined) {
    alert("Please set start and end date.");
    return null;
  }

  const startStr = encodeURIComponent(startDate.format("YYYYMMDD"));
  const endStr = encodeURIComponent(endDate.format("YYYYMMDD"));
  const idsStr = encodeURIComponent(sensorIds);
  const sensorTypeStr = getSelectedSensorTypeStr();
  const url = "/dashboards/timeseries_dashboard";
  const params =
    "startDate=" +
    startStr +
    "&endDate=" +
    endStr +
    "&sensorIds=" +
    idsStr +
    "&sensorType=" +
    sensorTypeStr;
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
      y: {
        display: true,
        title: {
          display: true,
          font: { size: 18 },
        },
      },
      x: {
        type: "time",
        time: {
          displayFormats: {
            hour: "DD MMM hA",
          },
        },
        ticks: {
          maxTicksLimit: 6,
          includeBounds: false,
        },
      },
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

function makePlot(data, allSensors, yDataName, yLabel, canvasName) {
  const datasets = [];
  const sensorIds = Object.keys(data);
  const numSensors = sensorIds.length;
  for (let i = 0; i < numSensors; i++) {
    const sensorId = sensorIds[i];
    let label = sensorId;
    if (allSensors[sensorId] && allSensors[sensorId].aranet_code) {
      label = allSensors[sensorId].aranet_code;
    }
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
      label: label,
      data: data[sensorId].map((row) => {
        return { x: row["timestamp"], y: row[yDataName] };
      }),
      pointRadius: pointRadius,
      borderWidth: borderWidth,
      borderColor: colour,
      fill: true,
    });
  }
  const config = JSON.parse(JSON.stringify(plotConfigTemplate)); // Make a copy
  config.options.scales.y.title.text = yLabel;
  config.data = { datasets: datasets };
  const ctx = document.getElementById(canvasName);
  new Chart(ctx, config);
}
