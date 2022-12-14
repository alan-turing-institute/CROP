const plotName = "parallelAxesPlotDiv";
// These variables are global, because different functions need to read/write them
// independently.
let startDate = undefined;
let endDate = undefined;
let plotInput = undefined;

function setDateRange(start, end) {
  startDate = start;
  endDate = end;
}

$("#reportrange").on("apply.daterangepicker", function (ev, picker) {
  setDateRange(picker.startDate, picker.endDate);
});

function getSelectedCropTypeStr() {
  const cropTypeSelector = document.getElementById("cropTypeSelector");
  const cropType = cropTypeSelector.value;
  const cropTypeStr = encodeURIComponent(cropType);
  return cropTypeStr;
}

function reloadPage() {
  const cropTypeStr = getSelectedCropTypeStr();
  const datePicker = document.getElementById("reportrange");
  const dateRange =
    startDate.format("YYYYMMDD") + "-" + endDate.format("YYYYMMDD");

  const searchParams = new URLSearchParams(window.location.search);
  searchParams.set("range", dateRange);
  searchParams.set("crop_type", cropTypeStr);
  const newUrl =
    window.location.origin +
    window.location.pathname +
    "?" +
    searchParams.toString();
  location.replace(newUrl);
}

function getColourAxisName() {
  const picker = document.getElementById("colourAxisSelector");
  const colourAxis = picker.value;
  return colourAxis;
}

function makeParAxesPlot(data, axes) {
  const colourAxis = getColourAxisName();
  const trace = {
    type: "parcoords",
    line: {
      showscale: true,
      colorscale: "Portland",
      color: Object.values(data[colourAxis]),
      // TODO I would like to increase the line width. That's currently unsupported by
      // Plotly, but support is on the way:
      // https://github.com/plotly/plotly.js/issues/2573
      // Once that's available, try adjusting the line width.
    },
    dimensions: [],
  };

  Object.keys(axes).forEach((columnName) => {
    const checkbox = document.getElementById("column_checkbox_" + columnName);
    trace.dimensions.push({
      name: columnName,
      label: axes[columnName],
      values: Object.values(data[columnName]),
      visible: checkbox.checked,
    });
  });

  plotInput = [trace]; // Set the global. rerender will modify this.
  Plotly.newPlot(plotName, plotInput);
}

function rerender(data) {
  const colourAxis = getColourAxisName();
  // Modify the global data dictionary, that the plot holds a reference to.
  plotInput[0]["line"]["color"] = Object.values(data[colourAxis]);
  plotInput[0]["dimensions"].forEach((dimension) => {
    const columnName = dimension["name"];
    const checkbox = document.getElementById("column_checkbox_" + columnName);
    dimension["visible"] = checkbox.checked;
  });
  Plotly.redraw(plotName);
}
