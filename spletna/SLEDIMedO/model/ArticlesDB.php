<?php

require_once "DBInit.php";

class ArticlesDB {

    public static function getAllArticles() {
        $db = DBInit::getInstance();

        $statement = $db->prepare("SELECT * FROM novice");
        $statement->execute();
        $db = null; // close a PDO connection

        return $statement->fetchAll(); // returns result
    }

    public static function liveSearch($str) {
        $db = DBInit::getInstance();

        $statement = $db->prepare("SELECT caption FROM novice where caption like '%$str%'");
       // $statement->bindParam(":str", $str);

        $statement->execute();

        return $statement->fetchAll();
    }
}