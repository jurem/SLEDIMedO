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

    public static function getArticle($id) {
        $db = DBInit::getInstance();

        $statement = $db->prepare("SELECT * FROM novice WHERE ID=:ID");
        $statement->bindParam(":ID", $id, PDO::PARAM_INT);
        $statement->execute();
        $db = null; // close a PDO connection

        return $statement->fetchAll(); // returns result
    }

    public static function executeQuery($sql) {
        $db = DBInit::getInstance();

        $statement = $db->prepare($sql);

        $statement->execute();
        $db = null;

        return $statement->fetchAll();
    }

    public static function liveSearch($str) {
        $db = DBInit::getInstance();

        $statement = $db->prepare("SELECT id, caption, contents, date FROM novice where LOWER( contents ) LIKE '%$str%' OR LOWER ( caption ) like '%$str%' OR source like '%$str%' LIMIT 5");
       // $statement->bindParam(":str", $str);

        $statement->execute();
        $db = null;

        return $statement->fetchAll();
    }

    public static function search($str) {
        $db = DBInit::getInstance();

        $statement = $db->prepare("SELECT * from novice where match(caption, contents, source) against ('$str')");
       // $statement->bindParam(":str", $str);

        $statement->execute();
        $db = null;
        
        return $statement->fetchAll();
    }
}