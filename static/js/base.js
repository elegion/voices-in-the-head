$(function(){

    $('.play').toggle(function(){
        $(this).removeClass('play').addClass('pause');
    }, function() {
        $(this).removeClass('pause').addClass('play');
    });

    Playlist.init();
});

var Playlist = {
    $playlist: null,
    $playlist_wrapper: null,
    $loader: null,
    
    init: function() {
        var self = this;
        
        self._last_tracks = {};
        
        self.$playlist = $('#js_playlist');
        self.$playlist_wrapper = $('#js_playlist_wrapper');
        self.$loader = $('.ajax_loader', self.$playlist_wrapper);    
        
        self.update_playlist();
        setInterval(function() {self.update_playlist()}, 10000);
    },
    
    update_playlist: function() {
        var self = this;
        $.get('/tracks', function(data) {
            var tracks = eval('[' + data + ']')[0];
            self.fill_playlist(tracks);
            self.$loader.hide();
            self.$playlist.show();
        });        
    },
    
    li_template: '<li class="%odd%" id="track_%id%">\
        <a class="control play"></a>\
        <span class="track">%name%<q></q></span>\
        <a class="control delete"></a>\
        <span class="duration">%length%</span>\
    </li>',
    
    render_li: function(raw_data, pos) {
        li = this.li_template;
        data = raw_data;
        var l = data['length'];
        data['length'] = Math.floor(l/60) + ':' + l % 60;
        data['odd'] = pos % 2 == 0 ? 'odd' : 'even';
        for (var datakey in data) {
            li = li.replace('%' + datakey + '%', data[datakey]);
        }        
        return $(li);
    },
    
    fill_playlist: function(rawtracks) {
        var self = this;

        var tracks = {};
        for (var i=0; i<rawtracks.length; i++) {
            tracks[rawtracks[i].id] = rawtracks[i];
        }

        // remove deleted
        for (var id in self._last_tracks) {            
            if (!(id in tracks)) {
                $('#track_' + id).remove();
            }
        }
        
        // add new
        for (var i=0; i<rawtracks.length; i++) {            
            if (!(rawtracks[i].id in self._last_tracks)) {
                var el = this.render_li(rawtracks[i], i);
                if (i == 0) {
                    this.$playlist.append(el);
                } else {
                    $('#track_' + rawtracks[i-1].id).after(el);
                }
            }
        }           
        
        self._last_tracks = tracks;
    }
}