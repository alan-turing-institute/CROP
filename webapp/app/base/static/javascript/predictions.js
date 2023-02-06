function findInJson(
  ges_json,
  measureName,
  scenarioType = "ScenarioType.Test",
  ventilationRate = null,
  numDehumidifiers = null,
  lightingShift = null
) {
  // pick out rows from a list, based on measure name and/or scenario type
  const result = ges_json.find((obj) => {
    if (scenarioType == "ScenarioType.BAU") {
      return (
        obj.measure_name == measureName && obj.scenario_type == scenarioType
      );
    } else {
      return (
        obj.measure_name == measureName &&
        obj.scenario_type == scenarioType &&
        obj.ventilation_rate == ventilationRate &&
        obj.num_dehumidifiers == numDehumidifiers &&
        obj.lighting_shift == lightingShift
      );
    }
  });
  return result;
}

function setScenario(
  ges_json,
  measureName,
  ventilationRate,
  numDehumidifiers,
  lightingShift,
  chart
) {
  const scenarioName =
    ventilationRate.toString() +
    " ACH, " +
    numDehumidifiers.toString() +
    " DH, " +
    lightingShift.toString() +
    " hours";

  const sce_json = findInJson(
    ges_json,
    measureName,
    "ScenarioType.Test",
    ventilationRate,
    numDehumidifiers,
    lightingShift
  );
  let values_sce;
  let times_sce;
  if (sce_json != null) {
    values_sce = sce_json["Values"].map((e) =>
      parseFloat(e["prediction_value"])
    );
    times_sce = sce_json["Values"].map((e) => new Date(e["timestamp"]));
  } else {
    values_sce = [];
    times_sce = [];
  }
  const sce_scatter = dictionary_scatter(times_sce, values_sce);
  chart.data.datasets[4] = {
    label: scenarioName,
    data: sce_scatter,
    borderColor: "#8eb0ee",
    fill: false,
    borderDash: [3],
    pointRadius: 1,
    showLine: true,
  };

  chart.update();
}

function createSliderListeners(ges_json, charts) {
  const ventilationRate = document.getElementById("ventilationRate");
  const numDehumidifiers = document.getElementById("numDehumidifiers");
  const lightingShift = document.getElementById("lightingShift");

  function onChangeSlider() {
    //update temperature plot
    setScenario(
      ges_json,
      "Mean Temperature (Degree Celcius)",
      ventilationRate.value,
      numDehumidifiers.value,
      lightingShift.value,
      charts[0]
    );
    //update humidity plot
    setScenario(
      ges_json,
      "Mean Relative Humidity (Percent)",
      ventilationRate.value,
      numDehumidifiers.value,
      lightingShift.value,
      charts[1]
    );
  }

  ventilationRate.oninput = (e) => onChangeSlider();
  numDehumidifiers.oninput = (e) => onChangeSlider();
  lightingShift.oninput = (e) => onChangeSlider();
  onChangeSlider();
}

function plot(
  top_json,
  mid_json,
  bot_json,
  trh_json,
  trh_measure,
  canvasname,
  y_label,
  show_legend
) {
  // start with no scenario
  var scenario_name = "default";
  var sce_json = null;
  sort_by_numerical(top_json["Values"], "prediction_index");
  sort_by_numerical(mid_json["Values"], "prediction_index");
  sort_by_numerical(bot_json["Values"], "prediction_index");
  if (sce_json != null) {
    sort_by_numerical(sce_json["Values"], "prediction_index");
  }
  const values_top = top_json["Values"].map((e) =>
    parseFloat(e["prediction_value"])
  );
  const times_top = top_json["Values"].map((e) => new Date(e["timestamp"]));
  const values_mid = mid_json["Values"].map((e) =>
    parseFloat(e["prediction_value"])
  );
  const times_mid = mid_json["Values"].map((e) => new Date(e["timestamp"]));
  const values_bot = bot_json["Values"].map((e) =>
    parseFloat(e["prediction_value"])
  );
  const times_bot = bot_json["Values"].map((e) => new Date(e["timestamp"]));
  let values_sce;
  let times_sce;
  if (sce_json != null) {
    values_sce = sce_json["Values"].map((e) =>
      parseFloat(e["prediction_value"])
    );
    times_sce = sce_json["Values"].map((e) => new Date(e["timestamp"]));
  } else {
    values_sce = [];
    times_sce = [];
  }

  trh_values = [];
  trh_time = [];

  for (let i = 0; i < trh_json.length; i++) {
    if (trh_json[i]["sensor_id"] == top_json["sensor_id"]) {
      for (ii = 0; ii < trh_json[i]["Values"].length; ii++) {
        trh_values.push(parseFloat(trh_json[i]["Values"][ii][trh_measure]));
        const date_z = new Date(trh_json[i]["Values"][ii]["timestamp"]);
        trh_time.push(date_z);
      }
    }
  }

  const mid_scatter = dictionary_scatter(times_mid, values_mid);
  const top_scatter = dictionary_scatter(times_top, values_top);
  const bot_scatter = dictionary_scatter(times_bot, values_bot);
  const sce_scatter = dictionary_scatter(times_sce, values_sce);
  const trh_scatter = dictionary_scatter(trh_time, trh_values);

  const data = {
    label: "GES Prediction",
    datasets: [
      {
        label: "Upper bound",
        data: top_scatter,
        borderColor: "#ee978c",
        fill: false,
        borderDash: [1],
        pointRadius: 1,
        showLine: true,
      },
      {
        label: "Mean",
        data: mid_scatter,
        borderColor: "#ff0000",
        fill: "-1",
        borderDash: [2],
        pointRadius: 1.5,
        showLine: true,
      },
      {
        label: "Lower bound",
        data: bot_scatter,
        borderColor: "#ee978c",
        fill: "-1",
        borderDash: [1],
        pointRadius: 1,
        showLine: true,
      },
      {
        label: "Aranet reading",
        data: trh_scatter,
        borderColor: "#a0a0a0",
        fill: false,
        pointRadius: 1.5,
        showLine: true,
      },
    ],
  };
  if (sce_json != null) {
    data.datasets[4] = {
      label: scenario_name,
      data: sce_scatter,
      borderColor: "#8eb0ee",
      fill: false,
      borderDash: [3],
      pointRadius: 1,
      showLine: true,
    };
  }

  const config = {
    type: "scatter",
    data: data,
    options: {
      animation: {
        duration: 0,
      },
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: show_legend,
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
        },
        x: {
          type: "time",
          time: {
            displayFormats: {
              hour: "DD MMM hA",
            },
          },
          ticks: {
            maxTicksLimit: 13,
            includeBounds: false,
          },
        },
      },
    },
  };
  const ctx = document.getElementById(canvasname);
  return new Chart(ctx, config);
}

function create_charts(ges_json, trh_json, canvasname) {
  // temperature
  const topTempJson = findInJson(
    ges_json,
    "Upper Bound Temperature (Degree Celcius)",
    "ScenarioType.BAU"
  );
  const midTempJson = findInJson(
    ges_json,
    "Mean Temperature (Degree Celcius)",
    "ScenarioType.BAU"
  );
  const bottomTempJson = findInJson(
    ges_json,
    "Lower Bound Temperature (Degree Celcius)",
    "ScenarioType.BAU"
  );

  const temperaturePlot = plot(
    topTempJson,
    midTempJson,
    bottomTempJson,
    trh_json,
    "temperature",
    "ges_model_temperature",
    "Temperature (°C)",
    true
  );

  /// humidity
  const topHumidityJson = findInJson(
    ges_json,
    "Upper Bound Relative Humidity (Percent)",
    "ScenarioType.BAU"
  );
  const midHumidityJson = findInJson(
    ges_json,
    "Mean Relative Humidity (Percent)",
    "ScenarioType.BAU"
  );
  const bottomHumidityJson = findInJson(
    ges_json,
    "Lower Bound Relative Humidity (Percent)",
    "ScenarioType.BAU"
  );
  const humidityPlot = plot(
    topHumidityJson,
    midHumidityJson,
    bottomHumidityJson,
    trh_json,
    "humidity",
    "ges_model_humidity",
    "Relative humidity (%)",
    false
  );
  createSliderListeners(ges_json, [temperaturePlot, humidityPlot]);
}
