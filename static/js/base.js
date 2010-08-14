$(function(){

    $('.play').toggle(function(){
        $(this).removeClass('play').addClass('pause');
    }, function() {
        $(this).removeClass('pause').addClass('play');
    });

    Uploader.init();

    Playlist.init();
});

var Uploader = {
    $btn: null,

    init: function() {
        var self = this;
        this.$btn = $('#btn_upload');
        this.$btn.uploadify({
            uploader: '/js/uploadify.swf',
            fileDataName: 'track_file',
            script: '/upload/',
            auto: true,
            multi: false,
            fileDesc: 'Audio files',
            fileExt: '*.mp3',
            sizeLimit: 1024*1024*10,
            buttonImg: '/imgs/btn_upload_sprite.png',
            cancelImg: '/imgs/btn_upload_cancel.png',            
            rollover: true,
            wmode: 'transparent',
            width: this.$btn.width(),
            height: this.$btn.height(),
            onSelect: function(){ return self.on_select.apply(self, arguments); },
            onComplete: function(){ return self.on_complete.apply(self, arguments); }
        });
    },

    on_select: function(event, queue_id, file_obj) {
        var fileName = file_obj.name;
        fileName = fileName.substring(0, fileName.lastIndexOf('.'));
        fileName = prompt('Please, enter track name:', fileName);
        if (!fileName) {
            this.$tbn.uploadifyCancel(queue_id);
        }
        this.$btn.uploadifySettings('scriptData', {name: fileName});
    },

    on_complete: function(event, queue_id, file_obj, response, data) {
        try {
            var $container = $('#' + this.$btn.attr('id') + queue_id);
            response = eval('(' + response + ')');
            if (response.status == 'ok') {
                this._success($container, response);
            } else {
                this._error($container, response);
            }
        } catch (e) {
            this._error($container);
        }
        $container.find('.cancel a').click(function(event){
            $container.fadeOut(250, function() { $(this).remove()});
            event.preventDefault();
        });
        return false;
    },

    _error: function($container, response) {
        var error = ' - Error uploading file. Try again.';
        if (response && response.errors && response.errors['track_file']) {
            error = ' - Error: ' + response.errors['track_file'][0].toLowerCase();
        }
        $container.find('.percentage').text(error);
    },

    _success: function($container, response) {
        response.track.play_time *= 1000;
        var playTime = new Date(response.track.play_time);
        $container.find('.percentage').html(' - Completed<br />Your track will be played at <strong>' + playTime + '</strong>');
    }
};

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
        $.get('/tracks/', function(data) {
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
};
