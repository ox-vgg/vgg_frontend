$(function(){

    $("#imageroi_query_box_submit").click(function() {
        var dset = $('#imageroi_dsetname').val();
        var imagename = $('#imageroi_imagename').val();
        var dsetresid = $('#imageroi_dsetresid').val();
        var engine = $('#imageroi_engine').val();

        try {
            roistr = ',roi:' + selXMin+'_'+selYMin + '_' + selXMin+'_'+selYMax + '_' + selXMax+'_'+selYMax + '_' + selXMax+'_'+selYMin + '_' + selXMin+'_'+selYMin;
            // Check for a valid ROI first ...
            if ( !(selXMax == imWidth && selYMax==imHeight && selXMin ==0 && selYMin==0) && // if it's NOT the full image
                  !(selXMax == 0 && selYMax==0 && selXMin ==0 && selYMin==0)    // if it's NOT an empty image
                ) {
                // ... proceed with ROI based search
                next_location = 'searchproc_qstr?q='+imagename+roistr+'&qtype=dsetimage&dsetname='+dset;
            }
            else {
                // ... or go for the same "similar" search we can do in the main result list
                next_location = 'searchproc_qstr?q='+dsetresid+'&qtype=dsetimage&dsetname='+dset;
            }
        }
        catch(e) {
            if(e.name == "ReferenceError") {
                // We get ReferenceError when selXMin, selYMin, selXMax, selYMax are not declared, because the ROI
                // selection is inactive. In such a case, run the same "similar" search we can do in the main
                // result list
                next_location = 'searchproc_qstr?q='+dsetresid+'&qtype=dsetimage&dsetname='+dset;
            }
        }
        next_location = next_location +'&engine=' + engine;
        document.location.href = next_location
    });

});
