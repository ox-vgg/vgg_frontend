/* QUERYBAR JQUERY UI WIDGET
 * ----------------------------------------------------------------------------
 * This JQuery UI widget provides a unified image search bar which allows
 * specification of a query either via text string or locally stored image file.
 * It is best used in conjunction with the jquery.ui.imageuploader widget to
 * provide URLs to locally stored image files.
 *
 * As with all JQuery UI widgets, it can be attached to any container div as follows:
 *
 * >>  $('#containerDivId').querybar();
 *
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Supported Query Modes
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Currently two main modes are supported:
 * - 'text' : where the user has specified a text string as a search term
 * - 'image' : where the user has specified a local image URLs
 *
 * Either can be enabled/disabled using the setImage/TextEnabled functions.
 *
 * In addition, a third mode 'refine' - used for refining a search by specifying
 * multiple local image URLs - is also available, but has no setRefineEnabled
 * function for reasons described in the next section
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * 'refine' Query Mode
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * This is a special mode which is only accessible by adding local image URLs
 * through calls to the following functions:
 * - addPosRefineImage(image_url)
 * - addNegRefineImage(image_url)
 *
 * The mode remains enabled until all added refine images are cleared, either
 * manually by the user or by calls to one of the following functions
 * - clearRefineImages() <- clears ALL added refine images
 * - clearPosRefineImage(image_url)
 * - clearNegRefineImage(image_url)
 *
 * A mode-specific drop down menu is provided to allow the user to manage added
 * local image URLs.
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Dataset selector widget
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * A combobox is also provided for dataset selection to the right of the query
 * input box.
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Initial setup
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * The initial configuration of the widget can be set in the container div
 * directly using options of the following form:
 *
 *    <div class="qbTextSearchEnabled">true</div>
 *    <div class="qbImageSearchEnabled">true</div>
 *    <div class="qbDset">Dataset Name 1</div>
 *    <div class="qbDset">Dataset Name 2</div>
 *    <div class="qbEngine">Engine Name 1</div>
 *    <div class="qbEngine">Engine Name 2</div>
 *    <div class="qbQueryDset">Selected Dataset Name</div>
 *    <div class="qbQueryEngine">Selected Engine Name</div>
 *    <div class="qbSrcQueryId">ID relating to source query</div>
 *    <div class="qbHideDatasetSelector">false</div>
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Interface
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * - getQueryMode() :
 *      RETURNS current query mode ('text', 'image' or 'refine')
 * - getQueryStr() :
 *      RETURNS current query text (meaning depends on mode)
 * - setQueryStr(query_str, query_type) :
 *      SET the query string/change mode (can specify 'text' or 'image')
 *
 * - setQueryField(query_field) / getQueryField() :
 *      GET/SET the form field used for storing the query text
 * - setDsetField(dset_field) / getDsetField() :
 *      GET/SET the form field used for storing the search dataset
 * - setEngineField(dset_field) / getEngineField() :
 *      GET/SET the form field used for storing the search engine
 * - setQueryTypeField(qtype_field) / getQueryTypeField() :
 *      GET/SET the form field used for storing the query type ('text', 'image', 'refine')
 * - setImagePreviewPrefix(prefix) / getImagePreviewPrefix() :
 *      GET/SET the prefix added to local URLs to provide a valid image URL for preview
 *
 * - setTextSearchEnabled(bool) / getTextSearchEnabled() :
 *      GET/SET the enabled status of the text search modality
 * - setImageSearchEnabled(bool) / getImageSearchEnabled() :
 *      GET/SET the enabled status of the image search modality
 * - enable() :
 *      enable the control as a whole
 * - disable() :
 *      disable the control as a whole
 *
 * - setSrcQueryIdField(src_query_id_field) / getSrcQueryIdField():
 *      GET/SET the form field used for storing the soruce query ID (if applicable)
 * - setSrcQueryId(src_query_id) / getSrcQueryId():
 *      GET/SET an ID relating to the source query (if non-empty, this is added as
 *        an additional field when submitting 'refine' queries)
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Output
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * The widget should be placed within a HTML form on the host page, and will
 * contribute the following fields when that form is submitted:
 *
 *   {queryField}={either text query string or local URL}
 *   {queryTypeField}={either 'text', 'image' or 'refine' depending on query mode}
 *   {dsetField}={text string relating to the currently selected dataset}
 *   {engineField}={text string relating to the currently selected engine}
 *
 * In the case that {queryTypeField}='text', {queryField} will be the text query string
 *
 * In the case that {queryTypeField}='image', {queryField} will be the local image URL
 *
 * In the case that {queryTypeField}='refine', {queryField} will be a string of
 * the form:
 *
 *  'url1,anno:1;url2,anno:1;url3,anno:1;url4,anno:-1;url5:anno-1;url6,anno:-1'
 *   \                                 / \                                   /
 *    -- positive refine images -------   -- negative refine images ---------
 *
 * IN ADDITION, when {queryTypeField}='refine', a further field will be added to the
 * submitted form:
 *
 *   {srcQueryIdField}={text string identifying the current query shown on the page}
 *
 * This field will ONLY be added if {srcQueryId} has been set
 *
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Provided Callbacks
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * In addition, the following callbacks can be bound to:
 *
 *   selectimage : the 'select image' button at the right side of the querybar was pressed
 *   dropurl : a URL was dropped on the control
 *   refineimageschange : the list of refine images changed
 *
 * The 'selectimage' callback can be bound to display an instance of the jquery.ui.imageuploader
 * widget to allow the user to specify an image from URL/user local file.
 *
 * Dependencies:
 * - JQuery and JQuery UI (widgets module)
 * - Associated stylesheet (jquery.ui.querybar.css) and files
 *   (contained in jquery.ui.querybar directory)
 */

var CONST_IMGTXT_PLACEHOLDER = 'search term/image';
var CONST_TXT_PLACEHOLDER = 'search term';
var CONST_IMG_PLACEHOLDER = 'search image';

var CONST_QT_TEXT = 'text';
var CONST_QT_IMAGE = 'image';
var CONST_QT_REFINE = 'dsetimage';

var querybar = {
    /* ----------------------------------------------------------------------------------
     INITIALISE WIDGET ****************************************************************
     ---------------------------------------------------------------------------------- */
    _create: function() {
        /* widget initialisation ------------------------------------------------------------ */
        var self = this;
        var opts = self.options;
        var el = self.element;

        var jsFileLocation = $('script[src*="jquery.ui.querybar.js"]').attr('src');  // the js file path
        jsFileLocation = jsFileLocation.replace('jquery.ui.querybar.js', '');   // the js folder path

        /* parse dataset names from container contents -------------------------------------- */
        var datasetstr = '';
        el.find('.qbDset').each(function(index, e) {
            var dset = $(this).text().split('|');
            datasetstr = datasetstr + '<option value="' + dset[0] + '" >' + dset[1] + '</option>';
        });
        el.find('.qbDset').hide();

        /* parse engine names from container contents -------------------------------------- */
        var enginestr = '';
        el.find('.qbEngine').each(function(index, e) {
            var eng = $(this).text().split('|');
            enginestr = enginestr + '<option value="' + eng[0] + '" >' + eng[1] + '</option>';
        });
        el.find('.qbEngine').hide();

        /* prepend the control structure ---------------------------------------------------- */
        el.prepend('<div id="qbRefine">\
                      <div id="qbFlash"></div>\
                      <div id="qbFlashError"></div>\
                      <span id="qbRefineText"><strong>Refine:</strong> 1 positive, 2 negative</span>\
                      <div id="qbRefineClose">x</div>\
                      <a id="qbRefineMore" href="#">more</a>\
                      <div id="qbRefineDropdown">\
                        <p id="qbRefinePosListHeader">More like this:</p>\
                        <div id="qbRefinePosList">\
                        </div>\
                        <p id="qbRefineNegListHeader">Less like this:</p>\
                        <div id="qbRefineNegList">\
                        </div>\
                      </div>\
                    </div>\
                    <div id="qbInput">\
                      <div id="qbInputTbl"><!-- necessary for bug in chrome -->\
                        <div id="qbPreviewImage"></div>\
                        <div id="qbPreviewText">\
                          <div id ="qbPreviewImageFilename">\
                            <!-- preview image filename goes here -->\
                          </div>\
                          <div id="qbPreviewImageFilenameClose">\
                            x\
                          </div>\
                        </div>\
                        <div id="qbQueryText">\
                          <input id="qbQueryType" type="hidden" name="'+opts.queryTypeField+'" value="'+opts.baseQueryType+'" />\
                          <input id="qbQueryInputImageUrl" name="'+opts.queryField+'" type="hidden" />\
                          <input id="qbQueryInputText" name="'+opts.queryField+'" type="text" />\
                          <input id="qbQueryInputRefine" name="'+opts.queryField+'" type="hidden" disabled="disabled" />\
                          <input id="qbSrcQueryId" name="'+opts.srcQueryIdField+'" type="hidden" disabled="disabled" />\
                        </div>\
                        <div id="qbSelImage">\
                         <img src="static/images/picture.png" title="Image uploading">\
                        </div>\
                        <div id="qbSelKey">\
                         <img src="static/images/list.png" title="Keyword selection">\
                        </div>\
                      </div>\
                    </div>\
                    <select id="qbSelDataset" name="'+opts.dsetField+'" style="display:none">\
                      <!-- datasets go here -->\
                      ' + datasetstr + '\
                    </select>\
                    <select id="qbSelEngine" name="'+opts.engineField+'" style="display:none">\
                      <!-- engines go here -->\
                      ' + enginestr + '\
                    </select>');

        /* parse mode enabled data from container contents ---------------------------------- */
        if (el.find('.qbTextSearchEnabled').length) {
            var e = el.find('.qbTextSearchEnabled');
            e.hide();
            if (e.html().toLowerCase() == 'false') {
                self.setTextSearchEnabled(false);
            } else {
                self.setTextSearchEnabled(true);
            }
        }
        if (el.find('.qbImageSearchEnabled').length) {
            var e = el.find('.qbImageSearchEnabled');
            e.hide();
            if (e.html().toLowerCase() == 'false') {
                self.setImageSearchEnabled(false);
            } else {
                self.setImageSearchEnabled(true);
            }
        }

        if (el.find('.qbHideDatasetSelector').length) {
            var e = el.find('.qbHideDatasetSelector');
            e.hide();
            if (e.html().toLowerCase() == 'true') {
            opts.hideDatasetSelector = true;
            } else {
            opts.hideDatasetSelector = false;
            }
        }

        /* update placeholder string given the available modes */
        this._updateControlState();

        /* parse initial values from container contents ------------------------------------- */
        /* this includes enabling/disabling appropriate controls based on current mode ------ */
        if (el.find('.qbTextSearchVal').length) {
            var e = el.find('.qbTextSearchVal');
            e.hide();
            self.setQueryStr(e.html(),CONST_QT_TEXT);
        }
        else if (el.find('.qbImageSearchVal').length) {
            var e = el.find('.qbImageSearchVal');
            e.hide();
            self.setQueryStr(e.html(),CONST_QT_IMAGE);
            if (e.html().indexOf('anno:') !== -1) {
                el.find('#qbQueryType').attr('value',CONST_QT_REFINE);
            }
        } else {
            /* DO THIS EVEN IF NO INITIAL VALUE SPECIFIED */
            this._setQueryMode();
        }

        if (!el.find('#selectKeywordControl').length) {
            /* if the keywordcontrol is not included in the page, then do not show the button*/
            el.find('#qbSelKey').hide();
        }
        if (!el.find('#imupControl').length) {
            /* if the image uploading control is not included in the page, then do not show the button*/
            el.find('#qbSelImage').hide();
        }

        if (el.find('.qbQueryDset').length) {
            var e = el.find('.qbQueryDset');
            e.hide();
            el.find('#qbSelDataset').find('option[value="'+e.text()+'"]').attr('selected', 'selected');
        }

        if (el.find('.qbQueryEngine').length) {
            var e = el.find('.qbQueryEngine');
            e.hide();
            el.find('#qbSelEngine').find('option[value="'+e.text()+'"]').attr('selected', 'selected');
        }

        if (el.find('.qbEnginesWithImageSearchSupport').length) {
            var e = el.find('.qbEnginesWithImageSearchSupport');
            e.hide();
            opts.enginesWithImageSearchSupport = e.text().split(" ");
        }

        if (el.find('.qbSrcQueryId').length) {
            var e = el.find('.qbSrcQueryId');
            e.hide();
            self.setSrcQueryId(e.text());
        }

        if (el.find('.qbImagePreviewPrefix').length) {
            var e = el.find('.qbImagePreviewPrefix');
            e.hide();
            self.setImagePreviewPrefix(e.text());
        }
        if (el.find('.qbDatasetImagePreviewPrefix').length) {
            var e = el.find('.qbDatasetImagePreviewPrefix');
            e.hide();
            self.setDatasetImagePreviewPrefix(e.text());
        }

        if (el.find('#qbSelDataset')) {
            self.onSelectedEngineChange();
        }

        /* selectbox-ify combo -------------------------------------------------------------- */

       /* // If using the combobox for selecting datasets, uncomment this
        $.getScript(jsFileLocation+'jquery.ui.querybar/jquery-selectbox-0.2.min.js', function() {
        $("#qbSelDataset").show();
        $("#qbSelDataset").selectbox();
        if (opts.hideDatasetSelector) {
            if( el.find('.sbHolder') ) {
                el.find('.sbHolder').hide();
            }
        }
        el.fadeIn();
        });*/

        $.getScript(jsFileLocation+'jquery.ui.querybar/jquery-selectbox-0.2.min.js', function() {
        $("#qbSelEngine").show();
        $("#qbSelEngine").selectbox();
        if (opts.hideDatasetSelector) {
            if( el.find('.sbHolder') ) {
                el.find('.sbHolder').hide();
            }
        }
        el.fadeIn();
        });

        /* ----------------------------------------------------------------------------------
         SET EVENT HANDLERS
         ---------------------------------------------------------------------------------- */
        /* ---
         On changing the selected engine in the combobox */
         if (el.find('#qbSelDataset')) {
           $('#qbSelEngine').change(function() {
                self.onSelectedEngineChange();
            });
        }
        /* ---
         On input into query textbox */
        el.find('#qbQueryInputText').change(function() {
            if (!el.find('#qbQueryInputText').attr('disabled')) {
                if (el.find('#qbQueryInputText').val() != opts.queryStr) {
                    opts.queryStr = el.find('#qbQueryInputText').val();
                }
            }
        });
        /* ---
         On clicking close button of image preview */
        el.find('#qbPreviewImageFilenameClose').click(function(e) {
            self.setQueryStr('',CONST_QT_TEXT);
            if (!(el.find('#qbQueryInputText').attr('readonly') == 'readonly')) {
                el.find('#qbQueryInputText').focus();
            }
        });
        /* ---
         On clicking the 'select image' button */
        el.find('#qbSelImage').click(function(e) {
            /* provide handle for callback */
            self._trigger('selectimage');
        });
        /* ---
         On clicking the 'select keyword' button */
        el.find('#qbSelKey').click(function(e) {
            /* provide handle for callback */
            self._trigger('selectkey');
        });
        /* ---
         On dragging an image over the querybar */
        el.find('#qbQueryInputText,#qbPreviewImage,#qbPreviewText').bind('dragover', function(e) {
            if (e.target.id == 'qbQueryInputText') {
                $(this).addClass('queryTextDragOver');
            } else {
                el.find('#qbPreviewImage').addClass('previewDragOver');
                el.find('#qbPreviewText').addClass('previewDragOver');
            }
            //e.dataTransfer.dropEffect = 'copy';
            return false;
        });
        /* ---
         On dropping an image into the querybar */
        $.event.props.push('dataTransfer');
        el.find('#qbQueryInputText,#qbPreviewImage,#qbPreviewText').bind('drop', function(e) {

            /* first remove the drag-over attributes */
            if (e.target.id == 'qbQueryInputText') {
                $(this).removeClass('queryTextDragOver');
            } else {
                el.find('#qbPreviewImage').removeClass('previewDragOver');
                el.find('#qbPreviewText').removeClass('previewDragOver');
            }

            /* determine whether there is any file object associated with the current
             drag operation - if so, assume we are dragging in a local file */
            if ((e.dataTransfer.files) && (e.dataTransfer.files.length == 1)) {
                self._trigger('dropfile', 0, e.dataTransfer.files[0]);
                return false;
            }

            /* in the case of being dragged into text field, attempt to set the
             text to something sensible to start */
            var setText = false;
            if (e.target.id == 'qbQueryInputText') {
                var orig_value = this.value;

                droptext =  e.dataTransfer.getData('url') || e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/x-moz-url') || e.dataTransfer.getData('text') || e.dataTransfer.getData('text/plain') || e.dataTransfer.getData('text/html');
                if ((droptext) && (!(el.find('#qbQueryInputText').attr('readonly') == 'readonly'))) {
                    this.value = droptext;
                    setText = true;
                }
            }

            /* now try extracting a url from an image from the web for processing */
            droptext = e.dataTransfer.getData('url') || e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/x-moz-url') || e.dataTransfer.getData('text') || e.dataTransfer.getData('text/plain') || e.dataTransfer.getData('text/html');
            dropurl = '';

            if (droptext) {
                url_start_idx = droptext.indexOf('http://');
                if (url_start_idx != -1) {
                    dropurl_tmp = droptext.substring(url_start_idx);
                    url_end_idx = dropurl_tmp.search(/["\s']/);
                    if (url_end_idx != -1) {
                        dropurl = dropurl_tmp(0,url_end_idx);
                    } else {
                        dropurl = dropurl_tmp;
                    }
                }
            }

            if (dropurl) {
                /* try to extract dataset image path */
                var dset_res_id = self._getDsetResIdFromURL(dropurl);
                if (dset_res_id) {
                    /* deal with dropping of dataset image */
                    self.addPosRefineImage(dset_res_id, true);
                    if (e.target.id == 'qbQueryInputText') {
                        /* reset text value, which was changed to url, so that
                         when refine value is cleared this original value is
                         displayed again instead of the dropped url */
                        this.value = orig_value;
                    }
                } else {
                    /* deal with dropping of any other url */
                    self._trigger('dropurl', 0, dropurl);
                }
            } else {
                if (!setText) {
                    originalBgColor = $(this).css('background-color');
                    $(this).stop().css('background-color', '#d86755').animate({backgroundColor: originalBgColor}, 'fast');
                }
            }
            return false;
        });
        /* ---
         On drag leave from the querybar */
        el.find('#qbPreviewImage,#qbPreviewText').bind('dragleave', function(e) {
            el.find('#qbPreviewImage').removeClass('previewDragOver');
            el.find('#qbPreviewText').removeClass('previewDragOver');
        });
        el.find('#qbQueryInputText').bind('dragleave', function(e) {
            $(this).removeClass('queryTextDragOver');
        });
        /* ---
         On clicking close button of refinebar */
        el.find('#qbRefineClose').click(function(e) {
            e.preventDefault();
            self.clearRefineImages();
        });
        /* ---
         On clicking more button of refinebar */
        el.find('#qbRefineMore').click(function(e) {
            e.preventDefault();
            el.find('#qbRefineDropdown').slideToggle('fast');
        });
        /* ---
         On dragging an image over the refinebar */
        el.find('#qbRefine').bind('dragover', function(e) {
            el.find('#qbRefine').addClass('qbRefineDragOver');
            return false;
        });
        /* ---
         On dropping an image into the refinebar */
        $.event.props.push('dataTransfer');
        el.find('#qbRefine').bind('drop', function(e) {
            addedRefineImage = false;

            el.find('#qbRefine').removeClass('qbRefineDragOver');
            droptext =  e.dataTransfer.getData('url') || e.dataTransfer.getData('text/uri-list');
            if (droptext) {
                var dset_res_id = self._getDsetResIdFromURL(droptext);
                if (dset_res_id) {
                    self.addPosRefineImage(dset_res_id, true);
                    addedRefineImage = true;
                }
            }

            if (!addedRefineImage) {
                el.find('#qbFlashError').stop().show().fadeOut();
            }

            return false;
        });
        /* ---
         On drag leave from the refinebar */
        el.find('#qbRefine').bind('dragleave', function(e) {
            el.find('#qbRefine').removeClass('qbRefineDragOver');
        });

    },
    /* ----------------------------------------------------------------------------------
     PRIVATE FUNCTIONS ****************************************************************
     ---------------------------------------------------------------------------------- */
    /* Function used to update placeholder text in query input box depending on mode
     (either 'text' or 'image'). Also sets the enabled state of the textbox to depending
     on whether text mode is enabled or not. */
    _updateControlState: function () {
        var opts = this.options;
        var el = this.element;

        $qbQueryInputText = el.find('#qbQueryInputText');

        if (opts.baseQueryType == CONST_QT_IMAGE) {
            /* if in image-mode (which implies an image query is specified) always just clear the placeholder text */
            $qbQueryInputText.attr('placeholder', '');
        } else {
            if ((opts.textSearchEnabled) && (opts.imageSearchEnabled)) {
                $qbQueryInputText.attr('placeholder', CONST_IMGTXT_PLACEHOLDER);
                $qbQueryInputText.removeAttr('readonly', 'readonly');
                $qbQueryInputText.off('focus');
                el.find('#qbSelImage').show();
            } else if (opts.textSearchEnabled) {
                $qbQueryInputText.attr('placeholder', CONST_TXT_PLACEHOLDER);
                $qbQueryInputText.removeAttr('readonly', 'readonly');
                $qbQueryInputText.off('focus');
                el.find('#qbSelImage').hide();
            } else if (opts.imageSearchEnabled) {
                $qbQueryInputText.attr('placeholder', CONST_IMG_PLACEHOLDER);
                $qbQueryInputText.attr('readonly', 'readonly');
                $qbQueryInputText.on('focus', function() { this.blur(); });
                el.find('#qbSelImage').show();
            } else {
                throw 'At least one input mode must be enabled';
            }
        }
    },
    /* Function used to switch between 'text' and 'image' query modes
     making all changes required to control state and output.

     N.B. This is independent from 'refine' mode which is enabled regardless as
     long as refine images have been added to the control */
    _setQueryMode: function(newMode) {
        var opts = this.options;
        var el = this.element;

        if ((newMode == CONST_QT_IMAGE) && (!opts.queryStr)) {
            throw "Can't set query mode to IMAGE whilst query string is blank";
        }

        if (newMode) {
            opts.baseQueryType = newMode;
        } else {
            /* fallback mode is text if no query type is specified and query is blank */
            if (!opts.queryStr) {
                opts.baseQueryType = CONST_QT_TEXT;
            }
        }

        switch(opts.baseQueryType) {
        case CONST_QT_IMAGE:
            el.find('#qbQueryType').attr('value',CONST_QT_IMAGE);
            /* show image-related controls */
            el.find('#qbPreviewImage').show();
            el.find('#qbPreviewText').show();
            /* clear text-related controls */
            el.find('#qbQueryInputText').attr('value','');
            /* disable text-related query field */
            el.find('#qbQueryInputText').attr('disabled','disabled');
            /* enable image-related query field */
            el.find('#qbQueryInputImageUrl').removeAttr('disabled');
            /* remove placeholder string */
            this._updateControlState();
            /* update contents */
            el.find('#qbQueryInputImageUrl').attr('value',opts.queryStr);
            el.find('#qbPreviewImageFilename').find('input').attr('value', opts.queryStr);
            previewName = opts.queryStr.replace(/^.*[\\\/]/, '');  // remove path
            previewName = previewName.split(",")[0]; // remove extra parameters
            el.find('#qbPreviewImageFilename').html(this._shortenString(previewName,20)); // shorten if necessary
            /* Get the currently selected dataset and make it part of the querystring.
               It will be only used by the code that uploads the image thumbnail to the querybar */
            selectedDataset = document.getElementById("qbSelDataset").value;
            opts.queryStr = opts.queryStr + ",dataset:" +  selectedDataset
            el.find('#qbPreviewImage').css('background-image', "url('"+opts.imagePreviewPrefix + opts.queryStr + "')");
            break;
        case CONST_QT_TEXT:
            el.find('#qbQueryType').attr('value',CONST_QT_TEXT);
            /* hide image-related controls */
            el.find('#qbPreviewImage').hide();
            el.find('#qbPreviewText').hide();
            /* clear image-related controls */
            el.find('#qbQueryInputImageUrl').attr('value','');
            /* disable image-related query field */
            el.find('#qbQueryInputImageUrl').attr('disabled','disabled');
            /* enable text-related query field if required */
            if (opts.barEnabled) {
                el.find('#qbQueryInputText').removeAttr('disabled');
            }
            /* restore placeholder (removed on switch to image mode) */
            this._updateControlState();
            /* update contents */
            try {
                el.find('#qbQueryInputText').attr('value',opts.queryStr);
                el.find('#qbQueryInputText')[0].value = opts.queryStr;
            }
            catch(err) {
                console.log("Warning: could not set the value of qbQueryInputText");
            }
            break;
        default:
            throw 'Unrecognised query type';
        }
    },
    _shortenString: function(str, n) {
        if (str.length > n) {
            var s = str.substring(0,n);
            lastidx = s.lastIndexOf(' ');
            if (lastidx != -1) {
                return s.substring(0,lastidx) + '&hellip;';
            } else {
                if (s[s.length-1] == '.') {
                    s = s.substring(0,s.length-1);
                }
                return s + '&hellip;';
            }
            str = words.join(' ') + '&hellip;';
            return str;
        } else {
            return str;
        }
    },
    _updateRefineModeActive: function() {
        var self = this;
        if (this.options.refineModeActive) {
            if ((!this.options.posRefineImages.length) && (!this.options.negRefineImages.length)) {
                this.options.refineModeActive = false;

                if (this.element.find("#qbRefineDropdown").is(":visible")) {
                    this.element.find('#qbRefineDropdown').slideUp('fast', function() {
                        self.element.find('#qbRefine').hide();
                        self.element.find('#qbInput').show();
                    });
                } else {
                    this.element.find('#qbRefine').hide();
                    this.element.find('#qbInput').show();
                }

                this.element.find('#qbQueryType').attr('value',this.options.baseQueryType);

                /* enable one of text or image query fields */
                this.element.find('#qbQueryInputRefine').attr('disabled','disabled');
                this.element.find('#qbSrcQueryId').attr('disabled','disabled');
                switch(this.options.baseQueryType) {
                case CONST_QT_IMAGE:
                    this.element.find('#qbQueryInputImageUrl').removeAttr('disabled');
                    break;
                case CONST_QT_TEXT:
                    this.element.find('#qbQueryInputText').removeAttr('disabled');
                    this.element.find('#qbQueryInputText').focus();
                    break;
                default:
                    throw 'Unrecognised query type';
                }
            }
        } else {
            if ((this.options.posRefineImages.length) || (this.options.negRefineImages.length)) {
                this.options.refineModeActive = true;

                this.element.find('#qbInput').hide();
                this.element.find('#qbRefine').show();

                this.element.find('#qbQueryType').attr('value',CONST_QT_REFINE);

                /* disable text and image-related query fields */
                this.element.find('#qbQueryInputRefine').removeAttr('disabled');
                this.element.find('#qbSrcQueryId').removeAttr('disabled');
                this.element.find('#qbQueryInputText').attr('disabled','disabled');
                this.element.find('#qbQueryInputImageUrl').attr('disabled','disabled');
            }
        }

        if (this.options.refineModeActive) {
            if (this.options.posRefineImages.length) {
                this.element.find("#qbRefinePosList").show();
                this.element.find("#qbRefinePosListHeader").show();
            } else {
                this.element.find("#qbRefinePosList").hide();
                this.element.find("#qbRefinePosListHeader").hide();
            }
            if (this.options.negRefineImages.length) {
                this.element.find("#qbRefineNegList").show();
                this.element.find("#qbRefineNegListHeader").show();
            } else {
                this.element.find("#qbRefineNegList").hide();
                this.element.find("#qbRefineNegListHeader").hide();
            }

            /* update label */
            var newLabelText = '<strong>Refine:</strong> ';
            if (this.options.posRefineImages.length) {
                newLabelText = newLabelText + this.options.posRefineImages.length + ' positive';
            }
            if (this.options.negRefineImages.length) {
                if (this.options.posRefineImages.length) newLabelText = newLabelText + ', ';
                newLabelText = newLabelText + this.options.negRefineImages.length + ' negative';
            }
            this.element.find('#qbRefineText').html(newLabelText);

            /* update output string */
            var output = '';
            if (this.options.posRefineImages.length) {
                for (var i = 0; i < this.options.posRefineImages.length; ++i) {
                    output += this.options.posRefineImages[i] + ',anno:1;';
                }
            }
            if (this.options.negRefineImages.length) {
                for (var i = 0; i < this.options.negRefineImages.length; ++i) {
                    output += this.options.negRefineImages[i] + ',anno:-1;';
                }
            }
            if (!output){
                throw 'No positive OR negative refine images provided! Error in jquery.ui.querybar.js';
            } else{
                output = output.slice(0,-1);
            }


            this.element.find('#qbQueryInputRefine').val(output);
        }
    },
    _getDsetResIdFromURL: function(url) {
        dsetresid_start = url.indexOf('dsetresid=');
        if (dsetresid_start > -1) {
            dsetresid_start = dsetresid_start + 'dsetresid='.length;
            //dsetresid_start = url.indexOf('/', dsetresid_start) + 1;
            if (dsetresid_start) {
                dsetresid_end = url.indexOf('&', dsetresid_start);
                var dsetresid;
                if (dsetresid_end > -1) {
                    dsetresid = url.substring(dsetresid_start, dsetresid_end);
                } else {
                    dsetresid = url.substring(dsetresid_start);
                }
                return dsetresid;
            }
        }
        return undefined;
    },
    /* ----------------------------------------------------------------------------------
     INTERFACE ************************************************************************
     ---------------------------------------------------------------------------------- */
    getQueryMode: function() {
        if (!this.options.refineModeActive) {
            return this.options.queryType;
        } else {
            return CONST_QT_REFINE;
        }
    },
    getQueryStr: function() { return this.options.queryStr; },
    setQueryStr: function(queryStr, queryType) {
        this.options.queryStr = queryStr;
        this._setQueryMode(queryType);
    },
    getSrcQueryId: function() { return this.options.srcQueryId; },
    setSrcQueryId: function(srcQueryId) {
        this.options.srcQueryId = srcQueryId;
        this.element.find('#qbSrcQueryId').val(this.options.srcQueryId);
    },
    /* ----------------------------------------------------------------------------------
     INTERFACE - refine mode functions ************************************************
     ---------------------------------------------------------------------------------- */
    isPosRefineImage: function(imurl) {
        return (this.options.posRefineImages.indexOf(imurl) != -1);
    },
    isNegRefineImage: function(imurl) {
        return (this.options.negRefineImages.indexOf(imurl) != -1);
    },
    togglePosRefineImage: function(imurl, flash) {
        /* add url if it is not in list, otherwise remove it */
        var urlidx = this.options.posRefineImages.indexOf(imurl);
        if (urlidx == -1) {
            this.addPosRefineImage(imurl, flash);
        } else {
            this.clearPosRefineImage(imurl, flash);
        }
    },
    toggleNegRefineImage: function(imurl, flash) {
        /* add url if it is not in list, otherwise remove it */
        var urlidx = this.options.negRefineImages.indexOf(imurl);
        if (urlidx == -1) {
            this.addNegRefineImage(imurl, flash);
        } else {
            this.clearNegRefineImage(imurl, flash);
        }
    },
    addPosRefineImage: function(imurl, flash) {
        self = this;
        /* add url if it is not in list, otherwise return with a negative error code */
        var retval = -1;
        var urlidx = this.options.posRefineImages.indexOf(imurl);
        if (urlidx == -1) {
            retval = 0;
            /* add imurl to storage */
            this.options.posRefineImages.push(imurl);
            /* drop extra parameters from the url */
            impath = imurl.split(',')[0]
            /* add element to dropdown list */
            var $newElem = $('<div class="listimg"><img src="' +
                             this.options.datasetImagePreviewPrefix + impath +
                             '"/><span class="closebtn"/></div>');
            $newElem.find('.closebtn').click(function(e) {
                self.clearPosRefineImage(imurl);
            });
            this.element.find('#qbRefinePosList').append($newElem);

            /* add new element to storage too at same index as url */
            this.options.posRefineElems.push($newElem);
        }

        this._updateRefineModeActive();

        if (retval == 0) {
            if (flash) {
                this.element.find('#qbFlash').stop().show().fadeOut();
            }

            self._trigger('refineimageschange');
        }
        return retval;
    },
    addNegRefineImage: function(imurl, flash) {
        /* add url if it is not in list, otherwise return with a negative error code */
        var retval = -1;
        var urlidx = this.options.negRefineImages.indexOf(imurl);
        if (urlidx == -1) {
            retval = 0;
            /* add imurl to storage */
            this.options.negRefineImages.push(imurl);
            /* drop extra parameters from the url */
            impath = imurl.split(',')[0]
            /* add element to dropdown list */
            var $newElem = $('<div class="listimg"><img src="' +
                             this.options.datasetImagePreviewPrefix + impath +
                             '"/><span class="closebtn"/></div>');
            $newElem.find('.closebtn').click(function(e) {
                self.clearNegRefineImage(imurl);
            });
            this.element.find('#qbRefineNegList').append($newElem);

            /* add associated list element to storage too at same index as url */
            this.options.negRefineElems.push($newElem);
        }

        this._updateRefineModeActive();
        if (retval == 0) {
            if (flash) {
                this.element.find('#qbFlash').stop().show().fadeOut();
            }

            self._trigger('refineimageschange');
        }
        return retval;
    },
    clearPosRefineImage: function(imurl, flash) {
        /* clear url if it is in list, otherwise return with a negative error code */
        var retval = -1;
        var urlidx = this.options.posRefineImages.indexOf(imurl);
        if (urlidx != -1) {
            retval = 0;
            /* remove imurl from storage */
            this.options.posRefineImages.splice(urlidx,1);
            /* remove associated list element from storage after deleting it */
            this.options.posRefineElems[urlidx].find('.closebtn').unbind();
            this.options.posRefineElems[urlidx].remove();
            this.options.posRefineElems.splice(urlidx,1);
        }

        this._updateRefineModeActive();
        if (retval == 0) {
            if (flash) {
                this.element.find('#qbFlash').stop().show().fadeOut();
            }

            self._trigger('refineimageschange');
        }
        return retval;
    },
    clearNegRefineImage: function(imurl, flash) {
        /* clear url if it is in list, otherwise return with a negative error code */
        var retval = -1;
        var urlidx = this.options.negRefineImages.indexOf(imurl);
        if (urlidx != -1) {
            retval = 0;
            /* remove imurl from storage */
            this.options.negRefineImages.splice(urlidx,1);
            /* remove associated list element from storage after deleting it */
            this.options.negRefineElems[urlidx].find('.closebtn').unbind();
            this.options.negRefineElems[urlidx].remove();
            this.options.negRefineElems.splice(urlidx,1);
        }

        this._updateRefineModeActive();
        if (retval == 0) {
            if (flash) {
                this.element.find('#qbFlash').stop().show().fadeOut();
            }

            self._trigger('refineimageschange');
        }
        return retval;
    },
    clearRefineImages: function() {
        this.options.posRefineImages.length = 0;
        this.options.negRefineImages.length = 0;

        for (var i = 0; i < this.options.posRefineElems.length; ++i) {
            this.options.posRefineElems[i].find('.closebtn').unbind();
            this.options.posRefineElems[i].remove();
        }
        for (var i = 0; i < this.options.negRefineElems.length; ++i) {
            this.options.negRefineElems[i].find('.closebtn').unbind();
            this.options.negRefineElems[i].remove();
        }
        this.options.posRefineElems.length = 0;
        this.options.negRefineElems.length = 0;

        this._updateRefineModeActive();

        self._trigger('refineimageschange');
    },
    /* ----------------------------------------------------------------------------------
     INTERFACE - set/get output fields ************************************************
     ---------------------------------------------------------------------------------- */
    getQueryField: function() { return this.options.queryField; },
    setQueryField: function(x) {
        this.options.queryField = x;
        this.element.find('#qbQueryText').find(input).attr('name', this.options.textQueryField);
    },
    getDsetField: function() { return this.options.dsetField; },
    setDsetField: function(x) {
        this.options.dsetField = x;
        this.element.find('#qbSelDataset').attr('name', this.options.dsetField);
    },
    getEngineField: function() { return this.options.engineField; },
    setEngineField: function(x) {
        this.options.engineField = x;
        this.element.find('#qbSelEngine').attr('name', this.options.engineField);
    },
    getQueryTypeField: function() { return this.options.queryTypeField; },
    setQueryTypeField: function(x) {
        this.options.queryTypeField = x;
        this.element.find('#qbQueryType').attr('name', this.options.queryTypeField);
    },
    getImagePreviewPrefix: function() { return this.options.imagePreviewPrefix; },
    setImagePreviewPrefix: function(x) {
        this.options.imagePreviewPrefix = x;
        if (this.options.baseQueryType == CONST_QT_IMAGE) {
            this.element.find('#qbPreviewImage').css('background-image', "url('"+this.options.imagePreviewPrefix + this.options.queryStr+"')");
        }
    },
    getDatasetImagePreviewPrefix: function() { return this.options.datasetImagePreviewPrefix; },
    setDatasetImagePreviewPrefix: function(x) { this.options.datasetImagePreviewPrefix = x; },
    getSrcQueryIdField: function() { return this.options.srcQueryIdField; },
    setSrcQueryIdField: function(x) {
        this.options.srcQueryIdField = x;
        this.element.find('#qbSrcQueryId').attr('name', this.options.srcQueryIdField);
    },
    /* ----------------------------------------------------------------------------------
     INTERFACE - enable/disable *******************************************************
     ---------------------------------------------------------------------------------- */
    getTextSearchEnabled: function() { return this.options.textSearchEnabled; },
    setTextSearchEnabled: function(x) {
        this.options.textSearchEnabled = x;
        if ((!x) && (this.options.baseQueryType == CONST_QT_TEXT) && (this.options.queryStr)) {
            this.setQueryStr('', CONST_QT_TEXT);
        }
        this._updateControlState();
    },
    getImageSearchEnabled: function() { return this.options.imageSearchEnabled; },
    setImageSearchEnabled: function(x) {
        this.options.imageSearchEnabled = x;
        if ((!x) && (this.options.baseQueryType == CONST_QT_IMAGE)) {
            this.setQueryStr('', CONST_QT_TEXT);
        }
        this._updateControlState();
    },
    getHideDatasetSelector: function() { return this.options.hideDatasetSelector; },
    setHideDatasetSelector: function(x) {
        this.options.hideDatasetSelector = x;
        if (x) {
            this.element.find('.sbHolder').show();
        } else {
            this.element.find('.sbHolder').hide();
        }
    },
    onSelectedEngineChange: function() {
        var selected = $('#qbSelEngine').find('option[selected="selected"]').val();
        if (selected == undefined) {
            selected =  $('#qbSelEngine').val();
        }
        if ($.inArray(selected, this.options.enginesWithImageSearchSupport) < 0) {
            this.setImageSearchEnabled(false);
            /* without image search support it makes no sense to allow keyword selection */
            this.element.find('#qbSelKey').hide();
        }
        else {
            this.setImageSearchEnabled(true);
            this.element.find('#qbSelKey').show();
        }
    },
    /* enable/disable control */
    disable: function() {
        this.element.find('#qbQueryInputText').attr('disabled','disabled');
        this.options.barEnabled = false;
    },
    enable: function(focusInput) {
        if (!focusInput) focusInput = false;

        this.options.barEnabled = true;
        this._setQueryMode();

        if (focusInput) {
            if (!(this.element.find('#qbQueryInputText').attr('readonly') == 'readonly')) {
                this.element.find('#qbQueryInputText').focus();
            }
        }
    },
    /* ----------------------------------------------------------------------------------
     WIDGET MEMBER VARIABLES **********************************************************
     ---------------------------------------------------------------------------------- */
    options: {
        queryField: 'q',
        queryStr: '',
        refineQueryStr: '',
        queryTypeField: 'qtype',
        baseQueryType: CONST_QT_TEXT, /* either 'text' or 'image' (never 'refine') */
        dsetField: 'dsetname',
        engineField: 'engine',
        textSearchEnabled: true,
        imageSearchEnabled: true,
        barEnabled: true,
        hideDatasetSelector: false,
        imagePreviewPrefix: '',
        datasetImagePreviewPrefix: '',
        refineModeActive: false,
        posRefineImages: [],
        negRefineImages: [],
        posRefineElems: [],
        negRefineElems: [],
        srcQueryIdField: 'prev_qsid',
        srcQueryId: '',
        enginesWithImageSearchSupport:[],
    }
};
$.widget("ui.querybar", querybar);
