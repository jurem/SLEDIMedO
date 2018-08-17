<?php 

class DBInit {
    /**
     * Returns a PDO instance -- a connection to the SQLite database.
     * The singleton instance assures that there is only one connection active
     * at once (within the scope of one HTTP request)
     * 
     * @return PDO instance 
     */

    public static function getInstance() {
        $dbh = new PDO('sqlite:sql/articles.db', '', '', array(
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        ));

        return $dbh;
    }
}