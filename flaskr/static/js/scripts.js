function sendData(tstamp, v, vname){
        $.post( "/save", { timestamp: tstamp, value: v, videoname: vname})
            .done(function( data ) {
                console.log(data);
            });
}

$(function () {
  var timestamp;
  var slider_value;
  $("#slider-vertical").slider({
    orientation: "vertical",
    range: "min",
    min: 0,
    max: 100,
    value: 60,
    slide: function (event, ui) {
      $("#amount").val(ui.value);
      slider_value = ui.value;
    },
    stop: function(event) {
      console.log(player.getCurrentTime());
      sendData(player.getCurrentTime(), slider_value, player.getVideoUrl());
    }
  });
  $("#amount").val($("#slider-vertical").slider("value"));
  //$("#timestamp").val($("#slider-vertical").slider("timestamp"));
/* 
  $("#time").val($("#slider-vertical")).slider("time"));
    range: "min",
    stop: function( event, ui ) {player.getTimeStamp());}
  
  }); */
});