<?php

session_start();

require_once("model/ArticlesDB.php");
require_once("controller/SiteController.php");

define("BASE_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php"));
define("IMAGES_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/img");
define("CSS_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/css/");
define("JS_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/js/");

$request_uri_t = explode("/", trim($_SERVER['REQUEST_URI'], "/"));
$request_uri = $request_uri_t[count($request_uri_t)-1];

$path = isset($_SERVER["PATH_INFO"]) ? trim($_SERVER["PATH_INFO"], "/") : $request_uri;

if ($path == trim(BASE_URL, "/"))
	$path = "";

$urls = [
	"zahvale" => function () {
		SiteController::thanks();
	},
	"navodila" => function () {
		SiteController::instructions();
	},
	"o-projektu" => function () {
		SiteController::about();
	},
	"articles/get" => function () {
		echo json_encode(ArticlesDB::getAllArticles()); // returns articles
	},
	"articles/livesearch" => function () {
		echo json_encode(ArticlesDB::liveSearch($_GET["q"]));
	},
	"results" => function () {
		SiteController::results();
	},
	"article" => function () {
		SiteController::showArticle();
	},
	"en" => function() {
		$_SESSION["lang"] = "en";
		ViewHelper::redirect(BASE_URL);
	},
	"slo" => function() {
		$_SESSION["lang"] = "slo";
		ViewHelper::redirect(BASE_URL);
	},
	"" => function () {
		SiteController::index();
    },
];

try {
    if (isset($urls[$path])) {
       $urls[$path]();
    } else {
       	SiteController::error404();
    }
} catch (Exception $e) {
	SiteController::error404();
} 

?>