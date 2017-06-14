function getCookie(c_name)
{
var i,x,y,ARRcookies=document.cookie.split(";");
for (i=0;i<ARRcookies.length;i++)
  {
  x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
  y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
  x=x.replace(/^\s+|\s+$/g,"");
  if (x==c_name)
    {
    return unescape(y);
    }
  }
}

function setCookie(c_name,value,exdays)
{
    var exdate=new Date();
    exdate.setDate(exdate.getDate() + exdays);
    document.cookie=c_name + "=" + escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString()) + "; path=/";
}

window.onload = function()
{
    // Google Analytics
    var authorisecookies=getCookie("vgg_bbcn_usecookies");

    if ( authorisecookies == "true" )
    {
    }
    else
    {
        $(".slidingDiv").slideDown();

        $("#hide").click(function(){
           $(".slidingDiv").slideUp();
           setCookie("vgg_bbcn_usecookies","true",365);
           location.reload();
       });

    }
}

var authorisecookies=getCookie("vgg_bbcn_usecookies");

if ( authorisecookies == "true" )
{
    var _gaq = _gaq || [];
    _gaq.push(['_setAccount', 'UA-84656248-1']);
    _gaq.push(['_setDomainName', 'zeus.robots.ox.ac.uk']);
    _gaq.push(['_setAllowHash', false]);
    _gaq.push(['_setCookiePath', '/bbc_search/']);
    _gaq.push(['_trackPageview']);

    (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
    })();
}
