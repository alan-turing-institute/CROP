function setScenario(ventilationRate, numDehumidifiers, lightingShift, chart) {
  chart.options.scales.x.min = minTime;
  chart.update();
}

function createSliderListeners(charts) {
  const ventilationRate = document.getElementById("ventilationRate");
  const numDehumidifiers = document.getElementById("numDehumidifiers");
  const lightingShift = document.getElementById("lightingShift");

  function onChangeSlider(value) {
    setValuesFromSlider(
      ventilationRate.value,
      numDehumidifiers.value,
      lightingShift.value,
      charts
    );
  }

  ventilationRate.oninput = (e) => onChangeSlider(e.target.value);
  numDehumidifiers.oninput = (e) => onChangeSlider(e.target.value);
  lightingShift.onchange = (e) => onChangeSlider(e.target.value);
}

function findInJson(ges_json, measureName) {
  // pick out rows from a list, based on measure name and/or scenario type
  const result = ges_json.find((obj) => {
    return obj.measure_name == measureName;
  });
  return result;
}

function plot(
  top_json,
  mid_json,
  bot_json,
  sce_json,
  trh_json,
  trh_measure,
  canvasname,
  y_label,
  show_legend,
  scenario_name
) {
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

  //    myChart.update();
}

function create_charts(ges_json, trh_json, canvasname) {
  const temperaturePlot = plot();
  createSliderListeners([temperaturePlot, humidityPlot]);
}
