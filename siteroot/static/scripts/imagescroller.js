/* HTML5 CANVAS BASED IMAGE SCROLLER FOR IMAGES LOADED FROM GOOGLE IMAGE SEARCH
 * ----------------------------------------------------------------------------
 * This script is called from the templates/search.html template to display
 * a dynamically updated 'scroller' of images, which displays images as they are
 * downloaded from a query to Google Images.
 *
 * Dependencies:
 * - query-progress.js - required to provide status struct containing array of
 *                       downloaded images
 * - easel.js ( >= v0.7.0 )- HTML5 canvas drawing library
 * Optional Dependencies:
 * - IE Canvas Library
 * - json2.js - provides JSON parsing in older browsers
 */

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
// html5 canvas
var imsc_stage;
var imsc_canvas;
var imsc_sub_stage;
var imsc_sub_canvas;
// context
var imsc_canvas_context;
// arrays for images
var imsc_pics = new Array();
var imsc_widths = new Array();
var num_images_added = 0;
// for animation
var imsc_maxleft = new Array();
var imsc_settledleft = new Array();
var clearedright = -1;
// for image path conversion
var siteroot;
// status text
var imsc_status;
// initial y position of images on stage (to stop them being shifted prematurely)
var initialy = -1000;
// for mouse scrolling (used to calculate scrolling)
var imscMouseDown = false;
var imscInCanvas = false;
var imscXStart = 0;
var imscYStart = 0;
var imscXEnd = 0;
var imscYEnd = 0;
var mousescroll = 0;
// for mouse scrolling (constants)
var decelSpeed = (49/50);
var springbackResistance = 0.02;
// for mouse scrolling (springback at ends)
var springback = false;
// for mouse scrolling (position variables)
var curXOffset = 0;
var minXOffset = 0;
// for waiting animation
var RADIUS = 28;
var END_PERCENT = 101; // give a it a bit of offset at the end
var CIRC = Math.PI * 2;
var QUART = Math.PI / 2;
var curPerc = 1;

/* check to see if current browser is supported by imsc applet. Requires:
 - canvas + textwidth support */
function is_compatible_browser() {
    var dc = document.createElement('canvas');
    if (!dc.getContext) return false;
    var c = dc.getContext('2d');
    return (typeof c.fillText == 'function');
}

function imsc_init() {
    if (is_compatible_browser()) {
        // get a reference to the canvas element
        imsc_canvas = document.getElementById("imsc_stage_canvas");
        imsc_canvas_context = imsc_canvas.getContext("2d");
        // pass canvas element to EaselJS stage wrapper
        imsc_stage = new createjs.Stage(imsc_canvas);
        // do the same for the second canvas
        imsc_sub_canvas = document.getElementById("imsc_stage_canvas_back");
        imsc_sub_stage = new createjs.Stage(imsc_sub_canvas);
        // add text status to sub-canvas
        imsc_status = new createjs.Text("", "bold 12px Trebuchet MS, Arial", "#AAA");
        imsc_status.textBaseline = "top"
        imsc_status.x = 5;
        imsc_status.y = 3;
        imsc_sub_stage.addChild(imsc_status);
        // add debug text to sub-canvas
        /*imsc_debug = new createjs.Text("", "bold 12px Trebuchet MS, Arial", "#F00");
        imsc_debug.textBaseline = "top"
        imsc_debug.x = 5;
        imsc_debug.y = 3;
        imsc_sub_stage.addChild(imsc_debug);*/
        // add scrolling text to sub-canvas
        imsc_scrolling_text = new createjs.Text("", "bold 12px Trebuchet MS, Arial", "#900000");
        imsc_scrolling_text.textBaseline = "top"
        imsc_scrolling_text.x = 0;
        imsc_scrolling_text.y = 3;
        imsc_sub_stage.addChild(imsc_scrolling_text);
        // add handler for mouse movement to allow scrolling
        imsc_canvas.onmousedown = imsc_canvasMouseDown;
        document.onmouseup = imsc_canvasMouseUp;
        imsc_canvas.onmousemove = imsc_canvasMouseMove;
        imsc_canvas.onmouseout = imsc_canvasMouseOut;
        imsc_canvas.onmouseover = imsc_canvasMouseOver;
        // add handler for selection, to disable selection and stop the cursor
        // turning into a text selection beam in chrome when dragging over canvas,
        // and also from missing 'onmouseup' due to selection (another bug
        // in webkit browsers)
        document.onselectstart = function() { return false; }

        createjs.Ticker.addEventListener("tick", tick);
        createjs.Ticker.setFPS(100);
    } else {
        /* reveal warning message about incompatible browser */
        document.getElementById("results_progress_imsc").style.display = 'none';
        document.getElementById("results_progress_incompatible_browser").style.display = 'block';
    }
}

function imsc_loadImage(engine, impath) {

    var siteimpath;

    if (impath.indexOf('/postrainimgs/') != -1) {
        var lastidx = impath.lastIndexOf('/');
        lastidx = impath.lastIndexOf('/', lastidx-1);
        var imfile = impath.substring(lastidx+1);
        imfile = escape(imfile.replace('%20', '%2520'));

        siteimpath = fullHomeLocation + 'postrainimgs/' + engine + '/' + imfile;
    } else if (impath.indexOf('/curatedtrainimgs/') != -1) {
        var lastidx = impath.lastIndexOf('/');
        lastidx = impath.lastIndexOf('/', lastidx-1);
        lastidx = impath.lastIndexOf('/', lastidx-1);
        var imfile = impath.substring(lastidx+1);
        imfile = escape(imfile);

        siteimpath = fullHomeLocation + 'curatedtrainimgs/' + engine + '/' + imfile;
    } else {
        throw 'Image path could not be interpreted: ' + impath;
    }

    // add new image
    newidx = imsc_pics.length;
    imsc_pics[newidx] = new Image();
    imsc_pics[newidx].src = siteimpath;
    imsc_pics[newidx].onload = function() { imsc_imageLoaded(newidx) };
    imsc_pics[newidx].onerror = function() { imsc_imageLoadFailed(newidx) };
}

function imsc_imageLoaded(idx) {

    num_images_added++;
    var scaleRatio = imsc_canvas.height / imsc_pics[idx].height;
    imsc_widths[idx] = imsc_pics[idx].width*scaleRatio;
    imsc_createBitmap(idx, scaleRatio);
}

function imsc_imageLoadFailed(idx) {

    console.log("image at idx " + idx + " could not be loaded - " + imsc_pics[idx].src);
    if (idx+1 != imsc_pics.length) {
        alert('Developer error: tried to load too many images at the same time (only one image at a time is supported)');
    }
    imsc_pics.splice(idx,1);
}

function imsc_createBitmap(idx, scaleRatio) {
    var thumb = new createjs.Bitmap(imsc_pics[idx]);

    thumb.x = imsc_canvas.width;
    thumb.y = initialy;
    thumb.scaleX = scaleRatio;
    thumb.scaleY = scaleRatio;

    // add image to stage
    imsc_stage.addChild(thumb);

    // update status arrays with new elements for the new image
    imsc_maxleft[idx] = 0;
    imsc_settledleft[idx] = false;
}

function imsc_canvasMouseDown(e) {
    if (!e) { var e = window.event; }
    imscXStart = e.pageX - imsc_canvas.offsetLeft;
    imscYStart = e.pageX - imsc_canvas.offsetTop;
    imscMouseDown = true;
    imscInCanvas = true;
}

function imsc_canvasMouseUp(e) {
    imscMouseDown = false;
}

function imsc_canvasMouseMove(e) {
    if (!e) { var e = window.event; }
    imscXEnd = e.pageX - imsc_canvas.offsetLeft;
    imscYEnd = e.pageY - imsc_canvas.offsetTop;
}

function imsc_canvasMouseOut(e) {
    imscInCanvas = false;
}

function imsc_canvasMouseOver(e) {
    imscInCanvas = true;
}

function waiting_animation(current) {

     if (num_images_added>0) return;
     
     context = imsc_canvas_context;
     location_x = imsc_canvas.width / 2;
     location_y = imsc_canvas.height / 2;
     context.clearRect(location_x - RADIUS - context.lineWidth, 
                  location_y - RADIUS - context.lineWidth, 
                  RADIUS * 2 + (context.lineWidth*2), 
                  RADIUS * 2 + (context.lineWidth*2));
     context.beginPath();
     context.arc( location_x, location_y, RADIUS, -(QUART), ((CIRC) * current) - QUART , false);
     context.stroke();
     context.lineWidth = 10;
     context.strokeStyle = '#ad2323';
     curPerc = curPerc + 0.01;
     if (curPerc <= END_PERCENT ) {
         requestAnimationFrame(function () {
             waiting_animation(curPerc / 100)
         });
     }
     else {   
        context.clearRect(0, 0, imsc_canvas.width, imsc_canvas.height);
        curPerc = 1;
     }
 }

function tick() {
    var maxspeed = 11;
    var minspeed = 4;
    var connectedspeed = 4;

    //////// Update status text on sub-canvas  ///////////////////

    if (num_images_added==0) {
        imsc_scrolling_text.text = "... searching for images ...";

        imsc_scrolling_text.x = imsc_scrolling_text.x + 1;
        if (imsc_scrolling_text.x > imsc_sub_canvas.width ) { 
            imsc_scrolling_text.x = -imsc_scrolling_text.text.length ; 
        }
    }
    else {
        imsc_status.text = num_images_added + " training images";
        imsc_scrolling_text.text = "";
    }
    
    // update debug text 
    //imsc_debug.text = "curXOffset: " + curXOffset.toFixed() + " max: " + 0 + " min: " + minXOffset.toFixed() + ' mousedown: ' + imscMouseDown + ' mousescroll: ' + mousescroll.toFixed(1) + ' incanvas: ' + imscInCanvas;
    
    // add negative training image count if required
    if (respStatus != null) {
        if (respStatus.negtrainimg_count > 0) {
            imsc_status.text = imsc_status.text + " (+ " + respStatus.negtrainimg_count + " negative training images)";
        }
    }
    // update width of label
    imsc_status.x = imsc_sub_canvas.width - imsc_status.getMeasuredWidth() - 5;
    
    // update stage
    imsc_sub_stage.update();
    
    /////// Update image scroller sub-canvas ///////////////////
        
    // check for new images
    if (respStatus != null) {
        if (respStatus.postrainimg_paths.length > imsc_pics.length) {
            // add a maximum of one image per tick
            // and only add a new image when the previous one has finished loading (or loading ended in error)
            if (imsc_stage.children.length == imsc_pics.length) {
                imsc_loadImage(respStatus.query.engine, respStatus.postrainimg_paths[imsc_pics.length]);
            }
        }
        if (respStatus.curatedtrainimgs_paths.length > imsc_pics.length) {
            // add a maximum of one image per tick
            // and only add a new image when the previous one has finished loading (or loading ended in error)
            if (imsc_stage.children.length == imsc_pics.length) {
                imsc_loadImage(respStatus.query.engine, respStatus.curatedtrainimgs_paths[imsc_pics.length]);
            }
        }
        if (num_images_added==0) {
            waiting_animation();
            return;
        }
    }
    else  {
        if (num_images_added==0) {
            waiting_animation();
            return;
        }
    }
    // limit the rate at which new images are added to the stage
    // EITHER process one more than images which are completely within the stage (cleared right)
    // OR at most the number of images which have been loaded into the stage
    var maxproc = 1;
    if (clearedright > -1) {
        maxproc = clearedright + 2;
    }
    if (maxproc > imsc_stage.children.length) {
        maxproc = imsc_stage.children.length;
    }

    // remove all x offsets for calculations for animation
    if (curXOffset != 0) {
        for (i=0; i < maxproc; i++) {
            if (imsc_stage.children[i].y != initialy) {
                imsc_stage.children[i].x = imsc_stage.children[i].x + curXOffset;
            }
        }
    }

    // update image positioning for animation
    for (i=0; i < maxproc; i++) {
        if (imsc_stage.children[i].y == initialy) {
            imsc_stage.children[i].y = 0;
        }
        // calculate the new position of the image ignoring all constraints
        if (imsc_stage.children[i].x > 0) {
            scrollwidthmid = imsc_canvas.width/2;
            curpos = imsc_stage.children[i].x - scrollwidthmid;
            scrollfrac = 1 - (Math.abs(curpos)/scrollwidthmid);
            scrollspeed = (maxspeed-minspeed)*scrollfrac + minspeed;
            newx = imsc_stage.children[i].x - scrollspeed;
        } else {
            // if image is to left of the stage it must be settled, and should
            // only move if pushed from right, so set its desired position to
            // its current position
            newx = imsc_stage.children[i].x;
        }
        // check whether the image area is full, in which case all images should
        // be scrolled leftwards to accommodate the new image (this only takes
        // effect if all images to left of current image are settled in their
        // final position, as determined by the settledleft array)
        if ((imsc_maxleft[i] > (imsc_canvas.width - imsc_widths[i])) &&
            (imsc_settledleft[i-1])) {
            // update newx to use fixed scrolling speed
            newx = imsc_stage.children[i].x - connectedspeed;
            // calculate the scroll distance and scroll previous images
            var scrolldist
            if (imsc_maxleft[i] > imsc_canvas.width) {
                // scroll at a constant rate if image is completely off the screen
                scrolldist = connectedspeed;
            } else {
                // else scroll in order to accommodate image moving onto the screen at a constant rate
                scrolldist = ((imsc_canvas.width - newx) - (imsc_canvas.width - imsc_maxleft[i]));
            }
            // only scroll images if they will be scrolled to the left
            if (scrolldist > 0) {
                for (ii=0; ii < i; ii++) {
                    imsc_stage.children[ii].x = imsc_stage.children[ii].x - scrolldist;
                    imsc_maxleft[ii] = imsc_maxleft[ii] - scrolldist;
                }
                imsc_maxleft[i] = imsc_maxleft[i] - scrolldist;
                // update min bounds of scrolling area
                minXOffset = minXOffset - scrolldist;
                if ((curXOffset < 0) || ((curXOffset == 0) && (imscMouseDown == true))) {
                    // only update curXOffset if in mouse scroll mode
                    // (i.e. curXOffset < 0  which would imply locking
                    // to the right of the scroller) or curXOffset is zero
                    // but the mouse is down to start a scrolling operation
                    // N.B. if 'springing' off the right, still update so that
                    // the canvas will remain locked to the right of the canvas
                    // as desired after the springback completes
                    curXOffset = curXOffset - scrolldist;
                }
            }
        }
        // now check left constraint and update image position accordingly
        if (newx > imsc_maxleft[i]) {
            imsc_stage.children[i].x = newx;
        } else {
            imsc_stage.children[i].x = imsc_maxleft[i];
            // if <= maxleft, and the previous image is in final position, this
            // image has also reached its final position, so store this
            if (i == 0) {
                imsc_settledleft[i] = true;
            } else {
                imsc_settledleft[i] = imsc_settledleft[i-1];
            }
        }
        if (((imsc_stage.children[i].x + imsc_widths[i]) <= imsc_canvas.width) &&
            (i > clearedright)) {
            clearedright = i;
        }
        imsc_maxleft[i+1] = imsc_stage.children[i].x + imsc_widths[i];
    }

    // calculate movement from scrolling...
    if (imscMouseDown == true) {
        if (imscInCanvas == true) {
            mousescroll = -(imscXEnd - imscXStart);
            imscXStart = imscXEnd;
        }
    } else {
        if (mousescroll != 0) {
            // if mouse is not down, decelerate normally
            mousescroll = decelSpeed*mousescroll;
            if (Math.abs(mousescroll) < 0.05) {
                mousescroll = 0;
            }
        }
    }

    // calculate springback if required
    if (springback == true) {
        var springaccel;
        var springsign;
        // springback acceleration is proportional to the distance out of the
        // allowed area
        if (curXOffset > 0) {
            springaccel = springbackResistance*curXOffset;
            springsign = 1;
        } else if (curXOffset < minXOffset) {
            springaccel = (springbackResistance*(minXOffset - curXOffset));
            springsign = -1;
        } else {
            springaccel = 0;
            springsign = 0;
        }
        // make acceleration squared
        springaccel = springaccel*springaccel;


        if ((imscMouseDown == true) && (springsign*mousescroll < 0)) {
            // if the mouse is down and scrolling INTO the allowed area,
            // just permit this normally i.e. don't update mousescroll
            // <EMPTY BODY>
        } else {
            // update scrolling disp change using
            // v = u + at
            mousescroll = mousescroll - springsign*springaccel;
            // if mouse is down, then don't allow springback until it is released
            if ((imscMouseDown == true) && (springsign*mousescroll < 0)) {
                mousescroll = 0;
            }
            // ensure springback doesn't occur beyond the limit of the allowed canvas
            if (imscMouseDown == false) {
                if (curXOffset > 0) {
                    if ((curXOffset + mousescroll) < 0) {
                        curXOffset = 0;
                        mousescroll = 0;
                    }
                } else if (curXOffset < minXOffset) {
                    if ((curXOffset + mousescroll) > minXOffset) {
                        curXOffset = minXOffset;
                        mousescroll = 0;
                    }
                }
            }
        }
    }

    // update x offset
    curXOffset = curXOffset + mousescroll;
    if ((curXOffset > 0) || (curXOffset < minXOffset)) {
        springback = true;
    } else {
        springback = false;
    }

    // reapply all x offsets (caused by mouse scrolling)
    if (curXOffset != 0) {
        for (i=0; i < maxproc; i++) {
            imsc_stage.children[i].x = imsc_stage.children[i].x - curXOffset;
        }
    }

    // update stage
    imsc_stage.update();

}
