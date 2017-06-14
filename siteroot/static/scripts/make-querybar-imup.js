/* SETUP INTEGRATED QUERYBAR/IMAGEUPLOADER WIDGET COMBO
 *
 * This script can be used to add an integrated Querybar/Imageuploader
 * widget combo on document load given the appropriate div elements
 * in the host page.
 * Dependencies:
 * - JQuery
 * - widgets/jquery.ui.querybar.js
 * - widgets/jquery.ui.imageuploader.js
 * PLUS their dependencies (JQuery UI etc.)
 */

$(function () {
    $('#qbControl').querybar();
    $('#imupControl').imageuploader();
    $('#qbControl').bind('querybarselectimage', function() {
        $('#qbControl').querybar('disable');
        $('#imupControl').imageuploader('toggle');
    });
    $('#qbControl').bind('querybardropurl', function(event, url) {
        $('#qbControl').querybar('disable');
        $('#imupControl').imageuploader('uploadFromUrl', url);
    });
    $('#qbControl').bind('querybardropfile', function(event, file) {
        $('#qbControl').querybar('disable');
        $('#imupControl').imageuploader('uploadFromFile', file);
    });
    $('#imupControl').bind('imageuploaderhidden', function() {
        $('#qbControl').querybar('enable',true);
    });
    $('#imupControl').bind('imageuploaderurlreturned', function(event, url) {
        $('#qbControl').querybar('setQueryStr', url, 'image');
    });
});
