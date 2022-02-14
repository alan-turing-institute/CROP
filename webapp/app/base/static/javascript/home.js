function check_data(data) {
  if (Object.keys(data).length === 0 && data.constructor === Object) {
    console.warn('dataset is empty');
  } else console.log('its good data', data);
}

function set_hourly_values(hourly_data_json) {
  let tempFF = hourly_data_json[1]['temperature'];
  document.getElementById('tempFF').innerHTML = tempFF;
  let tempFM = hourly_data_json[2]['temperature'];
  document.getElementById('tempFM').innerHTML = tempFM;
  let tempFB = hourly_data_json[0]['temperature'];
  document.getElementById('tempFB').innerHTML = tempFB;
  let tempPR = hourly_data_json[3]['temperature'];
  document.getElementById('tempPR').innerHTML = tempPR;
  let tempRD = hourly_data_json[4]['temperature'];
  document.getElementById('tempRD').innerHTML = tempRD;

  let humFF = hourly_data_json[1]['humidity'];
  document.getElementById('humFF').innerHTML = humFF;
  let humFM = hourly_data_json[2]['humidity'];
  document.getElementById('humFM').innerHTML = humFM;
  let humFB = hourly_data_json[0]['humidity'];
  document.getElementById('humFB').innerHTML = humFB;
  let humPR = hourly_data_json[3]['humidity'];
  document.getElementById('humPR').innerHTML = humPR;
  let humRD = hourly_data_json[4]['humidity'];
  document.getElementById('humRD').innerHTML = humRD;
}

function time_series_charts(json_data, series, limits, canvasname) {
  const data = {
    datasets: series.map((item) => {
      const temps = json_data[item.id].map((row) => row['temperature']);
      const dates = json_data[item.id].map((row) => row['timestamp']);
      return {
        label: item.label,
        data: dictionary_scatter(dates, temps),
        borderColor: item.color,
        pointRadius: 1,
        borderWidth: 1,
      };
    }),
  };
  const config = {
    type: 'line',
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
      },
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: 'Temperature (°C)',
            fontSize: 18,
          },
          ticks: {
            suggestedMin: limits.min,
            suggestedMax: limits.max,
          },
        }],
        xAxes: [{
          type: 'time',
        }],
      },
    },
  };
  const ctx = document.getElementById(canvasname);
  new Chart(ctx, config);
}

function roundcharts(json_data, zoneid, canvasname, colouramp) {
  console.log(json_data[zoneid]);

  bin_ = [];
  cnt_ = [];
  for (j = 0; j < json_data[zoneid]['Values'].length; j++) {
    bin_.push(json_data[zoneid]['Values'][j]['bin']);
    cnt_.push(parseFloat(json_data[zoneid]['Values'][j]['cnt']));
  }

  const data_ = [];
  data_.push({
    label: [json_data[zoneid]['zone']],
    data: cnt_,
    backgroundColor: colouramp,
  });
  // title: [json_data[zoneid]["zone"]],

  const data = {
    labels: bin_,
    datasets: data_,
  };

  const config = {
    type: 'doughnut',
    data: data,
    options:
    {
      legend: {
        display: false,
      },
      aspectRatio: 1.5,
    },
  };
  // roundchart0
  const ctx = document.getElementById(canvasname);
  new Chart(ctx, config);
}

function horizontal_charts(json_data, zoneid, canvasname, colouramp) {
  // iterates through zones (5)
  bin_ = [];
  cnt_ = [];
  for (j = 0; j < json_data[zoneid]['Values'].length; j++) {
    bin_.push(json_data[zoneid]['Values'][j]['bin']);
    cnt_.push(parseFloat(json_data[zoneid]['Values'][j]['cnt']));
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
    labels: [json_data[zoneid]['zone']],
    datasets: datasets_,
  };

  const config = {
    type: 'horizontalBar',
    data: data,
    options:
    {

      legend: {
        display: false,
      },
      scales: {
        xAxes: [{
          stacked: true,
          display: false, // this will remove all the x-axis grid lines
        }],
        yAxes: [{
          stacked: true,
          // display: true,
          position: 'right',
        }],
      },
      aspectRatio: 6.5,
      tooltips: {

        callbacks: {
          position: 'average',
          title: function(tooltipItems, data) {
            return '';
          },
        },
      },
    },
  };

  // var ctx = document.getElementById('stackedbarchart'.concat(0));
  let ctx = document.getElementById(canvasname);
  new Chart(ctx, config);
}

function create_charts(temperature_data, temperature_data_daily, humidity_data,
  humidity_data_daily, stratification) {
  set_hourly_values(hourly_data_json);

  // blue to red
  const colouramp_redblue = [
    'rgba(63,103,126,1)', 'rgba(27,196,121,1)', 'rgba(137,214,11,1)',
    'rgba(207,19,10,1)',
  ];
  const colouramp_blue = [
    'rgba(27,55,74,1)', 'rgba(0,96,196,1)', 'rgba(0,129,196,1)',
    'rgba(141,245,252,1)',
  ];


  // main farm
  // round charts ("roundchart0")
  let zone0_name = temperature_data[0]['zone'];
  document.getElementById('zone0_name').innerHTML = zone0_name;
  roundcharts(temperature_data, 0, 'roundchart0', colouramp_redblue);

  let zone1_name = temperature_data[1]['zone'];
  document.getElementById('zone1_name').innerHTML = zone1_name;
  roundcharts(temperature_data, 1, 'roundchart1', colouramp_redblue);

  let zone2_name = temperature_data[2]['zone'];
  document.getElementById('zone2_name').innerHTML = zone2_name;
  roundcharts(temperature_data, 2, 'roundchart2', colouramp_redblue);

  roundcharts(temperature_data_daily, 0, 'roundchart10', colouramp_redblue);
  roundcharts(temperature_data_daily, 1, 'roundchart11', colouramp_redblue);
  roundcharts(temperature_data_daily, 2, 'roundchart12', colouramp_redblue);

  roundcharts(humidity_data, 0, 'roundchart5', colouramp_blue);
  roundcharts(humidity_data, 1, 'roundchart6', colouramp_blue);
  roundcharts(humidity_data, 2, 'roundchart7', colouramp_blue);

  roundcharts(humidity_data_daily, 0, 'roundchart15', colouramp_blue);
  roundcharts(humidity_data_daily, 1, 'roundchart16', colouramp_blue);
  roundcharts(humidity_data_daily, 2, 'roundchart17', colouramp_blue);


  // Find out min and max temperatures, to set the axis limits.
  const min_temps = Object.values(stratification_json).map(
    (x) => Math.min(...x.map((row) => row['temperature']))
  );
  const min_temp = Math.min(...min_temps);
  const max_temps = Object.values(stratification_json).map(
    (x) => Math.max(...x.map((row) => row['temperature']))
  );
  const max_temp = Math.max(...max_temps);
  limits = {
    min: min_temp,
    max: max_temp,
  };
  // Sensor id locations:
  // 18: 16B1, 21: 1B2, 22: 29B2, 23: 16B4
  // Vertical stratification
  vertical_series = [
    {id: 23, color: '#ff0000', label: 'Top'},
    {id: 18, color: '#3399ff', label: 'Bottom'},
  ];
  time_series_charts(
    stratification, vertical_series, limits, 'canvas_vertical_stratification'
  );
  // Horizontal stratification
  horizontal_series = [
    {id: 22, color: '#ff0000', label: 'Back farm'},
    {id: 21, color: '#3399ff', label: 'Front farm'},
  ];
  time_series_charts(
    stratification, horizontal_series, limits,
    'canvas_horizontal_stratification'
  );


  // Propagation
  let zone3_name = temperature_data[3]['zone'];
  document.getElementById('zone3_name').innerHTML = zone3_name;
  roundcharts(temperature_data, 3, 'roundchart3', colouramp_redblue);
  roundcharts(temperature_data_daily, 3, 'roundchart13', colouramp_redblue);

  roundcharts(humidity_data, 3, 'roundchart8', colouramp_blue);
  roundcharts(humidity_data_daily, 3, 'roundchart18', colouramp_blue);

  // R&D
  let zone4_name = temperature_data[4]['zone'];
  document.getElementById('zone4_name').innerHTML = zone4_name;
  roundcharts(temperature_data, 4, 'roundchart4', colouramp_redblue);
  roundcharts(temperature_data_daily, 4, 'roundchart14', colouramp_redblue);

  roundcharts(humidity_data, 4, 'roundchart9', colouramp_blue);
  roundcharts(humidity_data_daily, 4, 'roundchart19', colouramp_blue);
}

