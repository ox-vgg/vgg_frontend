$(function() {

    $('#selection_save').bind('click', function() {
        var list = '';
        var qsid = '';
        var page = '';
        $('.roi_box').each(function(i, obj) {
            if ($(this).attr('anno') == 1 ) {
                list = list + $(this).attr('id') + ';';
                qsid = $(this).attr('qsid');
                page = $(this).attr('page');
            }
        });
        if (list=='') {
            alert('No image has been selected for saving');
        }
        else {
            savePageAsText(list, qsid, page);
        }
    });

    $('#set_all_images_yellow').bind('click', function() {
        $('.roi_box').each(function(i, obj) {
            div_ele = $(this);
            div_ele.attr('anno', '0');
            div_ele.removeClass('roi_box_positive');
            div_ele.addClass('roi_box_skip');
        });
    });

    $('#set_all_images_green').bind('click', function() {
        $('.roi_box').each(function(i, obj) {
            div_ele = $(this);
            div_ele.attr('anno', '1');
            div_ele.removeClass('roi_box_skip');
            div_ele.addClass('roi_box_positive');
        });
    });

});

function savePageAsText(list, qsid, page) {
    fullHomeLocation = location.protocol + '//' + window.location.hostname;
    if (location.port.length>0) {
        fullHomeLocation = fullHomeLocation + ':' + location.port + '/';
    }
    else {
        fullHomeLocation = fullHomeLocation + '/';
    }
    pathArray = location.href.split( '/' );
    if (pathArray.length>=4) {
        /* If pathArray hast at least 4 items, the third one must correspond to the site prefix, so add it to the request.
        * Otherwise, there is either no site prefix, or something else is wrong. */
        fullHomeLocation = fullHomeLocation + pathArray[3] + '/';
    }
    execstr = fullHomeLocation + 'savelistastext?qsid=' + qsid +
        '&list=' + encodeURIComponent(list) +
        '&page=' + page;
    window.open(execstr, '_blank');
}
