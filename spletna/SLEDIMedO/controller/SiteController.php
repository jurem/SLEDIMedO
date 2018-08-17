<?php

require_once("ViewHelper.php");

class SiteController {

	public static function index() {
        ViewHelper::render("view/home-page.php", []);
    }

    public static function about() {
        ViewHelper::render("view/about.php", []);
    }

    public static function instructions() {
        ViewHelper::render("view/instructions.php", []);
    }

    public static function thanks() {
        ViewHelper::render("view/thanks.php", []);
    }

    public static function error404() {
        ViewHelper::render("view/404.php", []);
    }

    public static function tests() {
        ViewHelper::render("view/tests.php", []);
    }
}

?>