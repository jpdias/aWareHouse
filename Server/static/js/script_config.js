var loadData;

$.getJSON("/api/config", function(data) {
  loadData = data;
  for (var key in data.config) {
    for (var keycode in data.config[key]) {
      var sel = "#" + keycode + "";
      $(sel).val(data.config[key][keycode]);
    }
  }
});

$("#submit").on("click", function() {
  for (var key in loadData.config) {
    for (var keycode in loadData.config[key]) {
      var sel = "#" + keycode + "";
      var value = $(sel).val();
      if(!isNaN(value)){
        value = Number(value);
      }
      loadData.config[key][keycode] = value;
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
