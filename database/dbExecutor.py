import sqlite3
databaseName = "articles.db"

class dbExecutor:
    def __init__(self):
        return

    #sprejme tuple oblike (date_created: string, caption: string,
    #  contents: string,date: string,hash: string,url: string,source: string)
    # in vnese podatke v bazo
    @staticmethod
    def insertOne(novica):
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            query = 'INSERT INTO NOVICE(DATE_CREATED,CAPTION,CONTENTS,DATE,HASH,URL,SOURCE) VALUES (?,?,?,?,?,?,?)'
            cursor.execute(query, novica)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return

    #sprejme seznam tuplov oblike [(date_created: string, caption: string,
    #  contents: string,date: string,hash: string,url: string,source: string)]
    # in vnese podatke v bazo
    @staticmethod
    def insertMany(seznam):
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            query = 'INSERT INTO NOVICE(DATE_CREATED,CAPTION,CONTENTS,DATE,HASH,URL,SOURCE) VALUES (?,?,?,?,?,?,?)'
            cursor.executemany(query, seznam)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return

    #vrne vse vrstice v bazi
    @staticmethod
    def getAll():
        data = None
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM NOVICE')
            data = cursor.fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return data

    #metoda sprejme poljubni sql query in vrne rezultate
    @staticmethod
    def getBySqlQuery(query):
        data = None
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return data

    #vrne vrstico z podanim id-jem
    @staticmethod
    def getById(id=1):
        data = None
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            sql = 'SELECT * FROM NOVICE WHERE ID=?'
            cursor.execute(sql,(id,))
            data = cursor.fetchone()
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return data

    # odstrani vrstico z podanim id-jem
    @staticmethod
    def deleteById(id):
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            query = 'DELETE FROM NOVICE WHERE  ID=?'
            cursor.execute(query, (id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
        return