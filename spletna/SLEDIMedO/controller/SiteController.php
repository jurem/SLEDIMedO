<?php

require_once("ViewHelper.php");

class SiteController {

	public static function index() {
        SiteController::render("home-page.php", []);
    }

    public static function about() {
        SiteController::render("about.php", []);
    }

    public static function instructions() {
        SiteController::render("instructions.php", []);
    }

    public static function showArticle() {
        $article = ArticlesDB::getArticle($_GET["id"]);
        SiteController::render("article.php", ["article" => $article]);
    }

    public static function error404() {
        SiteController::render("404.php", []);
    }

    public static function results() {

        $term = isset($_GET['search'])?$_GET['search']: '';
        $filter = '';

        if (isset($_GET['ff']) && !isset($_GET['sf'])){
            $filter = "10";
        } else if (!isset($_GET['ff']) && isset($_GET['sf'])) {
            $filter = "01";
        }

        if (strlen($term) > 0){
            $results = SiteController::search($term, $filter);
            SiteController::render("results.php", $results ? ["results" => $results] : ["results" => ""]);
        } else {
            ViewHelper::redirect(BASE_URL);
        }
    }

    public static function render($path, $v) {
        $link = "view/";

        if (isset($_SESSION["lang"]) && $_SESSION["lang"] == "en"){
            $link = $link . "en/";
        }

        ViewHelper::render($link . $path, $v);
    }

    function search($query, $filter){
        $query = trim($query);
        if (mb_strlen($query)===0)
            return false;

        $query = SiteController::limitChars($query);

        $scoreFullTitle = 6;
        $scoreTitleKeyword = 5;
        $scoreFullContent = 5;
        $scoreContentKeyword = 4;
        $scoreFullDocument = 4;
        $scoreDocumentKeyword = 3;
        $scoreCategoryKeyword = 2;
        $scoreUrlKeyword = 1;

        $keywords = SiteController::filterSearchKeys($query);
        $titleSQL = array();
        $sumSQL = array();
        $urlSQL = array();

        if (count($keywords) > 1){
            $titleSQL[] = "case when CAPTION LIKE '%".$query."%' then $scoreFullTitle else 0 end";
            $sumSQL[] = "case when CONTENTS LIKE '%".$query."%' then $scoreFullContent else 0 end";
        }

        foreach ($keywords as $key) {
            $titleSQL[] = "case when CAPTION LIKE '".$key." %' OR CAPTION LIKE '% ".$key."' OR CAPTION LIKE '% ".$key." %' OR CAPTION = '".$key."' then $scoreTitleKeyword else 0 end";
            $sumSQL[] = "case when CONTENTS LIKE '".$key." %' OR CONTENTS LIKE '% ".$key."' OR CONTENTS LIKE '% ".$key." %' OR CONTENTS = '".$key."' then $scoreContentKeyword else 0 end";
            $urlSQL[] = "case when URL LIKE '".$key." %' OR URL LIKE '% ".$key."' OR URL LIKE '% ".$key." %' OR URL = '".$key."' then $scoreUrlKeyword else 0 end";
        }

        // Just incase it's empty, add 0
        if (empty($titleSQL))
            $titleSQL[] = 0;
        
        if (empty($sumSQL))
            $sumSQL[] = 0;
        
        if (empty($urlSQL))
            $urlSQL[] = 0;
        
       
        if ($filter == '') {
            $sql = "SELECT ID, CAPTION, CONTENTS, DATE, ( (".implode(' + ', $titleSQL).")+(".implode(' + ', $sumSQL).")+(".implode(' + ', $urlSQL).") ) as relevance FROM novice WHERE relevance > 0 ORDER BY relevance DESC;";
        } else if ($filter == '01'){
            $sql = "SELECT ID, CAPTION, CONTENTS, DATE, ( (".implode(' + ', $titleSQL).")+(".implode(' + ', $sumSQL).")+(".implode(' + ', $urlSQL).") ) as relevance FROM novice WHERE SOURCE='INTERREG' AND relevance > 0 ORDER BY relevance DESC;";
        }  else if ($filter == '10') {
            $sql = "SELECT ID, CAPTION, CONTENTS, DATE, ( (".implode(' + ', $titleSQL).")+(".implode(' + ', $sumSQL).")+(".implode(' + ', $urlSQL).") ) as relevance FROM novice WHERE SOURCE != 'INTERREG' AND relevance > 0 ORDER BY relevance DESC;";
        }
		
        $results = ArticlesDB::executeQuery($sql);
        if (!$results)
            return false;
        return $results;
    }   

    function filterSearchKeys($query){
        $query = trim(preg_replace("/(\s+)+/", " ", $query));
        $words = array();

        $list = array("v", "na", "in", "ali", "če", "za", "pa", "je", "se", "bo");
        $query_limit = 0;
        foreach (explode(" ", $query) as $key) {
            if (in_array($key, $list))
                continue; // preskoči veznike, itd..
        
            $words[] = $key;

            if ($query_limit >= 10)
                break;
            $query_limit++;
        }
        return $words;
    }

    function limitChars($query, $limit = 200){
        return substr($query, 0, $limit);
    }
}

?>