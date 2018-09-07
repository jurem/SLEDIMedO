let testVariable = 1;
function showResult(str) {
    if (str.length==0) { 
        document.getElementById("livesearch").innerHTML="";
        document.getElementById("livesearch").style.border="0px";
        return;
    }
    if (window.XMLHttpRequest) {
        // code for IE7+, Firefox, Chrome, Opera, Safari
        xmlhttp=new XMLHttpRequest();
    } else {  // code for IE6, IE5
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    
    xmlhttp.onreadystatechange=function() {
        if (this.readyState==4 && this.status==200) {
            testVariable = JSON.parse(this.responseText);
            let livesearch_div = document.getElementById("livesearch");
            livesearch_div.innerHTML = "";
            console.log(testVariable);
            for (let i = 0; i < testVariable.length; i++){
                let result_div = document.createElement("div");
                result_div.classList.add("result");
                result_div.innerHTML = testVariable[i]["CAPTION"];

                let link = document.createElement("a");
                link.href = window.location.pathname+"index.php/article?id="+testVariable[i]["ID"];

                link.appendChild(result_div);
                livesearch_div.appendChild(link);
            }
            //document.getElementById("livesearch").style.border="1px solid #A5ACB2";
        }
    }
    xmlhttp.open("GET","index.php/articles/livesearch/?q="+str,true);
    xmlhttp.send();
}