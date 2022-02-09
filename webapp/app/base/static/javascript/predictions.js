// Zip to arrays [x0, x1, x2, ...] and [y0, y1, y2, ...] into
// [{x: x0, y: 01}, {x: x1, y: y1}, {x: x2, y: y2}, ...]
// Used to gather data for plots into a format preferred by Chart.js
function dictionary_scatter(x , y) {
  value_array = []
  for (var j=0; j < y.length; j++) {
    const mydict = {x: x[j], y: y[j]}
    value_array.push(mydict)
  }
  return value_array
}


// Sort an array of objects by the field elname, which each object is assumed
// to have, and which is assumed to be a number. Operates in place.
function sort_by_numerical(arr, elname) {
  return arr.sort((e1, e2) => e1[elname] - e2[elname])
}

function plot(top_json, mid_json, bot_json, sce_json, zensie_json, zensie_measure, canvasname, y_label, show_legend, scenario_name) {
  sort_by_numerical(top_json["Values"], "prediction_index")
  sort_by_numerical(mid_json["Values"], "prediction_index")
  sort_by_numerical(bot_json["Values"], "prediction_index")
  if ( sce_json != null ) {
    sort_by_numerical(sce_json["Values"], "prediction_index")
  }
  const values_top = top_json["Values"].map((e) => parseFloat(e["prediction_value"]));
  const times_top = top_json["Values"].map((e) => new Date(e["timestamp"]));
  const values_mid = mid_json["Values"].map((e) => parseFloat(e["prediction_value"]));
  const times_mid = mid_json["Values"].map((e) => new Date(e["timestamp"]));
  const values_bot = bot_json["Values"].map((e) => parseFloat(e["prediction_value"]));
  const times_bot = bot_json["Values"].map((e) => new Date(e["timestamp"]));
  var values_sce, times_sce;
  if ( sce_json != null ) {
    values_sce = sce_json["Values"].map((e) => parseFloat(e["prediction_value"]));
    times_sce = sce_json["Values"].map((e) => new Date(e["timestamp"]));
  } else {
    values_sce = [];
    times_sce = [];
  }
      
  zensie_values = []
  zensie_time = []
  
  for (var i = 0; i < zensie_json.length; i++) {
    if (zensie_json[i]["sensor_id"] == top_json["sensor_id"]) {
      var sensor_id = zensie_json[i]["sensor_id"]
      for (ii = 0; ii < zensie_json[i]["Values"].length;ii++) {
        zensie_values.push(parseFloat(zensie_json[i]["Values"][ii][zensie_measure]))
        var date_z = new Date(zensie_json[i]["Values"][ii]["timestamp"])
        zensie_time.push(date_z)
      }
    }
  }

  const mid_scatter = dictionary_scatter(times_mid, values_mid)
  const top_scatter = dictionary_scatter(times_top, values_top)
  const bot_scatter = dictionary_scatter(times_bot, values_bot)
  const sce_scatter = dictionary_scatter(times_sce, values_sce)
  const zensie_scatter = dictionary_scatter(zensie_time, zensie_values)

  const data = {
    label: "GES Prediction",
    datasets: [
      {
        label: 'Upper bound',
        data: top_scatter,
        borderColor: "#ee978c",
        fill: false,
        borderDash: [1],
        pointRadius:1,
        showLine: true
        
      },
      {
        label: 'Mean',
        data: mid_scatter,
        borderColor: "#ff0000",
        fill: '-1',
        borderDash: [2],
        pointRadius:1.5,
        showLine: true
      },
      {
        label: 'Lower bound',
        data: bot_scatter,
        borderColor: "#ee978c",
        fill: '-1',
        borderDash: [1],
        pointRadius:1,
        showLine: true
      },
      {
        label: 'Zensie',
        data: zensie_scatter,
        borderColor: "#a0a0a0",
        fill: false,
        pointRadius:1.5,
        showLine: true
      },
    ],
  };
  if ( sce_json != null ) {
      data.datasets[4] = {
        label: scenario_name,
        data: sce_scatter,
        borderColor: "#8eb0ee",
        fill: false,
        borderDash: [3],
        pointRadius:1,
        showLine: true
      }
  }
 
  const config = {
    type: "scatter",
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      legend: {
        display: show_legend,
        position: "top"
      },
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: y_label,
            fontSize: 18,
          },
        }],
        xAxes: [{
          type: 'time'
        }]
      },
    }
  };
  var ctx = document.getElementById(canvasname);
  var myChart = new Chart(ctx, config);
  myChart.update();
}
