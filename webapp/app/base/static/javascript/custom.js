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

// NProgress
if (typeof NProgress != "undefined") {
  $(document).ready(function () {
    NProgress.start();
  });

  $(window).load(function () {
    NProgress.done();
  });
}

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

/* SMART WIZARD */

function init_SmartWizard() {
  if (typeof $.fn.smartWizard === "undefined") {
    return;
  }
  console.log("init_SmartWizard");

  $("#wizard").smartWizard();

  $("#wizard_verticle").smartWizard({
    transitionEffect: "slide",
  });

  $(".buttonNext").addClass("btn btn-success");
  $(".buttonPrevious").addClass("btn btn-primary");
  $(".buttonFinish").addClass("btn btn-default");
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

/* PNotify */

function init_PNotify() {
  if (typeof PNotify === "undefined") {
    return;
  }
  console.log("init_PNotify");

  new PNotify({
    title: "PNotify",
    type: "info",
    text: "Welcome. Try hovering over me. You can click things behind me, because I'm non-blocking.",
    nonblock: {
      nonblock: true,
    },
    addclass: "dark",
    styling: "bootstrap3",
    hide: false,
    before_close: function (PNotify) {
      PNotify.update({
        title: PNotify.options.title + " - Enjoy your Stay",
        before_close: null,
      });

      PNotify.queueRemove();

      return false;
    },
  });
}

/* CUSTOM NOTIFICATION */

function init_CustomNotification() {
  console.log("run_customtabs");

  if (typeof CustomTabs === "undefined") {
    return;
  }
  console.log("init_CustomTabs");

  var cnt = 10;

  TabbedNotification = function (options) {
    var message =
      "<div id='ntf" +
      cnt +
      "' class='text alert-" +
      options.type +
      "' style='display:none'><h2><i class='fa fa-bell'></i> " +
      options.title +
      "</h2><div class='close'><a href='javascript:;' class='notification_close'><i class='fa fa-close'></i></a></div><p>" +
      options.text +
      "</p></div>";

    if (!document.getElementById("custom_notifications")) {
      alert("doesnt exists");
    } else {
      $("#custom_notifications ul.notifications").append(
        "<li><a id='ntlink" +
          cnt +
          "' class='alert-" +
          options.type +
          "' href='#ntf" +
          cnt +
          "'><i class='fa fa-bell animated shake'></i></a></li>"
      );
      $("#custom_notifications #notif-group").append(message);
      cnt++;
      CustomTabs(options);
    }
  };

  CustomTabs = function (options) {
    $(".tabbed_notifications > div").hide();
    $(".tabbed_notifications > div:first-of-type").show();
    $("#custom_notifications").removeClass("dsp_none");
    $(".notifications a").click(function (e) {
      e.preventDefault();
      var $this = $(this),
        tabbed_notifications =
          "#" + $this.parents(".notifications").data("tabbed_notifications"),
        others = $this.closest("li").siblings().children("a"),
        target = $this.attr("href");
      others.removeClass("active");
      $this.addClass("active");
      $(tabbed_notifications).children("div").hide();
      $(target).show();
    });
  };

  CustomTabs();

  var tabid = (idname = "");

  $(document).on("click", ".notification_close", function (e) {
    idname = $(this).parent().parent().attr("id");
    tabid = idname.substr(-2);
    $("#ntf" + tabid).remove();
    $("#ntlink" + tabid)
      .parent()
      .remove();
    $(".notifications a").first().addClass("active");
    $("#notif-group div").first().css("display", "block");
  });
}

/* EASYPIECHART */

function init_EasyPieChart() {
  if (typeof $.fn.easyPieChart === "undefined") {
    return;
  }
  console.log("init_EasyPieChart");

  $(".chart").easyPieChart({
    easing: "easeOutElastic",
    delay: 3000,
    barColor: "#26B99A",
    trackColor: "#fff",
    scaleColor: false,
    lineWidth: 20,
    trackWidth: 16,
    lineCap: "butt",
    onStep: function (from, to, percent) {
      $(this.el).find(".percent").text(Math.round(percent));
    },
  });
  var chart = (window.chart = $(".chart").data("easyPieChart"));
  $(".js_update").on("click", function () {
    chart.update(Math.random() * 200 - 100);
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
}

function init_charts() {
  console.log("run_charts  typeof [" + typeof Chart + "]");

  if (typeof Chart === "undefined") {
    return;
  }

  console.log("init_charts");

  Chart.defaults.legend = {
    display: false,
  };

  if ($("#canvas_line").length) {
    var canvas_line_00 = new Chart(document.getElementById("canvas_line"), {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  if ($("#canvas_line1").length) {
    var canvas_line_01 = new Chart(document.getElementById("canvas_line1"), {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  if ($("#canvas_line2").length) {
    var canvas_line_02 = new Chart(document.getElementById("canvas_line2"), {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  if ($("#canvas_line3").length) {
    var canvas_line_03 = new Chart(document.getElementById("canvas_line3"), {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  if ($("#canvas_line4").length) {
    var canvas_line_04 = new Chart(document.getElementById("canvas_line4"), {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  // Line chart

  if ($("#lineChart").length) {
    var ctx = document.getElementById("lineChart");
    var lineChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "My First dataset",
            backgroundColor: "rgba(38, 185, 154, 0.31)",
            borderColor: "rgba(38, 185, 154, 0.7)",
            pointBorderColor: "rgba(38, 185, 154, 0.7)",
            pointBackgroundColor: "rgba(38, 185, 154, 0.7)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointBorderWidth: 1,
            data: [31, 74, 6, 39, 20, 85, 7],
          },
          {
            label: "My Second dataset",
            backgroundColor: "rgba(3, 88, 106, 0.3)",
            borderColor: "rgba(3, 88, 106, 0.70)",
            pointBorderColor: "rgba(3, 88, 106, 0.70)",
            pointBackgroundColor: "rgba(3, 88, 106, 0.70)",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgba(151,187,205,1)",
            pointBorderWidth: 1,
            data: [82, 23, 66, 9, 99, 4, 2],
          },
        ],
      },
    });
  }

  // Bar chart

  if ($("#mybarChart").length) {
    var ctx = document.getElementById("mybarChart");
    var mybarChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
        ],
        datasets: [
          {
            label: "# of Votes",
            backgroundColor: "#26B99A",
            data: [51, 30, 40, 28, 92, 50, 45],
          },
          {
            label: "# of Votes",
            backgroundColor: "#03586A",
            data: [41, 56, 25, 48, 72, 34, 12],
          },
        ],
      },

      options: {
        scales: {
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
              },
            },
          ],
        },
      },
    });
  }

  // Doughnut chart

  if ($("#canvasDoughnut").length) {
    var ctx = document.getElementById("canvasDoughnut");
    var data = {
      labels: [
        "Dark Grey",
        "Purple Color",
        "Gray Color",
        "Green Color",
        "Blue Color",
      ],
      datasets: [
        {
          data: [120, 50, 140, 180, 100],
          backgroundColor: [
            "#455C73",
            "#9B59B6",
            "#BDC3C7",
            "#26B99A",
            "#3498DB",
          ],
          hoverBackgroundColor: [
            "#34495E",
            "#B370CF",
            "#CFD4D8",
            "#36CAAB",
            "#49A9EA",
          ],
        },
      ],
    };

    var canvasDoughnut = new Chart(ctx, {
      type: "doughnut",
      tooltipFillColor: "rgba(51, 51, 51, 0.55)",
      data: data,
    });
  }

  // Radar chart

  if ($("#canvasRadar").length) {
    var ctx = document.getElementById("canvasRadar");
    var data = {
      labels: [
        "Eating",
        "Drinking",
        "Sleeping",
        "Designing",
        "Coding",
        "Cycling",
        "Running",
      ],
      datasets: [
        {
          label: "My First dataset",
          backgroundColor: "rgba(3, 88, 106, 0.2)",
          borderColor: "rgba(3, 88, 106, 0.80)",
          pointBorderColor: "rgba(3, 88, 106, 0.80)",
          pointBackgroundColor: "rgba(3, 88, 106, 0.80)",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "rgba(220,220,220,1)",
          data: [65, 59, 90, 81, 56, 55, 40],
        },
        {
          label: "My Second dataset",
          backgroundColor: "rgba(38, 185, 154, 0.2)",
          borderColor: "rgba(38, 185, 154, 0.85)",
          pointColor: "rgba(38, 185, 154, 0.85)",
          pointStrokeColor: "#fff",
          pointHighlightFill: "#fff",
          pointHighlightStroke: "rgba(151,187,205,1)",
          data: [28, 48, 40, 19, 96, 27, 100],
        },
      ],
    };

    var canvasRadar = new Chart(ctx, {
      type: "radar",
      data: data,
    });
  }

  // Pie chart
  if ($("#pieChart").length) {
    var ctx = document.getElementById("pieChart");
    var data = {
      datasets: [
        {
          data: [120, 50, 140, 180, 100],
          backgroundColor: [
            "#455C73",
            "#9B59B6",
            "#BDC3C7",
            "#26B99A",
            "#3498DB",
          ],
          label: "My dataset", // for legend
        },
      ],
      labels: ["Dark Gray", "Purple", "Gray", "Green", "Blue"],
    };

    var pieChart = new Chart(ctx, {
      data: data,
      type: "pie",
      otpions: {
        legend: false,
      },
    });
  }

  // PolarArea chart

  if ($("#polarArea").length) {
    var ctx = document.getElementById("polarArea");
    var data = {
      datasets: [
        {
          data: [120, 50, 140, 180, 100],
          backgroundColor: [
            "#455C73",
            "#9B59B6",
            "#BDC3C7",
            "#26B99A",
            "#3498DB",
          ],
          label: "My dataset",
        },
      ],
      labels: ["Dark Gray", "Purple", "Gray", "Green", "Blue"],
    };

    var polarArea = new Chart(ctx, {
      data: data,
      type: "polarArea",
      options: {
        scale: {
          ticks: {
            beginAtZero: true,
          },
        },
      },
    });
  }
}

/* COMPOSE */

function init_compose() {
  if (typeof $.fn.slideToggle === "undefined") {
    return;
  }
  console.log("init_compose");

  $("#compose, .compose-close").click(function () {
    $(".compose").slideToggle();
  });
}

/* CALENDAR */

function init_calendar() {
  if (typeof $.fn.fullCalendar === "undefined") {
    return;
  }
  console.log("init_calendar");

  var date = new Date(),
    d = date.getDate(),
    m = date.getMonth(),
    y = date.getFullYear(),
    started,
    categoryClass;

  var calendar = $("#calendar").fullCalendar({
    header: {
      left: "prev,next today",
      center: "title",
      right: "month,agendaWeek,agendaDay,listMonth",
    },
    selectable: true,
    selectHelper: true,
    select: function (start, end, allDay) {
      $("#fc_create").click();

      started = start;
      ended = end;

      $(".antosubmit").on("click", function () {
        var title = $("#title").val();
        if (end) {
          ended = end;
        }

        categoryClass = $("#event_type").val();

        if (title) {
          calendar.fullCalendar(
            "renderEvent",
            {
              title: title,
              start: started,
              end: end,
              allDay: allDay,
            },
            true // make the event "stick"
          );
        }

        $("#title").val("");

        calendar.fullCalendar("unselect");

        $(".antoclose").click();

        return false;
      });
    },
    eventClick: function (calEvent, jsEvent, view) {
      $("#fc_edit").click();
      $("#title2").val(calEvent.title);

      categoryClass = $("#event_type").val();

      $(".antosubmit2").on("click", function () {
        calEvent.title = $("#title2").val();

        calendar.fullCalendar("updateEvent", calEvent);
        $(".antoclose2").click();
      });

      calendar.fullCalendar("unselect");
    },
    editable: true,
    events: [
      {
        title: "All Day Event",
        start: new Date(y, m, 1),
      },
      {
        title: "Long Event",
        start: new Date(y, m, d - 5),
        end: new Date(y, m, d - 2),
      },
      {
        title: "Meeting",
        start: new Date(y, m, d, 10, 30),
        allDay: false,
      },
      {
        title: "Lunch",
        start: new Date(y, m, d + 14, 12, 0),
        end: new Date(y, m, d, 14, 0),
        allDay: false,
      },
      {
        title: "Birthday Party",
        start: new Date(y, m, d + 1, 19, 0),
        end: new Date(y, m, d + 1, 22, 30),
        allDay: false,
      },
      {
        title: "Click for Google",
        start: new Date(y, m, 28),
        end: new Date(y, m, 29),
        url: "http://google.com/",
      },
    ],
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

/* CHART - MORRIS  */

function init_morris_charts() {
  if (typeof Morris === "undefined") {
    return;
  }
  console.log("init_morris_charts");

  if ($("#graph_bar").length) {
    Morris.Bar({
      element: "graph_bar",
      data: [
        { device: "iPhone 4", geekbench: 380 },
        { device: "iPhone 4S", geekbench: 655 },
        { device: "iPhone 3GS", geekbench: 275 },
        { device: "iPhone 5", geekbench: 1571 },
        { device: "iPhone 5S", geekbench: 655 },
        { device: "iPhone 6", geekbench: 2154 },
        { device: "iPhone 6 Plus", geekbench: 1144 },
        { device: "iPhone 6S", geekbench: 2371 },
        { device: "iPhone 6S Plus", geekbench: 1471 },
        { device: "Other", geekbench: 1371 },
      ],
      xkey: "device",
      ykeys: ["geekbench"],
      labels: ["Geekbench"],
      barRatio: 0.4,
      barColors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      xLabelAngle: 35,
      hideHover: "auto",
      resize: true,
    });
  }

  if ($("#graph_bar_group").length) {
    Morris.Bar({
      element: "graph_bar_group",
      data: [
        { period: "2016-10-01", licensed: 807, sorned: 660 },
        { period: "2016-09-30", licensed: 1251, sorned: 729 },
        { period: "2016-09-29", licensed: 1769, sorned: 1018 },
        { period: "2016-09-20", licensed: 2246, sorned: 1461 },
        { period: "2016-09-19", licensed: 2657, sorned: 1967 },
        { period: "2016-09-18", licensed: 3148, sorned: 2627 },
        { period: "2016-09-17", licensed: 3471, sorned: 3740 },
        { period: "2016-09-16", licensed: 2871, sorned: 2216 },
        { period: "2016-09-15", licensed: 2401, sorned: 1656 },
        { period: "2016-09-10", licensed: 2115, sorned: 1022 },
      ],
      xkey: "period",
      barColors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      ykeys: ["licensed", "sorned"],
      labels: ["Licensed", "SORN"],
      hideHover: "auto",
      xLabelAngle: 60,
      resize: true,
    });
  }

  if ($("#graphx").length) {
    Morris.Bar({
      element: "graphx",
      data: [
        { x: "2015 Q1", y: 2, z: 3, a: 4 },
        { x: "2015 Q2", y: 3, z: 5, a: 6 },
        { x: "2015 Q3", y: 4, z: 3, a: 2 },
        { x: "2015 Q4", y: 2, z: 4, a: 5 },
      ],
      xkey: "x",
      ykeys: ["y", "z", "a"],
      barColors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      hideHover: "auto",
      labels: ["Y", "Z", "A"],
      resize: true,
    }).on("click", function (i, row) {
      console.log(i, row);
    });
  }

  if ($("#graph_area").length) {
    Morris.Area({
      element: "graph_area",
      data: [
        { period: "2014 Q1", iphone: 2666, ipad: null, itouch: 2647 },
        { period: "2014 Q2", iphone: 2778, ipad: 2294, itouch: 2441 },
        { period: "2014 Q3", iphone: 4912, ipad: 1969, itouch: 2501 },
        { period: "2014 Q4", iphone: 3767, ipad: 3597, itouch: 5689 },
        { period: "2015 Q1", iphone: 6810, ipad: 1914, itouch: 2293 },
        { period: "2015 Q2", iphone: 5670, ipad: 4293, itouch: 1881 },
        { period: "2015 Q3", iphone: 4820, ipad: 3795, itouch: 1588 },
        { period: "2015 Q4", iphone: 15073, ipad: 5967, itouch: 5175 },
        { period: "2016 Q1", iphone: 10687, ipad: 4460, itouch: 2028 },
        { period: "2016 Q2", iphone: 8432, ipad: 5713, itouch: 1791 },
      ],
      xkey: "period",
      ykeys: ["iphone", "ipad", "itouch"],
      lineColors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      labels: ["iPhone", "iPad", "iPod Touch"],
      pointSize: 2,
      hideHover: "auto",
      resize: true,
    });
  }

  if ($("#graph_donut").length) {
    Morris.Donut({
      element: "graph_donut",
      data: [
        { label: "Jam", value: 25 },
        { label: "Frosted", value: 40 },
        { label: "Custard", value: 25 },
        { label: "Sugar", value: 10 },
      ],
      colors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      formatter: function (y) {
        return y + "%";
      },
      resize: true,
    });
  }

  if ($("#graph_line").length) {
    Morris.Line({
      element: "graph_line",
      xkey: "year",
      ykeys: ["value"],
      labels: ["Value"],
      hideHover: "auto",
      lineColors: ["#26B99A", "#34495E", "#ACADAC", "#3498DB"],
      data: [
        { year: "2012", value: 20 },
        { year: "2013", value: 10 },
        { year: "2014", value: 5 },
        { year: "2015", value: 5 },
        { year: "2016", value: 20 },
      ],
      resize: true,
    });

    $MENU_TOGGLE.on("click", function () {
      $(window).resize();
    });
  }
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
  init_SmartWizard();
  init_EasyPieChart();
  init_charts();
  init_morris_charts();
  init_validator();
  init_DataTables();
  init_chart_doughnut();
  init_PNotify();
  init_calendar();
  init_compose();
  init_CustomNotification();
});
