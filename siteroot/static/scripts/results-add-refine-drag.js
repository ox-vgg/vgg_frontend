

$(function () {
    $('.result_image_link').bind('mousedown', function(e) {
        e.stopPropagation();
    });
    $('.result_image_link').bind('dragstart', function(e) {
        $('#qbInput').addClass('is_drop_target_border');
        $('#qbRefine').addClass('is_drop_target_border');
        e.stopPropagation();
    });
    $('.result_image_link').bind('dragend', function(e) {
        $('#qbInput').removeClass('is_drop_target_border');
        $('#qbRefine').removeClass('is_drop_target_border');
        //updateRefineBtnStates();
    });
});
