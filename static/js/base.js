$(function(){
    Uploader.init();

    Recorder.init();

    Player.init();

    Playlist.init();
    
    NowPlaying.init();

    Tweets.init();
});

function site_url() {
    return document.location.protocol + '//' + document.location.host;
}

function setStatus_RP(str,num) {
    if (num == Recorder.LOADED) {
        Recorder.start();
    }
    window.console && window.console.debug(str,num);
}
function report_RP(s,num)
{
    alert(s);
}
function setTimer_RP(s)	{

}

var utils = {
    print_time: function(seconds) {
        return Math.floor(seconds/60) + ':' + utils.str_lpad(seconds % 60, 2, '0');
    },

    str_lpad: function(str, len, pad) {
        str = str + '';
        if (len + 1 > str.length) {
            return Array(len + 1 - str.length).join(pad) + str;
        }
        return str;
    }
};

var Recorder = {
    MAX_TRACK_LEN: 20000, /* in milliseconds */
    LOADED: 100,

    /** @type HTMLAppletElement */
    _applet: null,
    /** @type handler */
    _stop_timeout: null,

    init: function() {
        $('#btn_rec').click(function() {
            Recorder.toggle();
        })
    },

    _init_applet: function() {
        $('#layout_footer').append(
            '<applet code="RPApplet.class" archive="/js/RPAppletMp3.jar" codebase="." align="MIDDLE" width=374 height=24 name="RPApplet" mayscript>'
            + '<param name="cabbase" value="/js/RPAppletMp3.cab">'
            + '<param name="Registration" value="demo">'
            + '<param name="ServerScript" value="' + site_url() + '/upload/">'
            + '<param name="OverRecord" value="true">'
            + '<PARAM NAME = "VoiceServerFolder"	VALUE = ".">'
            + '<PARAM NAME = "TimeLimit"	VALUE = "1800">'
            + '<PARAM NAME = "UserServerFolder"	VALUE = ".">'
            + '<PARAM NAME = "UserPostVariables"	VALUE = "name">'
            + '<PARAM NAME = "name"			VALUE = "voice">'
            + '<param name="BlockSize" value="1024000">'
            + '<param name="InterfaceType" value="JS">'
            + '<param name="name" value="voice">'
            + '<param name="Sampling_frequency" value="22050">'
            + '<param name="Bitrate" value="64">'
            + '<param name="backgroudColor" value="c0c0c0">'
            + '<param name="indicatorLevel1" value="4664f0">'
            + '<param name="indicatorLevel2" value="28c814">'
            + '<param name="indicatorLevel3" value="f03250">'
            + '</applet>'
        );
        this._applet = document.RPApplet;
    },

    toggle: function() {
        this._stop_timeout ? this.stop() : this.start();
    },

    start: function() {
        if (!this._applet) {
            this._init_applet();
            return;
        }
        this._applet.RECORD();
        
        this._stop_timeout = setTimeout(function() {
            Recorder.stop();
        }, this.MAX_TRACK_LEN);
        
        this._progress.start();
    },

    stop: function() {
        try {
        if (this._stop_timeout) {
            this._stop_timeout = clearTimeout(this._stop_timeout);
        }

        this._applet.STOP_RP();
        this._progress.stop(); // If called before prompt, animation not shown
        
        Uploader.ask_data('', function(fileName, twitter) {
            if (!fileName) {
                return;
            }
            this._applet.SETPARAMETER('name', file_name);
            this._applet.SETPARAMETER('twitter', twitter);
            this._applet.UPLOAD('voice');            
        });
        } catch(e) {
            alert(e)
        }
    },

    _progress: {
        INTERVAL: 200, /* in milliseconds */

        /** @type handler */
        _interval: null,
        /** @type int */
        _passed: null,
        /** @type jQuery */
        _$progressbar: null,

        start: function() {
            this._interval = setInterval(function(){
                Recorder._progress._on_progress();
            }, this.INTERVAL);
            this._passed = 0;

            if (!this._$progressbar) {
                this._$progressbar = $('#record_progress');
            }
            this._$progressbar.show();
        },

        _on_progress: function() {
            this._passed += this.INTERVAL;
            var percent = this._passed / Recorder.MAX_TRACK_LEN * 100;
            this._$progressbar.children().css('width', percent + '%');
        },

        stop: function() {
            if (this._interval) {
                this._interval = clearInterval(this._interval);
                this._$progressbar.fadeOut('fast');
            }
        }
    }

}

var Uploader = {
    $btn: null,

    init: function() {
        var self = this;
        this.$btn = $('#btn_upload');
        this.$btn.uploadify({
            uploader: '/js/uploadify.swf',
            fileDataName: 'track_file',
            script: '/upload/',
            auto: false,
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
        var self = this;
        var fileName = file_obj.name;
        fileName = fileName.substring(0, fileName.lastIndexOf('.'));
        
        self.ask_data(fileName, function(fileName, twitter) {
            if (!fileName) {
                self.$btn.uploadifyCancel(queue_id);
            }
            self.$btn.uploadifySettings('scriptData', {name: fileName, twitter: twitter});
            self.$btn.uploadifyUpload();
        });
    },

    ask_data: function(fileName, callback) {
        var namef = $('#js_askbox #js_name');
        var twitf = $('#js_askbox #js_twitter')
        namef.val(fileName);
        twitf.val('');

        $('#js_askbox').show();
        $('#js_askbox .save').unbind('click');
        $('#js_askbox .save').click(function() {
            $('#js_askbox').hide();
            if (callback) {
                callback(namef.val(), twitf.val());
            }
        });
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
            data = raw_data;
        data['length'] = utils.print_time(data['length']);
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
    },

    update: function() {
        var self = this;

        if (self._cur_track && self._cur_track.pos_p <= 99) {
            self._cur_track.position += (new Date().getTime() - self._last_time) / 1000;
            self._cur_track.pos_p = Math.floor(self._cur_track.position / self._cur_track.length * 100);
            $('.progress', self.$block).css('width', self._cur_track.pos_p + '%');
            setTimeout(function() {self.update()}, 1000);

            self._last_time = new Date().getTime()
        } else {
            $.getJSON('/now_playing/', function(track) {
                self.$block.empty();

                if (track && track[0]) {
                    track = track[0];
                    track.pos_p = Math.floor(track['position'] / track.length * 100);

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
        data['length_m'] = utils.print_time(data['length']);
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

    template: '<li><img src="%profile_image_url%" />%text%<abbr class="timeago" title="%created_at%"></abbr></li>',

    render: function(data) {
        var self = this;

        data['text'] = data['text'].replace(/@([0-9a-zA-Z_]+)/g, '<a href="http://twitter.com/$1">@$1</a>')
        data['text'] = data['text'].replace(/(#[0-9a-zA-Z_]+)/g, '<a href="http://twitter.com/search?q=$1">$1</a>')

        el = self.template;
        for (key in data) {
            el = el.replace('%' + key  + '%', data[key]);
        }
        return $(el);
    }
}
