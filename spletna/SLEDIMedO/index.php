<?php

session_start();

require_once("model/ArticlesDB.php");
require_once("controller/SiteController.php");

define("BASE_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php"));
define("IMAGES_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/img");
define("CSS_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/css/");
define("JS_URL", rtrim($_SERVER["SCRIPT_NAME"], "index.php") . "static/js/");

$request_uri = ltrim($_SERVER['REQUEST_URI'], "/SLEDIMedO");


$path = isset($_SERVER["PATH_INFO"]) ? trim($_SERVER["PATH_INFO"], "/") : $request_uri;


$urls = [
	"tests" => function () {
		SiteController::tests();
	},
	"zahvale" => function () {
		SiteController::thanks();
	},
	"navodila" => function () {
		SiteController::instructions();
	},
	"o-projektu" => function () {
		SiteController::about();
	},
	"test" => function () {
		print_r(ArticlesDB::getAllArticles());
	},
	"articles/get" => function () {
		echo json_encode(ArticlesDB::getAllArticles()); // returns articles
	},
	"articles/livesearch" => function () {
		echo json_encode(ArticlesDB::liveSearch($_GET["q"]));
	},
	"" => function () {
        ViewHelper::render("view/home-page.php");
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