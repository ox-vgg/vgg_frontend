$(function() {
    $('.result_image_link').bind('click', function() {

    div_ele = $(this).parent()

    anno = div_ele.attr('anno')

    if (anno == '+1' || anno == '1') {
        div_ele.attr('anno', '-1')
            div_ele.removeClass('roi_box_positive');
            div_ele.addClass('roi_box_negative');
    } else if (anno == '-1') {
            div_ele.attr('anno', '0');
            div_ele.removeClass('roi_box_negative');
            div_ele.addClass('roi_box_skip');
    } else {
            div_ele.attr('anno', '+1')
            div_ele.removeClass('roi_box_skip');
            div_ele.addClass('roi_box_positive');
    }
    });

    $('#selection_search').bind('click', function() {
        var query = '';
        var dsetname = '';
        var qtype = '';
        $('.roi_box').each(function(i, obj) {
            query = query + $(this).attr('id') + ',anno:' + $(this).attr('anno') + ';';
            dsetname = $(this).attr('dsetname');
            qtype = $(this).attr('qtype');
            engine = $(this).attr('engine');
        });
        query = query.substr(0,query.length-1);
        sendRequest(engine, query,dsetname,qtype);
    });


});


function sendRequest(engine, query, dsetname, prev_qtype) {

    if (prev_qtype == 'text' || prev_qtype == 'refine') {
        qtype = 'refine';
    } else if (prev_qtype == 'dsetimage') {
        qtype = 'dsetimage';
    } else if (prev_qtype == 'image') {
        qtype = 'image';
    } else {
        alert('qtype not supported' + qtype);
        return;
    }
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

    execstr = fullHomeLocation + 'searchproc_qstr?q=' + encodeURIComponent(query) +
        '&engine=' + engine +
        '&qtype=' + qtype +
        '&dsetname=' + dsetname;
    var prev_qsid = $('#rpQuerySesId').html();
    if (prev_qsid) {
        execstr += '&prev_qsid=' + prev_qsid;
    }
    location.replace(execstr);
}
