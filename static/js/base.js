$(function(){
    Uploader.init();

    Player.init();

    Playlist.init();
    NowPlaying.init();
    
    Tweets.init();
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

var Player = {
    $player: null,
    $current: null,

    init: function() {
        var self = this;
        this.$player = $('#jquery_jplayer').jPlayer({
            customCssIds: true
        }).jPlayer('onProgressChange', function() {
            self._on_progress_change.apply(self, arguments);
        });
    },

    toggle: function($container, url) {
        if (this.$current && this.$current==$container) {
            this.pause($container);
            return;
        } else if (this.$current) {
            this.pause(this.$current);
        }
        this.play($container, url);
    },

    _on_progress_change: function(lp,ppr,ppa,pt,tt) {
        if (!this.$current) {
            return;
        }
        this.$current.find('.progress span').css('width', ppa + '%');
    },

    play: function($container, url) {
        if (this.$current) {
            this.pause(this.$current);
        }
        this.$player.jPlayer('setFile', url).jPlayer('play');

        $container.addClass('playing');
        this.$current = $container;
    },

    pause: function($container) {
        this.$player.jPlayer('pause');

        $container.removeClass('playing');

        this.$current = null;
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
        <a class="control play_pause"></a>\
        <span class="track">%name%<span class="progress"><span></span></span><q></q></span>\
        <a class="control delete %voted%" title="Vote against this track"></a>\
        <span class="duration">%length%</span>\
    </li>',

    render_li: function(raw_data, pos) {
        var li = this.li_template,
            data = raw_data,
            l = data['length'];
        data['length'] = Math.floor(l/60) + ':' + l % 60;
        data['odd'] = pos % 2 == 0 ? 'odd' : 'even';
        for (var datakey in data) {
            li = li.replace('%' + datakey + '%', data[datakey]);
        }

        // Bind events
        li = $(li);
        li.find('.control.play_pause').click(function(){
            Player.toggle(li, raw_data.track_file);
        });
        li.find('.control.delete').click(function() {
            var self = this;
            $.post('/vote/', {'track_id': raw_data.id}, function(data) {
                var data = eval('('+ data + ')');
                if (data['error']) {
                    alert(data['error']);
                } else if (data['result'] == 'delete') {
                    li.remove();
                } else if (data['result'] == 'ok') {
                    $(self).addClass('voted');
                }
            });
        });
        
        if (!raw_data.can_vote) {
            li.find('.delete').remove();
        }
        return li;
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


var NowPlaying = {
    $block: null,
    
    init: function() {
        var self = this;
        
        self.$block = $('#now_playing');

        self.update();
        setTimeout(function() {self.update()}, 1000);
    },
    
    update: function() {
        var self = this;
        
        if (self._cur_track && self._cur_track.pos_p <= 99) {
            self._cur_track.position += (new Date().getTime() - self._last_time) / 1000;
            self._cur_track.pos_p = Math.floor(self._cur_track.position / self._cur_track['length'] * 100);
            if (!self._cur_track.pos_p) {
                self._cur_track.pos_p = 0;
            }
            $('.progress', self.$block).css('width', self._cur_track.pos_p + '%');
            setTimeout(function() {self.update()}, 1000);

            self._last_time = new Date().getTime()
        } else {
            $.get('/now_playing/', function(data) {
                var track = eval('(' + data + ')');
                self.$block.empty();
                
                if (track && track[0]) {
                    track = track[0];
                    track.pos_p =
                        Math.floor(track['position'] / track.length * 100);
                    
                    self.$block.append(self.render(track));
                
                    self._cur_track = track;
                    setTimeout(function() {self.update()}, 1000);
                    self._last_time = new Date().getTime();
                } else {
                    setTimeout(function() {self.update()}, 10000);
                }
            });
        }
    },
    
    template: '<div id="track_%id%">\
        <span class="track">%name%<q></q></span>\
        <span class="duration">%length_m%</span>\
        <div class="progress" style="width: %pos_p%%;"></div>\
    </div>',
    
    render: function(raw_data) {
        var div = this.template;
        data = raw_data;
        var l = data['length'];
        data['length_m'] = Math.floor(l/60) + ':' + l % 60;
        for (var datakey in data) {
            div = div.replace('%' + datakey + '%', data[datakey]);
        }
        return $(div);        
    }
};


var Tweets = {
    api_q: '#inthehead',
    api_rpp: 20,
    api_url: 'http://search.twitter.com/search.json',
    $container: null,
    
    init: function() {
        var self = this;
        self._last_id = 0;
        
        self.$container = $('#js_tweets');
        
        self.update();
        setInterval(function() {self.update()}, 10000);
    },
    
    update: function() {
        var self = this;
        
        $.getJSON(self.api_url + '?callback=?',
            {'rpp': self.api_rpp, 'q': self.api_q, 'since_id': self._last_id}, function(data){
                self._last_id = data.max_id;
                for(var i=data.results.length - 1; i >= 0; i--) {
                    self.$container.prepend(self.render(data.results[i]));
                }
                self.$container.find('li:gt(' + (self.api_rpp - 1) + ')').remove();
                $('abbr.timeago').timeago();
        });
    },
    
    template: '<li><img src="%profile_image_url%"></img>%text%<abbr class="timeago" title="%created_at%"></abbr></li>',
    
    render: function(data) {
        var self = this;
        
        data['text'] = data['text'].replace(/@([0-9a-zA-Z_]+)/g, '<a href="http://twitter.com/$1">@$1</a>')
        data['text'] = data['text'].replace(/(#[0-9a-zA-Z_]+)/g, '<a href="http://twitter.com/search?q=$1">$1</a>')
        
        el = self.template;
        for (key in data) {            
            el = el.replace('%' + key  + '%', data[key]);
        }
        return $(el);
    },
}