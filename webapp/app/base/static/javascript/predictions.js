function plot(
  top_json,
  mid_json,
  bot_json,
  sce_json,
  zensie_json,
  zensie_measure,
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

  zensie_values = [];
  zensie_time = [];

  for (let i = 0; i < zensie_json.length; i++) {
    if (zensie_json[i]["sensor_id"] == top_json["sensor_id"]) {
      for (ii = 0; ii < zensie_json[i]["Values"].length; ii++) {
        zensie_values.push(
          parseFloat(zensie_json[i]["Values"][ii][zensie_measure])
        );
        let date_z = new Date(zensie_json[i]["Values"][ii]["timestamp"]);
        zensie_time.push(date_z);
      }
    }
  }

  const mid_scatter = dictionary_scatter(times_mid, values_mid);
  const top_scatter = dictionary_scatter(times_top, values_top);
  const bot_scatter = dictionary_scatter(times_bot, values_bot);
  const sce_scatter = dictionary_scatter(times_sce, values_sce);
  const zensie_scatter = dictionary_scatter(zensie_time, zensie_values);

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
        label: "Zensie",
        data: zensie_scatter,
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
      legend: {
        display: show_legend,
        position: "top",
      },
      scales: {
        yAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: y_label,
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
  let ctx = document.getElementById(canvasname);
  let myChart = new Chart(ctx, config);
  myChart.update();
}
