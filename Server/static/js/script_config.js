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
