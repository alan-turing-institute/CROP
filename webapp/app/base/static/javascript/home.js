function check_data(data) {
  if (Object.keys(data).length === 0 && data.constructor === Object) {
    console.warn("dataset is empty");
  } else console.log("its good data", data);
}

function set_meanminmax_values(hourly_data, minmax_data) {
  const numDecimals = 1;
  for (region of ["FrontFarm", "MidFarm", "BackFarm", "Propagation", "R&D"]) {
    for (metric of ["temperature", "humidity", "vpd"]) {
      const mean_element = document.getElementById(`${metric}_${region}`);
      const min_element = document.getElementById(`${metric}_${region}_min`);
      const max_element = document.getElementById(`${metric}_${region}_max`);

      if (hourly_data.length > 0) {
        const hourly = hourly_data.find((s) => s["region"] == region);
        const mean = hourly[metric];
        if (mean != undefined) {
          mean_element.innerHTML = mean.toFixed(numDecimals);
        }
      } else {
        mean_element.innerHTML = "N/A";
      }

      if (hourly_data.length > 0) {
        const min_obj = minmax_data.find(
          (s) =>
            s["region"] == region &&
            s["variable_0"] == metric &&
            s["variable_1"] == "min"
        );
        const max_obj = minmax_data.find(
          (s) =>
            s["region"] == region &&
            s["variable_0"] == metric &&
            s["variable_1"] == "max"
        );
        const min_value = min_obj["value"];
        const max_value = max_obj["value"];
        const min_timestamp = new Date(min_obj["timestamp"]);
        const max_timestamp = new Date(max_obj["timestamp"]);
        if (min_value != undefined) {
          min_element.innerHTML = min_value.toFixed(numDecimals);
          min_element.title = `6h min. Recorded at ${min_timestamp}`;
        }
        if (max_value != undefined) {
          max_element.innerHTML = max_value.toFixed(numDecimals);
          max_element.title = `6h max. Recorded at ${max_timestamp}`;
        }
      } else {
        min_element.innerHTML = "N/A";
        max_element.innerHTML = "N/A";
      }
    }
  }
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

function roundcharts(json_data, regionid, canvasname, colouramp) {
  bin_ = [];
  cnt_ = [];
  try {
    for (j = 0; j < json_data[regionid]["Values"].length; j++) {
      bin_.push(json_data[regionid]["Values"][j]["bin"]);
      cnt_.push(parseFloat(json_data[regionid]["Values"][j]["cnt"]));
    }
  } catch (e) {
    if (e instanceof TypeError) {
      console.log(`In roundcharts, got ${e}`);
      return null;
    } else {
      throw e;
    }
  }

  const data_ = [];
  data_.push({
    label: [json_data[regionid]["region"]],
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

function horizontal_charts(json_data, regionid, canvasname, colouramp) {
  // iterates through regions (5)
  bin_ = [];
  cnt_ = [];
  for (j = 0; j < json_data[regionid]["Values"].length; j++) {
    bin_.push(json_data[regionid]["Values"][j]["bin"]);
    cnt_.push(parseFloat(json_data[regionid]["Values"][j]["cnt"]));
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
    labels: [json_data[regionid]["region"]],
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
  vpd_data,
  vpd_data_daily,
  stratification,
  hourly_data,
  recent_minmax_data
) {
  set_meanminmax_values(hourly_data, recent_minmax_data);
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
  let region0_name = temperature_data[0]["region"];
  document.getElementById("region0_name").innerHTML = region0_name;
  roundcharts(temperature_data, 0, "roundchart0", colouramp_redbluegrey);

  let region1_name = temperature_data[1]["region"];
  document.getElementById("region1_name").innerHTML = region1_name;
  roundcharts(temperature_data, 1, "roundchart1", colouramp_redbluegrey);

  let region2_name = temperature_data[2]["region"];
  document.getElementById("region2_name").innerHTML = region2_name;
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

  roundcharts(vpd_data, 0, "vpd_roundchart0", colouramp_bluegrey);
  roundcharts(vpd_data, 1, "vpd_roundchart1", colouramp_bluegrey);
  roundcharts(vpd_data, 2, "vpd_roundchart2", colouramp_bluegrey);

  roundcharts(vpd_data_daily, 0, "vpd_roundchart10", colouramp_bluegrey);
  roundcharts(vpd_data_daily, 1, "vpd_roundchart11", colouramp_bluegrey);
  roundcharts(vpd_data_daily, 2, "vpd_roundchart12", colouramp_bluegrey);

  // Find out min and max values, to set the axis limits.
  const temperature_limits = stratification_minmax(
    stratification_json,
    "temperature"
  );
  const humidity_limits = stratification_minmax(
    stratification_json,
    "humidity"
  );
  const vpd_limits = stratification_minmax(stratification_json, "vpd");
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
  const verticalVpdStratChart = time_series_charts(
    stratification,
    vertical_series,
    vpd_limits,
    "vpd",
    "VPD (Pa)",
    "vertical_vpd_stratification"
  );
  const horizontalVpdStratChart = time_series_charts(
    stratification,
    horizontal_series,
    vpd_limits,
    "vpd",
    "VPD (Pa)",
    "horizontal_vpd_stratification"
  );
  createStratificationZoomListeners([
    verticalTempStratChart,
    verticalHumidityStratChart,
    verticalVpdStratChart,
    horizontalTempStratChart,
    horizontalHumidityStratChart,
    horizontalVpdStratChart,
  ]);

  // Propagation
  let region3_name = temperature_data[3]["region"];
  document.getElementById("region3_name").innerHTML = region3_name;
  roundcharts(temperature_data, 3, "roundchart3", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 3, "roundchart13", colouramp_redbluegrey);

  roundcharts(humidity_data, 3, "roundchart8", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 3, "roundchart18", colouramp_bluegrey);

  roundcharts(vpd_data, 3, "vpd_roundchart3", colouramp_bluegrey);
  roundcharts(vpd_data_daily, 3, "vpd_roundchart13", colouramp_bluegrey);

  // R&D
  let region4_name = temperature_data[4]["region"];
  document.getElementById("region4_name").innerHTML = region4_name;
  roundcharts(temperature_data, 4, "roundchart4", colouramp_redbluegrey);
  roundcharts(temperature_data_daily, 4, "roundchart14", colouramp_redbluegrey);

  roundcharts(humidity_data, 4, "roundchart9", colouramp_bluegrey);
  roundcharts(humidity_data_daily, 4, "roundchart19", colouramp_bluegrey);

  roundcharts(vpd_data, 4, "vpd_roundchart4", colouramp_bluegrey);
  roundcharts(vpd_data_daily, 4, "vpd_roundchart14", colouramp_bluegrey);
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

function setUpWarningTypeCheckboxListeners() {
  // Set up event listeners, so that when a checkbox for a warning type is
  // checked/unchecked, the warnings of that type are made visible/hidden.
  const warningsUl = document.getElementById("warningsUl");
  const checkboxesDiv = document.getElementById("warningTypeCheckboxesDiv");
  // Pick the <input> element from each checkbox div.
  const checkboxes = [...checkboxesDiv.children].map(
    (childDiv) => childDiv.childNodes[1]
  );
  const allCheckbox = document.getElementById("warning_type_checkbox_all");

  function onChange(e) {
    const checkbox = e.target;
    const value = checkbox.value;
    const checked = checkbox.checked;
    // Note that setting the checked status of a checkbox does not trigger an onChange
    // event. Which is good, otherwise the bit ~20 lines below would cause an infinite
    // loop.
    if (!checked) allCheckbox.checked = false;
    // Find all the warnings that are of this type. They can be identified by having a
    // particular CSS class. Set their display either to "none" to hide them or to the
    // browser default, as appropriate.
    warningsUl.querySelectorAll(".warning_" + value).forEach((warning) => {
      warning.style.display = checked ? "revert" : "none";
    });
  }

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", onChange);
    // Call the onChange function once to set the warning visibilities to their correct
    // initial values.
    onChange({ target: checkbox });
  });

  allCheckbox.addEventListener("change", () => {
    checkboxes.forEach((checkbox) => {
      checkbox.checked = allCheckbox.checked;
      onChange({ target: checkbox });
    });
  });
}
