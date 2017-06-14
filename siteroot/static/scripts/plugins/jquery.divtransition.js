/* PAGE TRANSITION MODULE FOR AJAX SUBPAGES
 * ----------------------------------------------------------------------------
 * This JQuery plugin provides transitions between AJAX subpages in a subpage module.
 *
 * To use, simply call on the element of your choice e.g.
 *
 * >> $('link_container').find('a').divtransition('fadein');
 *
 * This will then use the href parameter of the selected link to generate an updated
 * click handler which transitions between subpages instead of linking to a new page,
 * and handles updating the browser history appropriately using the HTML5 history API.
 *
 * The first parameter gives the transition type (can be 'fadein', 'slideleft', 'slideright')
 * and the transitions are provided by JQuery UI.
 *
 * The second parameter is a dictionary of associated options, different for each transition.
 *
 * Dependencies:
 * - JQuery and JQuery UI (transitions module)
 * - The $activeDiv and $contentLoadDiv global variables to be defined and pointing
 *   to two div elements on the host page *
 *
 * (*) these two divs are used in turn to load the new page in the background, then
 *     show the page, hiding the currently active div which then becomes the target
 *     for the next background page load and so on.
 */

/* activeDiv and contentLoadDiv global variables must exist */

(function($) {
    var TransitionType = {
        none: 'none',
        fadein: 'fadein',
        slideleft: 'slideleft',
        slideright:'slideright'
    };

    $.fn.divtransition = function(transition, options) {
        switch(transition) {
        case TransitionType.none:
            var params = $.extend({
                'addToHistory': true,
                'translucentWhileLoading': true,
                'waitForLoadElem': null,
                'doneFunction': null
            }, options);
        case TransitionType.fadein:
            var params = $.extend({
                'addToHistory': true,
                'translucentWhileLoading': true,
                'waitForLoadElem': null,
                'doneFunction': null,
                'fadeInElem': $contentLoadDiv
            }, options);
            break;
        case TransitionType.slideleft: case TransitionType.slideright:
            var params = $.extend({
                'addToHistory': true,
                'translucentWhileLoading': false,
                'doneFunction': null,
                'waitForLoadElem': null
            }, options);
            break;
        default:
            throw 'transition type not recognised: ' + transition
        }


        /* assign click handler of elements */
        this.click(function() {
            var targeturl = $(this).attr('href');
            /* push history state */
            if (params['addToHistory']) {
                history.pushState({'targeturl': targeturl}, '', location.href);
            }
            /* set current content's opacity to 50% whilst loading new page */
            if (params['translucentWhileLoading']) {
                $activeDiv.css('opacity',0.5);
            }
            /* load new page into secondary hidden div */
            $contentLoadDiv.load(targeturl, function() {
                if (params['waitForLoadElem']) {
                    params['waitForLoadElem'].on('load', function() {
                        contentLoaded(transition, params);
                    });
                } else {
                    contentLoaded(transition, params);
                }
            });
            return false;
        });
    };

    function contentLoaded(transition, params) {
        /* when loaded, scroll to top of page and swap active/loading divs */
        window.scrollTo(0, 0);

        switch(transition) {
        case TransitionType.none:
            $activeDiv.hide();
            $contentLoadDiv.show();
            animationDoneCleanup(params);
        case TransitionType.fadein:
            $activeDiv.hide();
            $(params['fadeInElem']).hide();
            $contentLoadDiv.show();
            $(params['fadeInElem']).fadeIn('fast');

            animationDoneCleanup(params);
            break;
        case TransitionType.slideleft: case TransitionType.slideright:
            $activeDiv.css('position','absolute'); // required to stop incoming div from being positioned incorrectly
            if (transition == TransitionType.slideleft) {
                var activeDir = 'left';
                var loadDir = 'right';
            } else {
                var activeDir = 'right';
                var loadDir = 'left';
            }
            $activeDiv.hide( { effect: 'slide', direction: activeDir, duration: 'fast', queue: false } );
            $contentLoadDiv.show( { effect: 'slide', direction: loadDir, duration: 'fast', queue: false, complete: function() {
                $activeDiv.css('position','static'); // reset to static

                animationDoneCleanup(params);
            } });
            break;
        }

    }

    function animationDoneCleanup(params) {
        /* do cleaning up after animation end */
        $activeDiv.html('');
        if (params['translucentWhileLoading']) {
            $activeDiv.css('opacity',1.0);
        }

        var $newContentLoadDiv = $activeDiv;
        var $newActiveDiv = $contentLoadDiv;

        $activeDiv = null;
        $contentLoadDiv = null;

        $activeDiv = $newActiveDiv;
        $contentLoadDiv = $newContentLoadDiv;

        /* run done function if required */
        if (params['doneFunction']) {
            params['doneFunction']();
        }
    }
})(jQuery);

function navigateHistory(target) {
    window.scrollTo(0, 0);

    $activeDiv.hide();
    $contentLoadDiv.show();

    $contentLoadDiv.load(target);
    $activeDiv.html('');

    var $newContentLoadDiv = $activeDiv;
    var $newActiveDiv = $contentLoadDiv;

    $activeDiv = null;
    $contentLoadDiv = null;

    $activeDiv = $newActiveDiv;
    $contentLoadDiv = $newContentLoadDiv;
}
