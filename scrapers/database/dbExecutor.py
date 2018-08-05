import sqlite3
import re
databaseName = "database/articles.db"

# removes multiple newlines in the string, then removes 
# the start and finishing new lines if they exist
def removeNewLines(text):
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip('\n')
    text = text.strip('\t')
    text = text.strip('\r')
    return text

def repairNovica(novica):
    novicaList = list(novica)
    novicaList[1] = removeNewLines(novicaList[1])  # CAPTION
    novicaList[2] = removeNewLines(novicaList[2])  # CONTENTS
    return tuple(novicaList)

class dbExecutor:
    def __init__(self):
        return

    #sprejme tuple oblike (date_created: string, caption: string,
    #  contents: string,date: string,hash: string,url: string,source: string)
    # in vnese podatke v bazo
    @staticmethod
    def insertOne(novica, removeLines=False):
        try:
            if removeLines: novica = repairNovica(novica) # removes the exces new lines
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

    #vrne vrstico s podanim id-jem
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

    #vrne vrstico s podanim hash-om
    @staticmethod
    def getByHash(hashStr):
        data = None
        try:
            conn = sqlite3.connect(databaseName)
            cursor = conn.cursor()
            sql = 'SELECT * FROM NOVICE WHERE HASH=?'
            cursor.execute(sql,(hashStr,))
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

    # odstrani vrstico s podanim id-jem
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