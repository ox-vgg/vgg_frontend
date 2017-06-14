
$(function() {
    var init_scroll = 30;
    var scroll_stop = 57;
    var logo_shift = -12;
    var orig_height = $('#page_header').outerHeight();
    $(window).scroll(function() {
        var $elem = $('#page_header');
        var $logo = $('#header_logo');
        var $elem_fill = $('#page_header_fill');
        var scroll_pos = $(window).scrollTop();

        if (scroll_pos > init_scroll) {
            $elem.css({'position':'fixed','top':-init_scroll+'px'});
            $elem_fill.show();
            if (scroll_pos < scroll_stop) {
                //console.log('scroll_pos: ' + scroll_pos + ' orig_height: ' + orig_height + ' new_height: ' + (orig_height - (scroll_pos - init_scroll)));
                $elem.height(orig_height - (scroll_pos - init_scroll));
            } else {
                var min_height = orig_height - (scroll_stop - init_scroll);
                //console.log('scroll_pos: ' + scroll_pos + ' min_height: ' + min_height);
                if ($elem.outerHeight() != min_height) {
                    $elem.height(min_height);
                }
            }
            $logo.css({'top':logo_shift+'px'});
        } else {
            $elem.css({'position':'static','top':'0px'});
            $elem_fill.hide();
            if ($elem.outerHeight() != orig_height) {
                $elem.height(orig_height);
            }
            var offset_ratio = 1.0 - (init_scroll-scroll_pos)/init_scroll;
            if (offset_ratio < 0.0) offset_ratio = 0.0;
            //console.log('scroll_pos: ' + scroll_pos + ' init_scroll: ' + init_scroll + ' offset_ratio: ' + offset_ratio);
            $logo.css({'top':logo_shift*offset_ratio+'px'});
        }
    });
});
