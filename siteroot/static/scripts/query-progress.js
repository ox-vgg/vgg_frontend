/* UPDATE PROGRESS CHECKLIST ON RESULTS PAGE
 * -----------------------------------------
 * This script is called from the templates/searchproc.html template to display
 * a dynamically updated checklist of tasks conducted when performing a query
 * which are 'ticked off' as completed. It uses the javascript XMLHttpRequest
 * object to update this list as each step concludes.
 *
 * The python function 'execquery' is used to perform the actual query, and
 * specifies the states which are tested for below.
 *
 * Dependencies:
 * - execquery function provided by webserver
 * - extractparams.js
 * Optional Dependencies:
 * - json2.js - provides JSON parsing in older browsers
 */

var http = new XMLHttpRequest();
var states = {
    processing: 0,
    training: 51,
    ranking: 52,
    results_ready: 100,
    fatal_error_or_socket_timeout: 800,
    invalid_qid: 850,
    result_read_error: 870,
    inactive: 890
};
// global variable to store status struct returned from execquery
var respStatus;
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

function getKeyByValue(obj_inst, value) {
    for (var prop in this) {
        if (this.hasOwnProperty(prop)) {
            if (this[prop] == value) {
                return prop;
            }
        }
    }
}

/* callback function for XMLHttpRequest object */
function getProgress() {
    var qsid = document.getElementById('qpQsid').firstChild.nodeValue;
    /* continue only if request is finished and response is ready (state 4) */
    var done = 4, ok = 200;
    if ((http.readyState == done) && (http.status == ok)) {
        /* server response (return value from function)
         is returned as a JSON string */
        respStatus = JSON.parse(http.responseText);

        /* check on status (could be used to update progress checklist) */
        if (respStatus.state == states.processing) {
            document.getElementById('results-pi-processing').className = 'progress-processing';
            setTimeout(function() {
                sendRequest(qsid);
            } ,1000);
        } else if (respStatus.state == states.training) {
            document.getElementById('results-pi-processing').className = 'progress-done';
            document.getElementById('results-pi-training').className = 'progress-processing';
            setTimeout(function(){
                sendRequest(qsid);
            },1000);
        } else if (respStatus.state == states.ranking) {
            document.getElementById('results-pi-processing').className = 'progress-done';
            document.getElementById('results-pi-training').className = 'progress-done';
            document.getElementById('results-pi-ranking').className = 'progress-processing';
            setTimeout(function(){
                sendRequest(qsid);
            },1000);
        } else if (respStatus.state == states.results_ready) {
            /* finally, redirect to the results page */
            resultpagestr = fullHomeLocation + 'searchres?qsid=' + qsid
            /* use replace function so back button goes back two
             pages to index page */
            location.replace(resultpagestr);
        } else if ((respStatus.state == states.fatal_error_or_socket_timeout) ||
                   (respStatus.state == states.invalid_qid) ||
                   (respStatus.state == states.result_read_error) ||
                   (respStatus.state == states.inactive)) {
            // if there is an error, display an alert, then return home
            err_msg = ''
            if (respStatus.err_msg) {
                err_msg = '\n\n' + respStatus.err_msg;
            }
            alert('The following error occurred when interacting with the backend: ' +
                  respStatus.state + ' ' + err_msg);
            location.replace( fullHomeLocation );
        } else {
            // state is not recognised - display an error and return home
            alert('State not recognised: ' + respStatus.state);
            location.replace( fullHomeLocation );
        }
    }
}

function sendRequest(qsid) {
    execstr = fullHomeLocation + 'execquery?qsid=' + qsid;
    /* if using IE, AJAX request are annoyingly cached, so add a random
     string to the end of the request to make it unique and prevent
     this */
    if (navigator.appName == 'Microsoft Internet Explorer') {
        execstr = execstr + '&time=' + new Date().getTime();
    }
    http.open('get', execstr);
    http.onreadystatechange = getProgress;
    /* must pass null argument for backwards compatibility with old versions of
     * firefox */
    http.send(null);
}
