// Zip to arrays [x0, x1, x2, ...] and [y0, y1, y2, ...] into
// [{x: x0, y: 01}, {x: x1, y: y1}, {x: x2, y: y2}, ...]
// Used to gather data for plots into a format preferred by Chart.js
function dictionary_scatter(x, y) {
  value_array = [];
  for (let j=0; j < y.length; j++) {
    const mydict = {x: x[j], y: y[j]};
    value_array.push(mydict);
  }
  return value_array;
}


// Sort an array of objects by the field elname, which each object is assumed
// to have, and which is assumed to be a number. Operates in place.
function sort_by_numerical(arr, elname) {
  return arr.sort((e1, e2) => e1[elname] - e2[elname]);
}
