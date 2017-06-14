/* CHECK STATUS OF BACKEND
 * -----------------------
 * This script is called from the templates/nobackend.html template to
 * establish when communication with the VISOR backend has been
 * re-established (at which point the script redirects back to the homepage)
 * 
 * The python function 'is_backend_reachable' is used to perform the check.
 * 
 * Dependencies:
 * - is_backend_reachable function provided by webserver
 */

var http = new XMLHttpRequest()
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

/* callback function for XMLHttpRequest object */
function getProgress() {
    /* continue only if request is finished and response is ready (state 4) */
    var done = 4, ok = 200;
    if ((http.readyState == done) && (http.status == ok)) {
	/* server response (return value from function)
	   is returned as a JSON string */
	response = parseInt(http.responseText);

	/* check on status (could be used to update progress checklist) */
	if (response == 0) {
	    setTimeout(function(){sendRequest()},5000);
	} else {
	    /* redirect to homepage, as backend was reachable */
	    location.replace( fullHomeLocation );
	}
    }
}

function sendRequest() {
    execstr = fullHomeLocation + 'is_backend_reachable';
    /* if using IE, AJAX request are annoyingly cached, so add a random
       string to the end of the request to make it unique and prevent
       this */
    if (navigator.appName == 'Microsoft Internet Explorer') {
	execstr = execstr + '&time=' + new Date().getTime();
    }
    http.open('get',execstr);
    http.onreadystatechange = getProgress;
    /* must pass null argument for backwards compatibility with old versions of
     * firefox */
    http.send(null);
}

sendRequest(); //initial request

