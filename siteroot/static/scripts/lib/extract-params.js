function extractParams(param, unescape) {
    if (unescape==null) unescape = true;
    
    params = window.location.href;
    params = params.substr(params.indexOf('?')+1);
    
    strstart = params.indexOf(param+'=');
    strstart = strstart + param.length + 1;
    strend = params.indexOf('&',strstart);
    if (strend == -1) {
	strend = params.length;
    }

    resultstr = params.substr(strstart,strend-strstart);
    
    if (unescape)
    {
	resultstr = unescape(resultstr);
	/* replace all '+' signs with spaces */
	while (true) {
	    i = resultstr.indexOf('+');
	    if (i == -1) break;
	    resultstr = resultstr.substr(0,i) + ' ' +
		resultstr.substr(i+1,resultstr.length);
	}
    }
    
    return resultstr;
}
