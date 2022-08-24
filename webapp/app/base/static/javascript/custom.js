/**
 * Resize function without multiple trigger
 *
 * Usage:
 * $(window).smartresize(function(){
 *     // code here
 * });
 */
(function ($, sr) {
  // debouncing function from John Hann
  // http://unscriptable.com/index.php/2009/03/20/debouncing-javascript-methods/
  var debounce = function (func, threshold, execAsap) {
    var timeout;

    return function debounced() {
      var obj = this,
        args = arguments;
      function delayed() {
        if (!execAsap) func.apply(obj, args);
        timeout = null;
      }

      if (timeout) clearTimeout(timeout);
      else if (execAsap) func.apply(obj, args);

      timeout = setTimeout(delayed, threshold || 100);
    };
  };

  // smartresize
  jQuery.fn[sr] = function (fn) {
    return fn ? this.bind("resize", debounce(fn)) : this.trigger(sr);
  };
})(jQuery, "smartresize");
/**
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

var CURRENT_URL = window.location.href.split("#")[0].split("?")[0],
  $BODY = $("body"),
  $MENU_TOGGLE = $("#menu_toggle"),
  $SIDEBAR_MENU = $("#sidebar-menu"),
  $SIDEBAR_FOOTER = $(".sidebar-footer"),
  $LEFT_COL = $(".left_col"),
  $RIGHT_COL = $(".right_col"),
  $NAV_MENU = $(".nav_menu"),
  $FOOTER = $("footer");

// Sidebar
function init_sidebar() {
  // TODO: This is some kind of easy fix, maybe we can improve this
  var setContentHeight = function () {
    // reset height
    $RIGHT_COL.css("min-height", $(window).height());

    var bodyHeight = $BODY.outerHeight(),
      footerHeight = $BODY.hasClass("footer_fixed") ? -10 : $FOOTER.height(),
      leftColHeight = $LEFT_COL.eq(1).height() + $SIDEBAR_FOOTER.height(),
      contentHeight = bodyHeight < leftColHeight ? leftColHeight : bodyHeight;

    // normalize content
    contentHeight -= $NAV_MENU.height() + footerHeight;

    $RIGHT_COL.css("min-height", contentHeight);
  };

  $SIDEBAR_MENU.find("a").on("click", function (ev) {
    console.log("clicked - sidebar_menu");
    var $li = $(this).parent();

    if ($li.is(".active")) {
      $li.removeClass("active active-sm");
      $("ul:first", $li).slideUp(function () {
        setContentHeight();
      });
    } else {
      // prevent closing menu if we are on child menu
      if (!$li.parent().is(".child_menu")) {
        $SIDEBAR_MENU.find("li").removeClass("active active-sm");
        $SIDEBAR_MENU.find("li ul").slideUp();
      } else {
        if ($BODY.is(".nav-sm")) {
          $SIDEBAR_MENU.find("li").removeClass("active active-sm");
          $SIDEBAR_MENU.find("li ul").slideUp();
        }
      }
      $li.addClass("active");

      $("ul:first", $li).slideDown(function () {
        setContentHeight();
      });
    }
  });

  // toggle small or large menu
  $MENU_TOGGLE.on("click", function () {
    console.log("clicked - menu toggle");

    if ($BODY.hasClass("nav-md")) {
      $SIDEBAR_MENU.find("li.active ul").hide();
      $SIDEBAR_MENU
        .find("li.active")
        .addClass("active-sm")
        .removeClass("active");
    } else {
      $SIDEBAR_MENU.find("li.active-sm ul").show();
      $SIDEBAR_MENU
        .find("li.active-sm")
        .addClass("active")
        .removeClass("active-sm");
    }

    $BODY.toggleClass("nav-md nav-sm");

    setContentHeight();

    $(".dataTable").each(function () {
      $(this).dataTable().fnDraw();
    });
  });

  // check active menu
  $SIDEBAR_MENU
    .find('a[href="' + CURRENT_URL + '"]')
    .parent("li")
    .addClass("current-page");

  $SIDEBAR_MENU
    .find("a")
    .filter(function () {
      return this.href == CURRENT_URL;
    })
    .parent("li")
    .addClass("current-page")
    .parents("ul")
    .slideDown(function () {
      setContentHeight();
    })
    .parent()
    .addClass("active");

  // recompute content when resizing
  $(window).smartresize(function () {
    setContentHeight();
  });

  setContentHeight();
}
// /Sidebar

var randNum = function () {
  return Math.floor(Math.random() * (1 + 40 - 20)) + 20;
};

// Panel toolbox
$(document).ready(function () {
  $(".collapse-link").on("click", function () {
    var $BOX_PANEL = $(this).closest(".x_panel"),
      $ICON = $(this).find("i"),
      $BOX_CONTENT = $BOX_PANEL.find(".x_content");

    // fix for some div with hardcoded fix class
    if ($BOX_PANEL.attr("style")) {
      $BOX_CONTENT.slideToggle(200, function () {
        $BOX_PANEL.removeAttr("style");
      });
    } else {
      $BOX_CONTENT.slideToggle(200);
      $BOX_PANEL.css("height", "auto");
    }

    $ICON.toggleClass("fa-chevron-up fa-chevron-down");
  });

  $(".close-link").click(function () {
    var $BOX_PANEL = $(this).closest(".x_panel");

    $BOX_PANEL.remove();
  });
});
// /Panel toolbox

// Tooltip
$(document).ready(function () {
  $('[data-toggle="tooltip"]').tooltip({
    container: "body",
  });
});
// /Tooltip

// Progressbar
if ($(".progress .progress-bar")[0]) {
  $(".progress .progress-bar").progressbar();
}
// /Progressbar

// Accordion
$(document).ready(function () {
  $(".expand").on("click", function () {
    $(this).next().slideToggle(200);
    $expand = $(this).find(">:first-child");

    if ($expand.text() == "+") {
      $expand.text("-");
    } else {
      $expand.text("+");
    }
  });
});

//hover and retain popover when on popover content
var originalLeave = $.fn.popover.Constructor.prototype.leave;
$.fn.popover.Constructor.prototype.leave = function (obj) {
  var self =
    obj instanceof this.constructor
      ? obj
      : $(obj.currentTarget)
          [this.type](this.getDelegateOptions())
          .data("bs." + this.type);
  var container, timeout;

  originalLeave.call(this, obj);

  if (obj.currentTarget) {
    container = $(obj.currentTarget).siblings(".popover");
    timeout = self.timeout;
    container.one("mouseenter", function () {
      //We entered the actual popover – call off the dogs
      clearTimeout(timeout);
      //Let's monitor popover content instead
      container.one("mouseleave", function () {
        $.fn.popover.Constructor.prototype.leave.call(self, self);
      });
    });
  }
};

$("body").popover({
  selector: "[data-popover]",
  trigger: "click hover",
  delay: {
    show: 50,
    hide: 400,
  },
});

function gd(year, month, day) {
  return new Date(year, month - 1, day).getTime();
}

function init_chart_doughnut() {
  if (typeof Chart === "undefined") {
    return;
  }

  console.log("init_chart_doughnut");

  if ($(".canvasDoughnut").length) {
    var chart_doughnut_settings = {
      type: "doughnut",
      tooltipFillColor: "rgba(51, 51, 51, 0.55)",
      data: {
        labels: ["Symbian", "Blackberry", "Other", "Android", "IOS"],
        datasets: [
          {
            data: [15, 20, 30, 10, 30],
            backgroundColor: [
              "#BDC3C7",
              "#9B59B6",
              "#E74C3C",
              "#26B99A",
              "#3498DB",
            ],
            hoverBackgroundColor: [
              "#CFD4D8",
              "#B370CF",
              "#E95E4F",
              "#36CAAB",
              "#49A9EA",
            ],
          },
        ],
      },
      options: {
        legend: false,
        responsive: false,
      },
    };

    $(".canvasDoughnut").each(function () {
      var chart_element = $(this);
      var chart_doughnut = new Chart(chart_element, chart_doughnut_settings);
    });
  }
}

/* SPARKLINES */

function init_sparklines() {
  if (typeof jQuery.fn.sparkline === "undefined") {
    return;
  }
  console.log("init_sparklines");

  $(".sparkline_one").sparkline(
    [
      2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 5, 6, 4, 5, 6, 3, 5, 4, 5, 4, 5, 4, 3, 4, 5,
      6, 7, 5, 4, 3, 5, 6,
    ],
    {
      type: "bar",
      height: "125",
      barWidth: 13,
      colorMap: {
        7: "#a1a1a1",
      },
      barSpacing: 2,
      barColor: "#26B99A",
    }
  );

  $(".sparkline_two").sparkline(
    [2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 5, 6, 7, 5, 4, 3, 5, 6],
    {
      type: "bar",
      height: "40",
      barWidth: 9,
      colorMap: {
        7: "#a1a1a1",
      },
      barSpacing: 2,
      barColor: "#26B99A",
    }
  );

  $(".sparkline_three").sparkline(
    [2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 5, 6, 7, 5, 4, 3, 5, 6],
    {
      type: "line",
      width: "200",
      height: "40",
      lineColor: "#26B99A",
      fillColor: "rgba(223, 223, 223, 0.57)",
      lineWidth: 2,
      spotColor: "#26B99A",
      minSpotColor: "#26B99A",
    }
  );

  $(".sparkline11").sparkline(
    [2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 6, 2, 4, 3, 4, 5, 4, 5, 4, 3],
    {
      type: "bar",
      height: "40",
      barWidth: 8,
      colorMap: {
        7: "#a1a1a1",
      },
      barSpacing: 2,
      barColor: "#26B99A",
    }
  );

  $(".sparkline22").sparkline(
    [2, 4, 3, 4, 7, 5, 4, 3, 5, 6, 2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 6],
    {
      type: "line",
      height: "40",
      width: "200",
      lineColor: "#26B99A",
      fillColor: "#ffffff",
      lineWidth: 3,
      spotColor: "#34495E",
      minSpotColor: "#34495E",
    }
  );

  $(".sparkline_bar").sparkline(
    [2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 5, 6, 4, 5, 6, 3, 5],
    {
      type: "bar",
      colorMap: {
        7: "#a1a1a1",
      },
      barColor: "#26B99A",
    }
  );

  $(".sparkline_area").sparkline([5, 6, 7, 9, 9, 5, 3, 2, 2, 4, 6, 7], {
    type: "line",
    lineColor: "#26B99A",
    fillColor: "#26B99A",
    spotColor: "#4578a0",
    minSpotColor: "#728fb2",
    maxSpotColor: "#6d93c4",
    highlightSpotColor: "#ef5179",
    highlightLineColor: "#8ba8bf",
    spotRadius: 2.5,
    width: 85,
  });

  $(".sparkline_line").sparkline(
    [2, 4, 3, 4, 5, 4, 5, 4, 3, 4, 5, 6, 4, 5, 6, 3, 5],
    {
      type: "line",
      lineColor: "#26B99A",
      fillColor: "#ffffff",
      width: 85,
      spotColor: "#34495E",
      minSpotColor: "#34495E",
    }
  );

  $(".sparkline_pie").sparkline([1, 1, 2, 1], {
    type: "pie",
    sliceColors: ["#26B99A", "#ccc", "#75BCDD", "#D66DE2"],
  });

  $(".sparkline_discreet").sparkline(
    [4, 6, 7, 7, 4, 3, 2, 1, 4, 4, 2, 4, 3, 7, 8, 9, 7, 6, 4, 3],
    {
      type: "discrete",
      barWidth: 3,
      lineColor: "#26B99A",
      width: "85",
    }
  );
}

/* PARSLEY */

function init_parsley() {
  if (typeof parsley === "undefined") {
    return;
  }
  console.log("init_parsley");

  $(/*.listen*/ "parsley:field:validate", function () {
    validateFront();
  });
  $("#demo-form .btn").on("click", function () {
    $("#demo-form").parsley().validate();
    validateFront();
  });
  var validateFront = function () {
    if (true === $("#demo-form").parsley().isValid()) {
      $(".bs-callout-info").removeClass("hidden");
      $(".bs-callout-warning").addClass("hidden");
    } else {
      $(".bs-callout-info").addClass("hidden");
      $(".bs-callout-warning").removeClass("hidden");
    }
  };

  $(/*.listen*/ "parsley:field:validate", function () {
    validateFront();
  });
  $("#demo-form2 .btn").on("click", function () {
    $("#demo-form2").parsley().validate();
    validateFront();
  });
  var validateFront = function () {
    if (true === $("#demo-form2").parsley().isValid()) {
      $(".bs-callout-info").removeClass("hidden");
      $(".bs-callout-warning").addClass("hidden");
    } else {
      $(".bs-callout-info").addClass("hidden");
      $(".bs-callout-warning").removeClass("hidden");
    }
  };

  try {
    hljs.initHighlightingOnLoad();
  } catch (err) {}
}

/* CROPPER */

function init_cropper() {
  if (typeof $.fn.cropper === "undefined") {
    return;
  }
  console.log("init_cropper");

  var $image = $("#image");
  var $download = $("#download");
  var $dataX = $("#dataX");
  var $dataY = $("#dataY");
  var $dataHeight = $("#dataHeight");
  var $dataWidth = $("#dataWidth");
  var $dataRotate = $("#dataRotate");
  var $dataScaleX = $("#dataScaleX");
  var $dataScaleY = $("#dataScaleY");
  var options = {
    aspectRatio: 16 / 9,
    preview: ".img-preview",
    crop: function (e) {
      $dataX.val(Math.round(e.x));
      $dataY.val(Math.round(e.y));
      $dataHeight.val(Math.round(e.height));
      $dataWidth.val(Math.round(e.width));
      $dataRotate.val(e.rotate);
      $dataScaleX.val(e.scaleX);
      $dataScaleY.val(e.scaleY);
    },
  };

  // Tooltip
  $('[data-toggle="tooltip"]').tooltip();

  // Cropper
  $image
    .on({
      "build.cropper": function (e) {
        console.log(e.type);
      },
      "built.cropper": function (e) {
        console.log(e.type);
      },
      "cropstart.cropper": function (e) {
        console.log(e.type, e.action);
      },
      "cropmove.cropper": function (e) {
        console.log(e.type, e.action);
      },
      "cropend.cropper": function (e) {
        console.log(e.type, e.action);
      },
      "crop.cropper": function (e) {
        console.log(
          e.type,
          e.x,
          e.y,
          e.width,
          e.height,
          e.rotate,
          e.scaleX,
          e.scaleY
        );
      },
      "zoom.cropper": function (e) {
        console.log(e.type, e.ratio);
      },
    })
    .cropper(options);

  // Buttons
  if (!$.isFunction(document.createElement("canvas").getContext)) {
    $('button[data-method="getCroppedCanvas"]').prop("disabled", true);
  }

  if (
    typeof document.createElement("cropper").style.transition === "undefined"
  ) {
    $('button[data-method="rotate"]').prop("disabled", true);
    $('button[data-method="scale"]').prop("disabled", true);
  }

  // Download
  if (typeof $download[0].download === "undefined") {
    $download.addClass("disabled");
  }

  // Options
  $(".docs-toggles").on("change", "input", function () {
    var $this = $(this);
    var name = $this.attr("name");
    var type = $this.prop("type");
    var cropBoxData;
    var canvasData;

    if (!$image.data("cropper")) {
      return;
    }

    if (type === "checkbox") {
      options[name] = $this.prop("checked");
      cropBoxData = $image.cropper("getCropBoxData");
      canvasData = $image.cropper("getCanvasData");

      options.built = function () {
        $image.cropper("setCropBoxData", cropBoxData);
        $image.cropper("setCanvasData", canvasData);
      };
    } else if (type === "radio") {
      options[name] = $this.val();
    }

    $image.cropper("destroy").cropper(options);
  });

  // Methods
  $(".docs-buttons").on("click", "[data-method]", function () {
    var $this = $(this);
    var data = $this.data();
    var $target;
    var result;

    if ($this.prop("disabled") || $this.hasClass("disabled")) {
      return;
    }

    if ($image.data("cropper") && data.method) {
      data = $.extend({}, data); // Clone a new one

      if (typeof data.target !== "undefined") {
        $target = $(data.target);

        if (typeof data.option === "undefined") {
          try {
            data.option = JSON.parse($target.val());
          } catch (e) {
            console.log(e.message);
          }
        }
      }

      result = $image.cropper(data.method, data.option, data.secondOption);

      switch (data.method) {
        case "scaleX":
        case "scaleY":
          $(this).data("option", -data.option);
          break;

        case "getCroppedCanvas":
          if (result) {
            // Bootstrap's Modal
            $("#getCroppedCanvasModal")
              .modal()
              .find(".modal-body")
              .html(result);

            if (!$download.hasClass("disabled")) {
              $download.attr("href", result.toDataURL());
            }
          }

          break;
      }

      if ($.isPlainObject(result) && $target) {
        try {
          $target.val(JSON.stringify(result));
        } catch (e) {
          console.log(e.message);
        }
      }
    }
  });

  // Keyboard
  $(document.body).on("keydown", function (e) {
    if (!$image.data("cropper") || this.scrollTop > 300) {
      return;
    }

    switch (e.which) {
      case 37:
        e.preventDefault();
        $image.cropper("move", -1, 0);
        break;

      case 38:
        e.preventDefault();
        $image.cropper("move", 0, -1);
        break;

      case 39:
        e.preventDefault();
        $image.cropper("move", 1, 0);
        break;

      case 40:
        e.preventDefault();
        $image.cropper("move", 0, 1);
        break;
    }
  });

  // Import image
  var $inputImage = $("#inputImage");
  var URL = window.URL || window.webkitURL;
  var blobURL;

  if (URL) {
    $inputImage.change(function () {
      var files = this.files;
      var file;

      if (!$image.data("cropper")) {
        return;
      }

      if (files && files.length) {
        file = files[0];

        if (/^image\/\w+$/.test(file.type)) {
          blobURL = URL.createObjectURL(file);
          $image
            .one("built.cropper", function () {
              // Revoke when load complete
              URL.revokeObjectURL(blobURL);
            })
            .cropper("reset")
            .cropper("replace", blobURL);
          $inputImage.val("");
        } else {
          window.alert("Please choose an image file.");
        }
      }
    });
  } else {
    $inputImage.prop("disabled", true).parent().addClass("disabled");
  }
}

/* CROPPER --- end */

/* KNOB */

function init_knob() {
  if (typeof $.fn.knob === "undefined") {
    return;
  }
  console.log("init_knob");

  $(".knob").knob({
    change: function (value) {
      //console.log("change : " + value);
    },
    release: function (value) {
      //console.log(this.$.attr('value'));
      console.log("release : " + value);
    },
    cancel: function () {
      console.log("cancel : ", this);
    },
    /*format : function (value) {
				   return value + '%';
				   },*/
    draw: function () {
      // "tron" case
      if (this.$.data("skin") == "tron") {
        this.cursorExt = 0.3;

        var a = this.arc(this.cv), // Arc
          pa, // Previous arc
          r = 1;

        this.g.lineWidth = this.lineWidth;

        if (this.o.displayPrevious) {
          pa = this.arc(this.v);
          this.g.beginPath();
          this.g.strokeStyle = this.pColor;
          this.g.arc(
            this.xy,
            this.xy,
            this.radius - this.lineWidth,
            pa.s,
            pa.e,
            pa.d
          );
          this.g.stroke();
        }

        this.g.beginPath();
        this.g.strokeStyle = r ? this.o.fgColor : this.fgColor;
        this.g.arc(
          this.xy,
          this.xy,
          this.radius - this.lineWidth,
          a.s,
          a.e,
          a.d
        );
        this.g.stroke();

        this.g.lineWidth = 2;
        this.g.beginPath();
        this.g.strokeStyle = this.o.fgColor;
        this.g.arc(
          this.xy,
          this.xy,
          this.radius - this.lineWidth + 1 + (this.lineWidth * 2) / 3,
          0,
          2 * Math.PI,
          false
        );
        this.g.stroke();

        return false;
      }
    },
  });

  // Example of infinite knob, iPod click wheel
  var v,
    up = 0,
    down = 0,
    i = 0,
    $idir = $("div.idir"),
    $ival = $("div.ival"),
    incr = function () {
      i++;
      $idir.show().html("+").fadeOut();
      $ival.html(i);
    },
    decr = function () {
      i--;
      $idir.show().html("-").fadeOut();
      $ival.html(i);
    };
  $("input.infinite").knob({
    min: 0,
    max: 20,
    stopper: false,
    change: function () {
      if (v > this.cv) {
        if (up) {
          decr();
          up = 0;
        } else {
          up = 1;
          down = 0;
        }
      } else {
        if (v < this.cv) {
          if (down) {
            incr();
            down = 0;
          } else {
            down = 1;
            up = 0;
          }
        }
      }
      v = this.cv;
    },
  });
}

/* INPUT MASK */

function init_InputMask() {
  if (typeof $.fn.inputmask === "undefined") {
    return;
  }
  console.log("init_InputMask");

  $(":input").inputmask();
}

/* COLOR PICKER */

function init_ColorPicker() {
  if (typeof $.fn.colorpicker === "undefined") {
    return;
  }
  console.log("init_ColorPicker");

  $(".demo1").colorpicker();
  $(".demo2").colorpicker();

  $("#demo_forceformat").colorpicker({
    format: "rgba",
    horizontal: true,
  });

  $("#demo_forceformat3").colorpicker({
    format: "rgba",
  });

  $(".demo-auto").colorpicker();
}

/* ION RANGE SLIDER */

function init_IonRangeSlider() {
  if (typeof $.fn.ionRangeSlider === "undefined") {
    return;
  }
  console.log("init_IonRangeSlider");

  $("#range_27").ionRangeSlider({
    type: "double",
    min: 1000000,
    max: 2000000,
    grid: true,
    force_edges: true,
  });
  $("#range").ionRangeSlider({
    hide_min_max: true,
    keyboard: true,
    min: 0,
    max: 5000,
    from: 1000,
    to: 4000,
    type: "double",
    step: 1,
    prefix: "$",
    grid: true,
  });
  $("#range_25").ionRangeSlider({
    type: "double",
    min: 1000000,
    max: 2000000,
    grid: true,
  });
  $("#range_26").ionRangeSlider({
    type: "double",
    min: 0,
    max: 10000,
    step: 500,
    grid: true,
    grid_snap: true,
  });
  $("#range_31").ionRangeSlider({
    type: "double",
    min: 0,
    max: 100,
    from: 30,
    to: 70,
    from_fixed: true,
  });
  $(".range_min_max").ionRangeSlider({
    type: "double",
    min: 0,
    max: 100,
    from: 30,
    to: 70,
    max_interval: 50,
  });
  $(".range_time24").ionRangeSlider({
    min: +moment().subtract(12, "hours").format("X"),
    max: +moment().format("X"),
    from: +moment().subtract(6, "hours").format("X"),
    grid: true,
    force_edges: true,
    prettify: function (num) {
      var m = moment(num, "X");
      return m.format("Do MMMM, HH:mm");
    },
  });
}

/* DATERANGEPICKER */

function init_daterangepicker() {
  if (typeof $.fn.daterangepicker === "undefined") {
    return;
  }
  console.log("init_daterangepicker");

  var cb = function (start, end, label) {
    console.log(start.toISOString(), end.toISOString(), label);
    $("#reportrange span").html(
      start.format("MMMM D, YYYY") + " - " + end.format("MMMM D, YYYY")
    );
  };

  var optionSet1 = {
    startDate: moment().subtract(29, "days"),
    endDate: moment(),
    minDate: "01/01/2010",
    maxDate: "12/31/2030",
    dateLimit: {
      days: 730, // Max time range is two years
    },
    showDropdowns: true,
    showWeekNumbers: true,
    timePicker: false,
    timePickerIncrement: 1,
    timePicker12Hour: true,
    ranges: {
      Today: [moment(), moment()],
      Yesterday: [moment().subtract(1, "days"), moment().subtract(1, "days")],
      "Last 7 Days": [moment().subtract(6, "days"), moment()],
      "Last 30 Days": [moment().subtract(29, "days"), moment()],
      "This Month": [moment().startOf("month"), moment().endOf("month")],
      "Last Month": [
        moment().subtract(1, "month").startOf("month"),
        moment().subtract(1, "month").endOf("month"),
      ],
    },
    opens: "left",
    buttonClasses: ["btn btn-default"],
    applyClass: "btn-small btn-primary",
    cancelClass: "btn-small",
    format: "MM/DD/YYYY",
    separator: " to ",
    locale: {
      applyLabel: "Submit",
      cancelLabel: "Clear",
      fromLabel: "From",
      toLabel: "To",
      customRangeLabel: "Custom",
      daysOfWeek: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
      monthNames: [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
      ],
      firstDay: 1,
    },
  };

  $("#reportrange span").html(
    moment().subtract(29, "days").format("MMMM D, YYYY") +
      " - " +
      moment().format("MMMM D, YYYY")
  );
  $("#reportrange").daterangepicker(optionSet1, cb);
  $("#reportrange").on("show.daterangepicker", function () {
    console.log("show event fired");
  });
  $("#reportrange").on("hide.daterangepicker", function () {
    console.log("hide event fired");
  });
  $("#reportrange").on("apply.daterangepicker", function (ev, picker) {
    console.log(
      "apply event fired, start/end dates are " +
        picker.startDate.format("MMMM D, YYYY") +
        " to " +
        picker.endDate.format("MMMM D, YYYY")
    );
  });
  $("#reportrange").on("cancel.daterangepicker", function (ev, picker) {
    console.log("cancel event fired");
  });
  $("#options1").click(function () {
    $("#reportrange").data("daterangepicker").setOptions(optionSet1, cb);
  });
  $("#options2").click(function () {
    $("#reportrange").data("daterangepicker").setOptions(optionSet2, cb);
  });
  $("#destroy").click(function () {
    $("#reportrange").data("daterangepicker").remove();
  });
}

function init_daterangepicker_right() {
  if (typeof $.fn.daterangepicker === "undefined") {
    return;
  }
  console.log("init_daterangepicker_right");

  var cb = function (start, end, label) {
    console.log(start.toISOString(), end.toISOString(), label);
    $("#reportrange_right span").html(
      start.format("MMMM D, YYYY") + " - " + end.format("MMMM D, YYYY")
    );
  };

  var optionSet1 = {
    startDate: moment().subtract(29, "days"),
    endDate: moment(),
    minDate: "01/01/2010",
    maxDate: "12/31/2030",
    dateLimit: {
      days: 60,
    },
    showDropdowns: true,
    showWeekNumbers: true,
    timePicker: false,
    timePickerIncrement: 1,
    timePicker12Hour: true,
    ranges: {
      Today: [moment(), moment()],
      Yesterday: [moment().subtract(1, "days"), moment().subtract(1, "days")],
      "Last 7 Days": [moment().subtract(6, "days"), moment()],
      "Last 30 Days": [moment().subtract(29, "days"), moment()],
      "This Month": [moment().startOf("month"), moment().endOf("month")],
      "Last Month": [
        moment().subtract(1, "month").startOf("month"),
        moment().subtract(1, "month").endOf("month"),
      ],
    },
    opens: "right",
    buttonClasses: ["btn btn-default"],
    applyClass: "btn-small btn-primary",
    cancelClass: "btn-small",
    format: "MM/DD/YYYY",
    separator: " to ",
    locale: {
      applyLabel: "Submit",
      cancelLabel: "Clear",
      fromLabel: "From",
      toLabel: "To",
      customRangeLabel: "Custom",
      daysOfWeek: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
      monthNames: [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
      ],
      firstDay: 1,
    },
  };

  $("#reportrange_right span").html(
    moment().subtract(29, "days").format("MMMM D, YYYY") +
      " - " +
      moment().format("MMMM D, YYYY")
  );

  $("#reportrange_right").daterangepicker(optionSet1, cb);

  $("#reportrange_right").on("show.daterangepicker", function () {
    console.log("show event fired");
  });
  $("#reportrange_right").on("hide.daterangepicker", function () {
    console.log("hide event fired");
  });
  $("#reportrange_right").on("apply.daterangepicker", function (ev, picker) {
    console.log(
      "apply event fired, start/end dates are " +
        picker.startDate.format("MMMM D, YYYY") +
        " to " +
        picker.endDate.format("MMMM D, YYYY")
    );
  });
  $("#reportrange_right").on("cancel.daterangepicker", function (ev, picker) {
    console.log("cancel event fired");
  });

  $("#options1").click(function () {
    $("#reportrange_right").data("daterangepicker").setOptions(optionSet1, cb);
  });

  $("#options2").click(function () {
    $("#reportrange_right").data("daterangepicker").setOptions(optionSet2, cb);
  });

  $("#destroy").click(function () {
    $("#reportrange_right").data("daterangepicker").remove();
  });
}

function init_daterangepicker_single_call() {
  if (typeof $.fn.daterangepicker === "undefined") {
    return;
  }
  console.log("init_daterangepicker_single_call");

  $("#single_cal1").daterangepicker(
    {
      singleDatePicker: true,
      singleClasses: "picker_1",
    },
    function (start, end, label) {
      console.log(start.toISOString(), end.toISOString(), label);
    }
  );
  $("#single_cal2").daterangepicker(
    {
      singleDatePicker: true,
      singleClasses: "picker_2",
    },
    function (start, end, label) {
      console.log(start.toISOString(), end.toISOString(), label);
    }
  );
  $("#single_cal3").daterangepicker(
    {
      singleDatePicker: true,
      singleClasses: "picker_3",
    },
    function (start, end, label) {
      console.log(start.toISOString(), end.toISOString(), label);
    }
  );
  $("#single_cal4").daterangepicker(
    {
      singleDatePicker: true,
      singleClasses: "picker_4",
    },
    function (start, end, label) {
      console.log(start.toISOString(), end.toISOString(), label);
    }
  );
}

function init_daterangepicker_reservation() {
  if (typeof $.fn.daterangepicker === "undefined") {
    return;
  }
  console.log("init_daterangepicker_reservation");

  $("#reservation").daterangepicker(null, function (start, end, label) {
    console.log(start.toISOString(), end.toISOString(), label);
  });

  $("#reservation-time").daterangepicker({
    timePicker: true,
    timePickerIncrement: 30,
    locale: {
      format: "MM/DD/YYYY h:mm A",
    },
  });
}

/* VALIDATOR */

function init_validator() {
  if (typeof validator === "undefined") {
    return;
  }
  console.log("init_validator");

  // initialize the validator function
  validator.message.date = "not a real date";

  // validate a field on "blur" event, a 'select' on 'change' event & a '.reuired' classed multifield on 'keyup':
  $("form")
    .on(
      "blur",
      "input[required], input.optional, select.required",
      validator.checkField
    )
    .on("change", "select.required", validator.checkField)
    .on("keypress", "input[required][pattern]", validator.keypress);

  $(".multi.required").on("keyup blur", "input", function () {
    validator.checkField.apply($(this).siblings().last()[0]);
  });

  $("form").submit(function (e) {
    e.preventDefault();
    var submit = true;

    // evaluate the form using generic validaing
    if (!validator.checkAll($(this))) {
      submit = false;
    }

    if (submit) this.submit();

    return false;
  });
}

/* DATA TABLES */

function init_DataTables() {
  console.log("run_datatables");

  if (typeof $.fn.DataTable === "undefined") {
    return;
  }
  console.log("init_DataTables");

  var handleDataTableButtons = function () {
    if ($("#datatable-buttons").length) {
      $("#datatable-buttons").DataTable({
        dom: "Bfrtip",
        buttons: [
          {
            extend: "copy",
            className: "btn-sm",
          },
          {
            extend: "csv",
            className: "btn-sm",
          },
          {
            extend: "excel",
            className: "btn-sm",
          },
          {
            extend: "pdfHtml5",
            className: "btn-sm",
          },
          {
            extend: "print",
            className: "btn-sm",
          },
        ],
        responsive: true,
      });
    }
  };

  TableManageButtons = (function () {
    "use strict";
    return {
      init: function () {
        handleDataTableButtons();
      },
    };
  })();

  $("#datatable").dataTable();

  $("#datatable-keytable").DataTable({
    keys: true,
  });

  $("#datatable-responsive").DataTable();

  $("#datatable-scroller").DataTable({
    ajax: "js/datatables/json/scroller-demo.json",
    deferRender: true,
    scrollY: 380,
    scrollCollapse: true,
    scroller: true,
  });

  $("#datatable-fixed-header").DataTable({
    fixedHeader: true,
  });

  var $datatable = $("#datatable-checkbox");

  $datatable.dataTable({
    order: [[1, "asc"]],
    columnDefs: [{ orderable: false, targets: [0] }],
  });

  TableManageButtons.init();
}

$(document).ready(function () {
  init_sparklines();
  init_sidebar();
  init_InputMask();
  init_cropper();
  init_knob();
  init_IonRangeSlider();
  init_ColorPicker();
  init_parsley();
  init_daterangepicker();
  init_daterangepicker_right();
  init_daterangepicker_single_call();
  init_daterangepicker_reservation();
  init_validator();
  init_DataTables();
  init_chart_doughnut();
});
