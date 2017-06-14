/* DO RESULTS LIST (SUBPAGE) INITIAL SETUP
 *
 * Checks querybar widget with the id #qbControl for positive and
 * negative training images, then pre-activates the refine buttons
 * on the corresponding images (siblings of class '.result_refinebtn_url')
 *
 * Dependencies:
 * - results-add-refine-buttons.js
 * - jQuery
 */

function updateRefineBtnStates() {
    $('.result_refinebtn_url').each(function(idx) {
        $this = $(this);
        $posrefinebtn = $this.parent().find('.result_refinebtn_pos');
        $negrefinebtn = $this.parent().find('.result_refinebtn_neg');
        var url = $this.html();

        if ($('#qbControl').querybar('isPosRefineImage', url)) {
            $posrefinebtn.removeClass('result_refinebtn_unselected');
            $posrefinebtn.addClass('result_refinebtn_selected');
        } else if ($posrefinebtn.hasClass('result_refinebtn_selected')) {
            $posrefinebtn.removeClass('result_refinebtn_selected');
            $posrefinebtn.addClass('result_refinebtn_unselected');
        }
        if ($('#qbControl').querybar('isNegRefineImage', url)) {
            $negrefinebtn.removeClass('result_refinebtn_unselected');
            $negrefinebtn.addClass('result_refinebtn_selected');
        } else if ($negrefinebtn.hasClass('result_refinebtn_selected')) {
            $negrefinebtn.removeClass('result_refinebtn_selected');
            $negrefinebtn.addClass('result_refinebtn_unselected');
        }
    });
}

$(function() {
    updateRefineBtnStates();
    $('#qbControl').bind('querybarrefineimageschange', function() {
        updateRefineBtnStates();
    });
});
