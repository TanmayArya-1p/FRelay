
from hashlib import sha256
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib
import sqlite3

con = sqlite3.connect("pass.db", check_same_thread=False)
cursor = con.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS passhash(rid text PRIMARY KEY, pass text)")
auth_pool= list()

class RouteAuthSession():
    def __init__(self,route,authkey):
        pswrd = authkey
        self.route = route
        self.route.auth = self
        hash = sha256(pswrd.encode('utf-8')).hexdigest()
        cursor.execute(f"INSERT OR IGNORE INTO passhash VALUES('{self.route.rid}','{hash}');")
        del hash
        del pswrd
        del authkey
        auth_pool.append(self)


    @staticmethod
    def resetTable():
        global auth_pool
        cursor.execute(f"DELETE FROM passhash;")
        for i in auth_pool:
            del i 
        
    
    @staticmethod
    def fetchSHAhash(rid):
        cursor.execute(f"SELECT pass FROM passhash WHERE rid ='{rid}'")
        return cursor.fetchone()[0]
    

    @staticmethod
    def fetchHashes():
        cursor.execute(f"SELECT * FROM passhash")
        d = dict()
        for i in cursor.fetchall():
            d[i[0]]= i[1]
        return d

    def verifyPass(self,authkey):
        hash = str(hashlib.sha256(authkey.encode('utf-8')).hexdigest())
        if hash == self.fetchSHAhash(self.route.rid):
            return True
        else:
            return False
    
    def destroy(self):
        cursor.execute(f"DELETE FROM passhash WHERE rid ='{self.route.rid}'")
        self.route.auth = None
        del self








