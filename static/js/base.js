$(function(){

    $('.play').toggle(function(){
        $(this).removeClass('play').addClass('pause');
    }, function() {
        $(this).removeClass('pause').addClass('play');
    });

});