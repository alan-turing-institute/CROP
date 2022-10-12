const plotConfigTemplate = {
  type: "line",
  options: {
    responsive: true,
    plugins: {
      legend: false,
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

function makePlots(data, yDataName, canvasId, yLabel, colour, placeholderId) {
  const datasets = [];
  const pointRadius = 1;
  const borderWidth = 1;
  datasets.push({
    data: data.map((row) => {
      return { x: row["timestamp"], y: row[yDataName] };
    }),
    pointRadius: pointRadius,
    borderWidth: borderWidth,
    borderColor: colour,
    fill: true,
  });
  const config = JSON.parse(JSON.stringify(plotConfigTemplate)); // Make a copy
  config.options.scales.y.title.text = yLabel;
  config.data = { datasets: datasets };
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, config);

  const placeholder = document.getElementById(placeholderId);
  placeholder.style.display = "none";
}
