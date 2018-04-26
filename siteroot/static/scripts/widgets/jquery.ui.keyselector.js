

var keyselector = {
    _create: function() {
        /* widget initialisation */
        var self = this;
        var opts = self.options;
        var el = self.element;

        var jsFileLocation = $('script[src*="jquery.ui.querybar.js"]').attr('src');  // the js file path
        jsFileLocation = jsFileLocation.replace('jquery.ui.querybar.js', '');   // the js folder path

        el.addClass('selectKeywordControlWrapper');
        el.hide();

        var jsFileLocation = $('script[src*="jquery.ui.keyselector.js"]').attr('src');  // the js file path
        jsFileLocation = jsFileLocation.replace('jquery.ui.keyselector.js', '');   // the js folder path

        /* prepend the control structure */
        el.prepend('<select id="selectKeyControl" class="select2-key-selector" style="width: 100%"></select>\
                   <div id="selectKeySubmitContainer" class="selectKeyContainer">\
                   <input id="selectKeyCancel" value="Cancel" type="button" />\
                   <input id="selectKeySubmit" value="Submit" type="button" />\
                   </div>\
                   <script>\
                    $(".select2-key-selector").select2({\
                      multiple: "multiple",\
                      ajax: {\
                        url: "keyword_list",\
                        dataType: "json"\
                      }\
                    });\
                    </script>\
                   ');

        /* event handlers */
        el.find('#selectKeyCancel').click(function(e) {
            /* provide handle for callback */
            self._trigger('hidden');
            el.find('#selectKeyControl').val(null).trigger('change')
            el.slideUp('fast', function() {
                opts._cancelled = true;
            });
        });
        el.find('#selectKeySubmit').click(function(e) {
            /* provide handle for callback */
            keys = '';
            data = el.find('#selectKeyControl').select2('data');
            if (data.length>0) {
                for (var i = 0; i < data.length; i++)  {
                    if (keys != '') keys = keys + ',';
                    keys = keys + data[i].text;
                }
                self._trigger('choosenkey', 0, keys);
            }
            self._trigger('hidden');
            el.find('#selectKeyControl').val(null).trigger('change')
            el.slideUp('fast');
        });
    },
    show: function() {
        this.element.slideDown('fast');
    },
    hide: function() {
        /* provide handle for callback */
        this._trigger('hidden');

        this.element.slideUp('fast');
    },
    toggle: function() {
        if (this.element.is(':visible')) {
            this.hide();
        } else {
            this.show();
        }
    },
    options: {
        errorJsonField: 'Error',
        _cancelled: false,
    }
};
$.widget("ui.keyselector", keyselector);
