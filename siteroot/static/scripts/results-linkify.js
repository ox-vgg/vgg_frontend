/* UTILITY SCRIPT FOR CONVERTING REGULAR LINKS TO AJAX SUBPAGE LINKS
 *
 * This script should be included on every subpage of an AJAX subpage
 * environment and updated such that all regular page links on that page
 * are updated to point to navigation actions to other subpages.
 *
 * How to use:
 *   1. Put location of subpage in href attribute of link in original page
 *   2. Use JQuery selector to select this link, and apply a divtrasition to it
 *      using the divtransition module and the transition type of your choice
 *
 * Dependencies:
 * - plugins/jquery.divtransition.js (and its dependencies including JQuery UI)
 * - jQuery
 */

$(function() {
    // linkify links on results display page
    $('.result_image_link').divtransition('slideleft');
    $('.more_results_btn').divtransition('slideleft');
    $('#results_prevpane,#results_pagespane,#results_nextpane,#results_prevpane_top,#results_nextpane_top').find('a').divtransition('fadein', {doneFunction: resizeResultBoxes, fadeInElem: '#results_list'});
    $('.results_nav_centre_link').divtransition('slideleft');
    // linkify links on details/trainingimages page
    $('.back_to_results').divtransition('slideright', {doneFunction: resizeResultBoxes});
});
