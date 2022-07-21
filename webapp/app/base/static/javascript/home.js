function check_data(data) {
  if (Object.keys(data).length === 0 && data.constructor === Object) {
    console.warn("dataset is empty");
  } else console.log("its good data", data);
}

function set_hourly_values(hourly_data_json) {
  let tempFF = hourly_data_json[1]["temperature"];
  document.getElementById("tempFF").innerHTML = tempFF;
  let tempFM = hourly_data_json[2]["temperature"];
  document.getElementById("tempFM").innerHTML = tempFM;
  let tempFB = hourly_data_json[0]["temperature"];
  document.getElementById("tempFB").innerHTML = tempFB;
  let tempPR = hourly_data_json[3]["temperature"];
  document.getElementById("tempPR").innerHTML = tempPR;
  let tempRD = hourly_data_json[4]["temperature"];
  document.getElementById("tempRD").innerHTML = tempRD;

  let humFF = hourly_data_json[1]["humidity"];
  document.getElementById("humFF").innerHTML = humFF;
  let humFM = hourly_data_json[2]["humidity"];
  document.getElementById("humFM").innerHTML = humFM;
  let humFB = hourly_data_json[0]["humidity"];
  document.getElementById("humFB").innerHTML = humFB;
  let humPR = hourly_data_json[3]["humidity"];
  document.getElementById("humPR").innerHTML = humPR;
  let humRD = hourly_data_json[4]["humidity"];
  document.getElementById("humRD").innerHTML = humRD;
}

function time_series_charts(
  json_data,
  series,
  limits,
  trh_measure,
  y_label,
  canvasname
) {
  const data = {
    datasets: series.map((item) => {
      const temps = json_data[item.id].map((row) => row[trh_measure]);
      const dates = json_data[item.id].map((row) => row["timestamp"]);
      return {
        label: item.label,
        data: dictionary_scatter(dates, temps),
        borderColor: item.color,
        pointRadius: 1,
        borderWidth: 1,
        fill: true,
      };
    }),
  };
  const config = {
    type: "line",
    data: data,
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
            text: y_label,
            font: { size: 18 },
          },
          suggestedMin: limits.min,
          suggestedMax: limits.max,
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
  const ctx = document.getElementById(canvasname);
  return new Chart(ctx, config);
}

function roundcharts(json_data, zoneid, canvasname, colouramp) {
  bin_ = [];
  cnt_ = [];
  for (j = 0; j < json_data[zoneid]["Values"].length; j++) {
    bin_.push(json_data[zoneid]["Values"][j]["bin"]);
    cnt_.push(parseFloat(json_data[zoneid]["Values"][j]["cnt"]));
  }

  const data_ = [];
  data_.push({
    label: [json_data[zoneid]["zone"]],
    data: cnt_,
    backgroundColor: colouramp,
  });

  const data = {
    labels: bin_,
    datasets: data_,
  };

  const config = {
    type: "doughnut",
    data: data,
    options: {
      plugins: {
        legend: {
          display: false,
        },
      },
      aspectRatio: 1.5,
    },
  };
  const ctx = document.getElementById(canvasname);
  new Chart(ctx, config);
}

function horizontal_charts(json_data, zoneid, canvasname, colouramp) {
  // iterates through zones (5)
  bin_ = [];
  cnt_ = [];
  for (j = 0; j < json_data[zoneid]["Values"].length; j++) {
    bin_.push(json_data[zoneid]["Values"][j]["bin"]);
    cnt_.push(parseFloat(json_data[zoneid]["Values"][j]["cnt"]));
  }

  const datasets_ = [];
  for (i = 0; i < bin_.length; i++) {
    datasets_.push({
      label: bin_[i],
      data: [cnt_[i]],
      backgroundColor: colouramp[i],
    });
  }

  const data = {
    labels: [json_data[zoneid]["zone"]],
    datasets: datasets_,
  };

  const config = {
    type: "horizontalBar",
    data: data,
    options: {
      legend: {
        display: false,
      },
      scales: {
        xAxes: [
          {
            stacked: true,
            display: false, // this will remove all the x-axis grid lines
          },
        ],
        yAxes: [
          {
            stacked: true,
            // display: true,
            position: "right",
          },
        ],
      },
      aspectRatio: 6.5,
      tooltips: {
        callbacks: {
          position: "average",
          title: function (tooltipItems, data) {
            return "";
          },
        },
      },
    },
  };

  // var ctx = document.getElementById('stackedbarchart'.concat(0));
  let ctx = document.getElementById(canvasname);
  new Chart(ctx, config);
}

function stratification_minmax(data, measure_name) {
  const min_temps = Object.values(data).map((x) =>
    Math.min(...x.map((row) => row[measure_name]))
  );
  const min_temp = Math.min(...min_temps);
  const max_temps = Object.values(data).map((x) =>
    Math.max(...x.map((row) => row[measure_name]))
  );
  const max_temp = Math.max(...max_temps);
  return {
    min: min_temp,
    max: max_temp,
  };
}

function create_charts(
  temperature_data,
  temperature_data_daily,
  humidity_data,
  humidity_data_daily,
  stratification,
  hourly_data
) {
  set_hourly_values(hourly_data);
  // blue to red, and grey for missing
  const colouramp_redbluegrey = [
    "rgba(63,103,126,1)",
    "rgba(27,196,121,1)",
    "rgba(137,214,11,1)",
    "rgba(207,19,10,1)",
    "rgba(200,200,200,1)",
  ];
  const colouramp_bluegrey = [
    "rgba(27,55,74,1)",
    "rgba(0,96,196,1)",
    "rgba(0,129,196,1)",
    "rgba(141,245,252,1)",
    "rgba(200,200,200,1)",
  ];

  // main farm
  let zone0_name = temperature_data[0]["zone"];
  document.getElementById("zone0_name").innerHTML = zone0_name;
  roundcharts(temperature_data, 0, "roundchart0", colouramp_redbluegrey);

  let zone1_name = temperature_data[1]["zone"];
  document.getElementById("zone1_name").innerHTML = zone1_name;
  roundcharts(temperature_data, 1, "roundchart1", colouramp_redbluegrey);

  let zone2_name = temperature_data[2]["zone"];
  document.getElementById("zone2_name").innerHTML = zone2_name;
  roundcharts(temperature_data, 2, "roundchart2", colouramp_redbluegrey);

  roundcharts(temperature_data_daily, 0, "roundchart10", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 1, "roundchart11", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 2, "roundchart12", colouramp_redbluegrey);

  roundcharts(humidity_data, 0, "roundchart5", colouramp_bluegrey);
  roundcharts(humidity_data, 1, "roundchart6", colouramp_bluegrey);
  roundcharts(humidity_data, 2, "roundchart7", colouramp_bluegrey);

  roundcharts(humidity_data_daily, 0, "roundchart15", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 1, "roundchart16", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 2, "roundchart17", colouramp_bluegrey);

  // Find out min and max values, to set the axis limits.
  const temperature_limits = stratification_minmax(
    stratification_json,
    "temperature"
  );
  const humidity_limits = stratification_minmax(
    stratification_json,
    "humidity"
  );
  // Sensor id locations:
  // 18: 16B1, 21: 1B2, 22: 29B2, 23: 16B4
  vertical_series = [
    { id: 23, color: "#ff0000", label: "Top" },
    { id: 18, color: "#3399ff", label: "Bottom" },
  ];
  horizontal_series = [
    { id: 22, color: "#ff0000", label: "Back farm" },
    { id: 21, color: "#3399ff", label: "Front farm" },
  ];
  const verticalTempStratChart = time_series_charts(
    stratification,
    vertical_series,
    temperature_limits,
    "temperature",
    "Temperature (°C)",
    "vertical_temp_stratification"
  );
  const horizontalTempStratChart = time_series_charts(
    stratification,
    horizontal_series,
    temperature_limits,
    "temperature",
    "Temperature (°C)",
    "horizontal_temp_stratification"
  );
  const verticalHumidityStratChart = time_series_charts(
    stratification,
    vertical_series,
    humidity_limits,
    "humidity",
    "Humidity (%)",
    "vertical_humidity_stratification"
  );
  const horizontalHumidityStratChart = time_series_charts(
    stratification,
    horizontal_series,
    humidity_limits,
    "humidity",
    "Humidity (%)",
    "horizontal_humidity_stratification"
  );
  createStratificationZoomListeners([
    verticalTempStratChart,
    verticalHumidityStratChart,
    horizontalTempStratChart,
    horizontalHumidityStratChart,
  ]);

  // Propagation
  let zone3_name = temperature_data[3]["zone"];
  document.getElementById("zone3_name").innerHTML = zone3_name;
  roundcharts(temperature_data, 3, "roundchart3", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 3, "roundchart13", colouramp_redbluegrey);

  roundcharts(humidity_data, 3, "roundchart8", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 3, "roundchart18", colouramp_bluegrey);

  // R&D
  let zone4_name = temperature_data[4]["zone"];
  document.getElementById("zone4_name").innerHTML = zone4_name;
  roundcharts(temperature_data, 4, "roundchart4", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 4, "roundchart14", colouramp_redbluegrey);

  roundcharts(humidity_data, 4, "roundchart9", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 4, "roundchart19", colouramp_bluegrey);
}

function setMinTime(daysFromNow, charts) {
  const minTime = moment().subtract(daysFromNow, "days");
  for (chart of charts) {
    chart.options.scales.x.min = minTime;
    chart.update();
  }
}

function createStratificationZoomListeners(charts) {
  const vertTimeRange = document.getElementById("vertTimeRange");
  const horzTimeRange = document.getElementById("horzTimeRange");
  const vertTimeNumber = document.getElementById("vertTimeNumber");
  const horzTimeNumber = document.getElementById("horzTimeNumber");

  function onChangeMinTime(daysFromNow) {
    setMinTime(daysFromNow, charts);
    horzTimeRange.value = daysFromNow;
    vertTimeRange.value = daysFromNow;
    horzTimeNumber.value = daysFromNow;
    vertTimeNumber.value = daysFromNow;
  }

  vertTimeRange.oninput = (e) => onChangeMinTime(e.target.value);
  horzTimeRange.oninput = (e) => onChangeMinTime(e.target.value);
  vertTimeNumber.onchange = (e) => onChangeMinTime(e.target.value);
  horzTimeNumber.onchange = (e) => onChangeMinTime(e.target.value);

  // To set the initial values when the page is first loaded.
  onChangeMinTime(vertTimeRange.value);
}
