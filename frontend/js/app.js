// Foundation JavaScript
// Documentation can be found at: http://foundation.zurb.com/docs
$(document).foundation();

var nowPlayingSocket = new WebSocket("ws://localhost:8000");
nowPlayingSocket.onmessage = function (event) {
  console.log(event.data);
  var metadata = JSON.parse(event.data);
  if(metadata.updateType === 'playStatus') {
    var playStatus = metadata.playing.toLowerCase();
    if(playStatus.indexOf("play") > -1) {
      $('#playicon').attr('class', 'fi-play');
      $('#albumartcontainer').css('opacity', 1);
      $('#metadatacontainer').attr('class', '');
    }else if(playStatus.indexOf("pause") > -1){
      $('#playicon').attr('class', 'fi-pause');
      $('#albumartcontainer').css('opacity', 0.5);
      $('#metadatacontainer').attr('class', 'paused');
    }else if(playStatus.indexOf("stop") > -1) {
      $('#playicon').attr('class', 'fi-stop');
      $('#albumartcontainer').css('opacity', 0.5);
      $('#metadatacontainer').attr('class', 'paused');
    } else {
      $('#playicon').attr('class', '');
      $('#albumartcontainer').css('opacity', 0.5);
      $('#metadatacontainer').attr('class', 'paused');
    }
  }
  if(metadata.updateType === 'track') {
    $('#track').html(metadata.track);
    $('#albumartcontainer img').attr('src', metadata.albumart);
    $('#artist').html(metadata.artist);
    $('#album').html(metadata.album);
  }
}