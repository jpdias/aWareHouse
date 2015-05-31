/// <reference path="../typings/jquery/jquery.d.ts"/>
var loadData;

$.getJSON("/api/config", function(data) {
  loadData = data;
  for (var key in data) {
    for (var keyCode in data[key]) {
      var sel = "#" + keyCode + "";
      $(sel).val(data[key][keyCode]);
    }
  }
});

$("#submit").on("click", function() {
  for (var key in loadData) {
    for (var keyCode in loadData[key]) {
      var sel = "#" + keyCode + "";
      var value = $(sel).val();
      if (!isNaN(value)){
        value = Number(value);
      }
      loadData[key][keyCode] = value;
    }
  }

  if (loadData && loadData["warnings"])
    loadData["warnings"].clear();

  var rows = $("#warnings").children();
  for (var i = 0; i < rows.length; i++) {
    var row = $(rows[i]);
    var inputs = row.find("[name]");
    
    var warning = {};
    for (var j = 0; j < inputs.length; j++) {
      var input = $(inputs[j]);
      warning[input.attr("name")] = input.val();
    }
    
    if (warning.value.length == 0)
      continue;
      
    warning.value = parseInt(warning.value);
    loadData["warnings"].push(warning);
  }

  $.ajax({
    type: "POST",
    url: "/api/config",
    data: JSON.stringify(loadData, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    success: function(result) {
      console.log(result);
    }
  });
});

$(".add_warning").on("click", function() {
  $(this).parent().clone(true, true).insertAfter(".warning:last");
});

$(".remove_warning").on("click", function() {
  if ($(this).parent().parent().children().length <= 1)
    return;

  $(this).parent().remove();
});
