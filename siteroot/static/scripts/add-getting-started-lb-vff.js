/* SETUP GETTING STARTED LIGHTBOX
 *
 * This script sets up the 'getting started' lightbox on the homepage
 * Dependencies:
 * - JQuery
 * - JQuery FancyBox (lib/fancybox/jquery.fancybox.pack.js)
 */

var fullPrototypeLocation = 'http://zeus.robots.ox.ac.uk/bbc_search/'
var FinalPageHTML = '<div style="padding-left: 40px; padding-right:40px; padding-bottom: 40px;">\
    <h1>What is next ?...</h1>\
    <p>This system is an early beta which can be enhanced to perform more advanced queries. We have our own advanced protoype, which you can test with some sample queries for each different search engine:</p>\
    <ul>\
    <li><a href="' + fullPrototypeLocation + 'searchproc_qstr?engine=faces&qtype=text&q=David+Cameron&dsetname=BBCn" target="_blank">People: David Cameron</a></li>\
    <li><a href="' + fullPrototypeLocation + 'searchproc_qstr?engine=faces&qtype=text&q=Boris+Johnson&dsetname=BBCn" target="_blank">People: Boris Johnson</a></li>\
    <li><a href="' + fullPrototypeLocation + 'searchproc_qstr?engine=faces&qtype=text&q=Queen+Elizabeth&dsetname=BBCn" target="_blank">People: Queen Elizabeth</a></li>\
    </ul>\
    <p>Bugs in this system should be expected, but if you have any major issues \
    please contact <a href="mailto:ecoto-removemeifyouarehuman@robots.ox.ac.uk">Ernesto @ VGG Oxford</a>.</p>\
    <a id="close_tour" href="#">Close tour</a>\
    </div>'

function openTour() {
    $.fancybox.open([{'href': 'static/images/tour/vff/tour1.png',
                      'title': 'Getting Started'},
                     {'href': 'static/images/tour/vff/tour2.png',
                      'title': 'Starting a Search'},
                     {'href': 'static/images/tour/vff/tour3.png',
                      'title': 'Executing a Search'},
                     {'href': 'static/images/tour/vff/tour4.png',
                      'title': 'Viewing and Refining Results'},
                     {'href': 'static/images/tour/vff/tour5.png',
                      'title': 'Searching by Image'},
                     {'href': 'static/images/tour/vff/tour6.png',
                      'title': 'Searching by Keyword'},
                     FinalPageHTML],
                    {autoSize: true,
                     arrows: false,
                     closeBtn: false,
                     closeClick: false,
                     nextClick: true,
                     loop: false,
                     nextEffect: 'none',
                     prevEffect: 'none',
                     maxWidth: 850,
                     helpers: {
                         title: {
                             type: 'inside'
                         },
                         buttons: {
                             position: 'bottom'
                         }
                     }});
}

function closeTour() {
    $.fancybox.close();
}

$(function () {

    $('#getting_started').click(function(e){
        openTour();
        e.preventDefault();
    });

    $(document).on("click", "#close_tour", function(e){
        closeTour();
        e.preventDefault();
    });

});
