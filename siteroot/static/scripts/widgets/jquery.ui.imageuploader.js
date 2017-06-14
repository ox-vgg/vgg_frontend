/* IMAGEUPLOADER JQUERY UI WIDGET
 * ----------------------------------------------------------------------------
 * This JQuery UI widget provides an interface for picking and uploading an image,
 * either from a web URL or from disk.
 *
 * As with all JQuery UI widgets, it can be attached to any container div as follows:
 *
 * >>  $('#containerDivId').imageuploader();
 *
 * The widget must be used in conjunction with a backend function which accepts
 * a request of the following form:
 *
 * >> /{uploadAction}?{uploadFileField}={output from HTML file picker control}
 * OR:
 * >> /{uploadAction}?{uploadUrlField}={image URL from web}
 *
 * ...and returns a URL to the uploaded image stored on the webserver.
 *
 * When such a URL is returned, the 'imageuploaderurlreturned' callback
 * is triggered which can be caught as follows:
 *
 * >> $('#imupControl').bind('imageuploaderurlreturned', function(event, url) {});
 *
 * ...to process the return value.
 *
 * This widget is best used with the complementary jquery.ui.querybar widget
 *
 * Dependencies:
 * - JQuery and JQuery UI (widgets module
 * - JQuery Forms (located at lib/jquery.form.js)
 * - Associated stylesheet (jquery.ui.imageuploader.css) and files
 *   (contained in jquery.ui.imageuploader directory)
 */

var imageuploader = {
    _create: function() {
        /* widget initialisation */
        var self = this;
        var opts = self.options;
        var el = self.element;

        var jsFileLocation = $('script[src*="jquery.ui.querybar.js"]').attr('src');  // the js file path
        jsFileLocation = jsFileLocation.replace('jquery.ui.querybar.js', '');   // the js folder path

        el.addClass('imupControlWrapper');
        el.hide();

        var jsFileLocation = $('script[src*="jquery.ui.imageuploader.js"]').attr('src');  // the js file path
        jsFileLocation = jsFileLocation.replace('jquery.ui.imageuploader.js', '');   // the js folder path

        /* prepend the control structure */
        el.prepend('<form id="imupUploadForm" enctype="multipart/form-data" action="'+self.options.uploadAction+'" method="POST">\
                   <ul id="imupTabbar">\
                   <li id="imupTabbarUrl" class="imupTabbarSelected">Paste image URL</li>\
                   <li id="imupTabbarFile">Upload an image</li>\
                   </ul>\
                   <div id="imupUploadUrlContainer" class="imupContainer">\
                   <input id="imupUploadUrl" name="'+self.options.uploadUrlField+'" type="text" />\
                   </div>\
                   <div id="imupUploadFileContainer" class="imupContainer">\
                   <input id="imupUploadFile" name="'+self.options.uploadFileField+'" type="file" />\
                   </div>\
                   <div id="imupProcessingContainer" class="imupContainer">\
                   <img src="'+jsFileLocation+'jquery.ui.imageuploader/spinner.gif" />Processing...\
                   </div>\
                   <div id="imupSubmitContainer" class="imupContainer">\
                   <input id="imupCancel" value="Cancel" type="button" />\
                   <input id="imupSubmit" value="Upload" type="submit" />\
                   </div>\
                   <div id="imupOutput"></div>\
                   </form>');

        el.find('#imupUploadFileContainer').hide();
        el.find('#imupUploadFileContainer').attr('disabled','disabled');

        /* event handlers */
        el.find('#imupTabbarUrl').click(function(e) {
            if (!el.find('#imupProcessingContainer').is(':visible')) {
                self._switchToUrlTab();
            }
        });
        el.find('#imupTabbarFile').click(function(e) {
            if (!el.find('#imupProcessingContainer').is(':visible')) {
                self._switchToFileTab();
            }
        });
        el.find('#imupCancel').click(function(e) {
            /* provide handle for callback */
            self._trigger('hidden');

            el.slideUp('fast', function() {
                opts._cancelled = true;
                opts._uploading = false;
                self._prepareForNewRequest();
            });
        });

        el.find('#imupUploadForm').submit(function() {

            var options = {
                target: '#imupOutput',
                dataType: 'json',
                success: function(data){
                    opts._uploading = false;
                    self.hide();
                    self._prepareForNewRequest();

                    var url = '';
                    if (self.options.returnUrlJsonField in data) {
                        url = data[self.options.returnUrlJsonField];
                    }
                    if (url == '') {
                        $.getScript(jsFileLocation+'jquery.ui.imageuploader/appriseimup-1.5.min.js', function() {
                            srcurl = '';
                            if (self.options.returnUrlSource in data) srcurl = data[self.options.returnUrlSource];
                            if (srcurl != '') {
                                var alertstr = 'The selected image could not be loaded or was invalid:<br/><span style="font-size:small;">'+srcurl+'</span>';
                                appriseimup(alertstr);
                            } else {
                                var alertstr = 'The selected image could not be uploaded';
                                appriseimup(alertstr);
                            }
                        });
                        opts._cancelled = false;
                        opts._uploading = false;
                        self._switchToUrlTab();
                    } else {
                        /* provide handle for callback */
                        self._trigger('urlreturned', 0, url);
                    }
                }
            }

            opts._cancelled = false;
            opts._uploading = true;
            $(this).ajaxSubmit(options);

            el.find('#imupSubmit').attr('disabled','disabled');
            el.find('#imupUploadUrlContainer').hide();
            el.find('#imupUploadFileContainer').hide();
            el.find('#imupProcessingContainer').show();
            el.find('#imupTabbar').slideUp('fast');

            return false;
        });
    },
    show: function() {
        this.element.slideDown('fast');

        if (this.element.find('#imupTabbarUrl').is('.imupTabbarSelected')) {
            this.element.find('#imupUploadUrl').focus();
        } else {
            this.element.find('#imupUploadFile').focus();
        }
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
    _switchToUrlTab: function() {
        if (!this.options._uploading) {
            this.element.find('#imupTabbarUrl').addClass('imupTabbarSelected');
            this.element.find('#imupTabbarFile').removeClass('imupTabbarSelected');
            document.getElementById("imupUploadFile").value = "";
            this.element.find('#imupUploadFileContainer').hide();
            this.element.find('#imupUploadFileContainer').attr('disabled','disabled');
            this.element.find('#imupUploadUrlContainer').show();
            this.element.find('#imupUploadUrlContainer').removeAttr('disabled');
            this.element.find('#imupUploadUrl').focus();
        }
    },
    _switchToFileTab: function() {
        if (!this.options._uploading) {
            this.element.find('#imupTabbarFile').addClass('imupTabbarSelected');
            this.element.find('#imupTabbarUrl').removeClass('imupTabbarSelected');
            document.getElementById("imupUploadUrl").value = "";
            this.element.find('#imupUploadUrlContainer').hide();
            this.element.find('#imupUploadUrlContainer').attr('disabled','disabled');
            this.element.find('#imupUploadFileContainer').show();
            this.element.find('#imupUploadFileContainer').removeAttr('disabled');
            this.element.find('#imupUploadFile').focus();
        }
    },
    uploadFromUrl: function(url) {
        /* function for uploading image given specified URL directly without
         * showing imageuploader interface */
        this._switchToUrlTab()
        this.element.find('#imupUploadUrl').attr('value', url);

        this.element.find('#imupUploadForm').submit();

        if (!this.element.is(':visible')) {
            with (this) {
                /* display the spinner if it takes more than 700ms to
                 * upload the image, to indicate that something is going on! */
                setTimeout(function(){
                    _upload_showLoader();
                }, 700);
            }
            //this.delay(1000)._upload_showLoader();
        }
    },
    uploadFromFile: function(file) {
        /* function for uploading image given specified URL directly without
         * showing imageuploader interface */
        var self = this;

        this._switchToFileTab()

        var data = new FormData();
        data.append(this.options.uploadUrlField, '');
        data.append(this.options.uploadFileField, file);

        this.options._cancelled = false;
        this.options._uploading = true;

        $.ajax({
            url: this.options.uploadAction,
            data: data,
            cache: false,
            contentType: false,
            processData: false,
            type: 'POST',
            success: function(data) {
                data = JSON.parse(data);
                self.options._uploading = false;
                self.hide();
                self._prepareForNewRequest();

                var url = '';
                if (self.options.returnUrlJsonField in data) {
                    url = data[self.options.returnUrlJsonField];
                }
                if (url == '') {
                    $.getScript(jsFileLocation+'jquery.ui.imageuploader/appriseimup-1.5.min.js', function() {
                        srcurl = '';
                        if (self.options.returnUrlSource in data) srcurl = data[self.options.returnUrlSource];
                        if (srcurl != '') {
                            var alertstr = 'The selected image could not be loaded or was invalid:<br/><span style="font-size:small;">'+srcurl+'</span>';
                            appriseimup(alertstr);
                        } else {
                            var alertstr = 'The selected image could not be uploaded';
                            appriseimup(alertstr);
                        }
                    });
                    self.options._cancelled = false;
                    self.options._uploading = false;
                    self._switchToUrlTab();
                } else {
                    /* provide handle for callback */
                    self._trigger('urlreturned', 0, url);
                }
            }
        });

        this.element.find('#imupSubmit').attr('disabled','disabled');
        this.element.find('#imupUploadUrlContainer').hide();
        this.element.find('#imupUploadFileContainer').hide();
        this.element.find('#imupProcessingContainer').show();
        this.element.find('#imupTabbar').slideUp('fast');
    },
    _upload_showLoader: function() {
        if (this.options._uploading) {
            this.show();
        }
    },
    _prepareForNewRequest: function() {
        this.element.find('#imupUploadFile').attr('value', '');
        this.element.find('#imupUploadUrl').attr('value', '');

        this.element.find('#imupProcessingContainer').hide();
        this.element.find('#imupSubmit').removeAttr('disabled');
        if (this.element.find('#imupTabbarUrl').is('.imupTabbarSelected')) {
            this.element.find('#imupUploadUrlContainer').show();
        } else {
            this.element.find('#imupUploadFileContainer').show();
        }
        this.element.find('#imupTabbar').slideDown('fast');
    },
    options: {
        uploadFileField: 'file',
        uploadUrlField: 'url',
        uploadAction: 'uploadimage',
        returnUrlJsonField: 'impath',
        returnUrlSource: 'srcurl',
        errorJsonField: 'Error',
        _cancelled: false,
        _uploading: false
    }
};
$.widget("ui.imageuploader", imageuploader);
