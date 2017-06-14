/* SETUP AJAX SUBPAGE ENVIRONMENT AND HISTORY HANDLING
 *
 * Loads initial AJAX subpage environment (first page of results
 * using searchreslist template) and handles HTML5 history navigation
 * event 'popstate' so that subpages can be navigated using the back/
 * forward buttons when using compatible browsers. Should be placed on
 * the parent page of the subpage environment (searchres page).
 *
 * This script also defines the $activeDiv and $contentLoadDiv global
 * variables used to make the AJAX subpage environment a reality using
 * the plugins/jquery.divtransition.js module.
 *
 * Dependencies:
 * - plugins/jquery.divtransition.js (and its dependencies including JQuery UI)
 * - jQuery
 */

var popped = ('state' in window.history), initialURL = location.href;
var fullHomeLocation = location.protocol + '//' + window.location.hostname;
if (location.port.length>0) {
    fullHomeLocation = fullHomeLocation + ':' + location.port + '/';
}
else {
    fullHomeLocation = fullHomeLocation + '/';
}
var pathArray = location.href.split( '/' );
if (pathArray.length>=4) {
    /* If pathArray hast at least 4 items, the third one must correspond to the site prefix, so add it to the request.
     * Otherwise, there is either no site prefix, or something else is wrong. */
    fullHomeLocation = fullHomeLocation + pathArray[3] + '/';
}
var $activeDiv = $('#results_content_block_primary');
var $contentLoadDiv = $('#results_content_block_secondary');

$(function() {
    
    /* load in initial result page */
    var targeturl = fullHomeLocation + 'searchreslist';
    targeturl = targeturl + '?qsid='+escape($('#rpQuerySesId').html())+
        '&page='+$('#rpPage').html()+
        '&processingtime='+$('#rpProcessingtime').html()+
        '&trainingtime='+$('#rpTrainingtime').html()+
        '&rankingtime='+$('#rpRankingtime').html();

    $activeDiv.load(targeturl);
    history.replaceState({'targeturl': targeturl}, '', location.href);

    $(window).bind('popstate', function(evt) {
        // discard initial popstate some browsers fire on pageload
        var initialPop = !popped && location.href == initialURL;
        popped = true;
        if (initialPop) {
            return;
        }

        var state = evt.originalEvent.state;

        if (state) {
            navigateHistory(state.targeturl);
        }
    });
});
