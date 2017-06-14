/* ADD REFINE BUTTONS
 *
 * Add refine buttons to images, and sets up click handlers to add to
 * a query bar widget with the id #qbControl. Uses animation effect to
 * show images being added to the querybar.
 *
 * Dependencies:
 * - lib/jquery.path.js
 * - jQuery
 */

function doRefineAnimation($img, doneFunc) {
    $ghost_img = $img.clone().appendTo('#content');

    var x_start = $img.offset().left;
    var y_start = $img.offset().top;
    var y_end = $(window).scrollTop() + 40;
    var x_end = 450;
    var imwidth = $img.width();
    var imheight = $img.height();
    var targetheight = 30;
    var targetwidth = targetheight/imheight*imwidth;

    var y_diff = y_start-y_end;
    var x_diff = x_start-x_end;
    var hyp = Math.sqrt(x_diff*x_diff + y_diff*y_diff);

    var theta = Math.acos(y_diff/hyp)/Math.PI*180;
    var is_right;
    if (x_end < x_start) {
        is_right = 1;
    } else {
        is_right = -1;
    }

    var start_rel_ang = is_right*theta;
    var end_rel_ang = is_right*theta;

    var bezier_params = {
        start: {
            x: x_start,
            y: y_start,
            angle: start_rel_ang,
            length: 0.2
        },
        end: {
            x: x_end,
            y: y_end,
            angle: end_rel_ang,
            length: 0.2
        }
    }
    $ghost_img.css({'position':'absolute','opacity':'1.0',
                    'left':x_start,'top':y_start,
                    'width':imwidth,'height':imheight,'z-index':5500});
    $ghost_img.animate({'opacity': 0.0, 'path': new $.path.bezier(bezier_params),
                        'width': targetwidth, 'height': targetheight},
                       200, function(){
                           $ghost_img.remove();
                           doneFunc();
                       });
}

function doDeleteAnimation($img) {
    $ghost_img = $img.clone().appendTo('#content');

    var x_start = 350;
    var y_start = $(window).scrollTop() + 40;
    var y_end = y_start + 100;
    var x_end = x_start;
    var imwidth = $img.width();
    var imheight = $img.height();

    $ghost_img.css({'position':'absolute','opacity':'0.5',
                    'left':x_start,'top':y_start,
                    'width':imwidth,'height':imheight,'z-index':5500});
    $ghost_img.animate({'opacity': 0.0, 'left': x_end, 'top': y_end},
                       200, function(){
                           $ghost_img.remove();
                       });
}

$(function () {
    $('.result_refinebtn_pos').click(function(e) {
        $this = $(e.target);
        e.preventDefault();
        // find url of image from sibling element
        var url = $this.parent().find('.result_refinebtn_url').html();
        // find image element itself
        var $img = $this.parent().parent().find('.result_image_link>img');
        // check if refine button should add or remove url (based on current associated class)
        if ($this.hasClass('result_refinebtn_unselected')) {
            // if url should be added...
            $this.removeClass('result_refinebtn_unselected');
            $this.addClass('result_refinebtn_selected');
            // begin animating 'flash' of image
            originalBgColor = $img.css('background-color');
            $img.stop().css({'opacity': '0.5',
                             'background-color': '#9cb0d8'}).animate({opacity: 1.0,
                                                                      backgroundColor: originalBgColor});
            // begin animating slide animation up to refine bar
            // and when done add image to querybar
            doRefineAnimation($img, function(){$('#qbControl').querybar('addPosRefineImage',url,true);});
        } else {
            // if url should be removed...
            $this.removeClass('result_refinebtn_selected');
            $this.addClass('result_refinebtn_unselected');
            // remove image from querybar
            $('#qbControl').querybar('clearPosRefineImage',url,false);
            // begin animating delete animation
            doDeleteAnimation($img);
        }
    });
    $('.result_refinebtn_neg').click(function(e) {
        $this = $(e.target);
        e.preventDefault();
        // find url of image from sibling element
        var url = $this.parent().find('.result_refinebtn_url').html();
        // find image element itself
        var $img = $this.parent().parent().find('.result_image_link>img');
        // check if refine button should add or remove url (based on current associated class)
        if ($this.hasClass('result_refinebtn_unselected')) {
            // if url should be added...
            $this.removeClass('result_refinebtn_unselected');
            $this.addClass('result_refinebtn_selected');
            // begin animating 'flash' of image
            originalBgColor = $img.css('background-color');
            $img.stop().css({'opacity': '0.5',
                             'background-color': '#9cb0d8'}).animate({opacity: 1.0,
                                                                      backgroundColor: originalBgColor});
            // begin animating slide animation up to refine bar
            // and when done add image to querybar
            doRefineAnimation($img, function(){$('#qbControl').querybar('addNegRefineImage',url,true);});
        } else {
            // if url should be removed...
            $this.removeClass('result_refinebtn_selected');
            $this.addClass('result_refinebtn_unselected');
            // remove image from querybar
            $('#qbControl').querybar('clearNegRefineImage',url,false);
            // begin animating delete animation
            doDeleteAnimation($img);
        }
    });
});
