/* AUTO-REFLOW RESULTS GRID SCRIPT
 *
 * Script for automatically reflowing the results grid on the
 * searchreslist page such that each row always fills the current
 * available width on the page.
 *
 * Dependencies:
 * - jQuery
 */
function resizeResultBoxes() {
    var imsize = $('.result_inner_wrapper').find('img').css('max-width');
    if (imsize == undefined) {
        return;
    }
    imsize = parseInt(imsize.replace('px','').replace(/^\s+|\s+$/g,''));

    var padleft = undefined;
    var padright = undefined;
    if ($('.grid_list>div').css('padding-left') != undefined) {
        padleft = parseInt($('.grid_list>div').css('padding-left').replace('px','').replace(/^\s+|\s+$/g,''));
        padright = parseInt($('.grid_list>div').css('padding-right').replace('px','').replace(/^\s+|\s+$/g,''));
        imsize = imsize + padleft + padright;
    }

    var containersize = $('.grid_list').width();
    if (containersize != "0" && containersize != null ) {
        lastNonZeroContainerSize = containersize;
    }
    else {
        if (lastNonZeroContainerSize != undefined) {
            containersize = lastNonZeroContainerSize;
        }
    }
    var numims = Math.floor(containersize/imsize);
    var imwidth = Math.floor(containersize/numims)-1;
    if (padleft!= undefined && padright!= undefined) {
        // After upgrade to jquery > 1.8, compensate
        // for the padding of the result boxes
        imwidth = imwidth - (padleft + padright);
    }
    $('.grid_list>div').width(imwidth);
};

$(function(){
    var lastNonZeroContainerSize = undefined;
    resizeResultBoxes();
    $(window).resize(function(){
        resizeResultBoxes();
    });
});
