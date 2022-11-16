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
      colorscale: "Jet",
      color: Object.values(data[colourAxis]),
      width: 5, // TODO Why doesn't this have an effect?
    },
    dimensions: [],
  };

  Object.keys(axes).forEach((columnName) => {
    trace.dimensions.push({
      label: axes[columnName],
      values: Object.values(data[columnName]),
    });
  });

  plotInput = [trace]; // Set the global. rerender will modify this.
  Plotly.newPlot(plotName, plotInput);
}

function rerender(data) {
  const colourAxis = getColourAxisName();
  plotInput[0]["line"]["color"] = Object.values(data[colourAxis]); // Modify the global
  Plotly.redraw(plotName);
}
