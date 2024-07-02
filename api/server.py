from rm import *
from fastapi import FastAPI, File, UploadFile , Request
from fastapi.responses import FileResponse
import threading
from auth import RouteAuthSession,verifyMasterKey
import json
from hashlib import sha256 
import time

tags_metadata = [
    {
        "name": "Methods",
        "description": "",
    }]
rm = RouteManager()
app = FastAPI(debug=True, title="FRelay" , version=VERSION,docs_url="/simulate",openapi_tags=tags_metadata)

#ELPT= epoch Last Ping Time
config = ConfigParser()
config.read("config.ini")
STIMEOUT = int(dict(config._sections["frelay"])["stimeout"])


def sessionMetaData():
    f = open('sessions.json')
    data = json.load(f)
    f.close()
    return data

def updateSessionMetaData(d):
    with open('sessions.json', 'w') as f:
        json.dump(d, f)
    return d


def updateSessionELPT(sid):
    data = sessionMetaData()
    data[sid]["elpt"] = int(time.time())
    updateSessionMetaData(data)

def killDormantSessions():
    data = sessionMetaData()
    rmv = []
    for i in data:
        if((int(time.time()) - data[i]["elpt"]) >= STIMEOUT):
            rmv.append(i)
    [data.pop(i) for i in rmv]
    updateSessionMetaData(data)

def appendStatusStack(l,i,bufferLimit = 4):
    if(len(l) == bufferLimit):
        l.pop(0)
        l.append(i+"    "+str(datetime.now()).split(".")[0])
    else:
        l.append(i+"    "+str(datetime.now()).split(".")[0])

@app.get("/",tags=["Methods"])
async def ping():
    return {"message" : "Relay Server is Alive"}


@app.get("/session/{session_id}", tags = ["Session Management"])
async def sessionFetch(session_id,session_key,master_key):
    if(verifyMasterKey(master_key)):
        data = sessionMetaData()
        if(data.get(session_id) != None):
            if(data[session_id]["session_key"] == sha256(session_key.encode('utf-8')).hexdigest()):
                updateSessionELPT(session_id)
                killDormantSessions()
                return data[session_id]["img_hashes"]
            else:
                return {"message" : "session authentication failed"}

        else:
            return {"message" : f"{session_id} does not exist"}
    else:
        appendStatusStack(rm.status_bar,"SESSION FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}


@app.post("/session/{session_id}" , tags = ["Session Management"])
async def sessionUpdate(request: Request,session_id,master_key,session_key):
    #ONLY IMG HASHES HAS TO BE SENT FROM CLIENT :IMP   
    #{"data" : [(imghash,rid)]}
    if(verifyMasterKey(master_key)):
        data = sessionMetaData()
        if(data.get(session_id) != None):
            if(data[session_id]["session_key"] == sha256(session_key.encode('utf-8')).hexdigest()):
                #appendStatusStack(rm.status_bar,str(await request.json()))
                data = dict(await request.json())["data"]
                k = sessionMetaData()
                k[session_id]["img_hashes"] = data
                updateSessionMetaData(k)
                return {"message" : "Success"}
            else:
                return {"message" : "session authentication failed"}
        else:
            return {"message" : f"{session_id} does not exist"}
    else:
        appendStatusStack(rm.status_bar,"SESSION UPDATE FAILED - INCORRECT MASTER KEY")
        return {"message" : "Update Failed"}
    


@app.post("/session/{session_id}/appendImg",tags = ["Session Management"])
async def appendImg(request : Request,master_key,session_id,session_key):
    # SEND IMG AS {"data" : [imghash,uimgrid]} )
    if(verifyMasterKey(master_key)):
        data = sessionMetaData()
        if(data.get(session_id) != None):
            if(data[session_id]["session_key"] == sha256(session_key.encode('utf-8')).hexdigest()):
                l =data[session_id]["img_hashes"].copy()
                if(len(l) == 5):
                    clearRoute(l.pop(0)[1])
                    l.append(dict(await request.json())["data"]) #ITS  A REVERSE STACK ***********************
                else:
                    l.append(dict(await request.json())["data"])
                data[session_id]["img_hashes"] = l
                updateSessionMetaData(data)
                return {"message" : "Successful"}
            else:
                return {"message" : "session authentication failed"}
        else:
            return {"message" : f"{session_id} does not exist"}
    else:
        appendStatusStack(rm.status_bar,"SESSION UPDATE FAILED - INCORRECT MASTER KEY")
        return {"message" : "Update Failed"}


@app.post("/sessionCreate", tags = ["Session Management"])
async def sessionCreate(master_key,session_key):
    if(verifyMasterKey(master_key)):
        data =sessionMetaData()
        sk = sha256(session_key.encode('utf-8')).hexdigest()
        del session_key
        session_id = generateID()
        data[session_id] = {
            "session_key": sk,
            "img_hashes" : [],
            "elpt" : int(time.time())
        }
        updateSessionMetaData(data)
        return {"session_id" : session_id}
    else:
        return {"message" : "Request Failed"}

@app.post("/sessionDestroy" , tags = ["Session Management"])
async def sessionDestroy(master_key,session_id,session_key):
    if(verifyMasterKey(master_key)):
        data = sessionMetaData()
        if(data.get(session_id) != None):
            if(data[session_id]["session_key"] == sha256(session_key.encode('utf-8')).hexdigest()):
                data.pop(session_id)
                updateSessionMetaData(data)
                return {}
            else:
                return {"message" : "session authentication failed"}
        else:
            return {"message" : f"{session_id} does not exist"}
    else:
        appendStatusStack(rm.status_bar,"SESSION DELETE FAILED - INCORRECT MASTER KEY")
        return {"message" : "Request Failed"}



"""
{
"sid" : {
sk= skhash
imghashes:[
[imghash,rid],
.
.
.
]
elpt:""
}
}
"""




@app.get("/reset",tags=["Single File Relay"])
async def reset(master_key):
    print("RESET")
    if(verifyMasterKey(master_key)):
        appendStatusStack(rm.status_bar,"RE-POPULATING ROUTE POOL")
        rm.flush()
        updateSessionMetaData({})
        return {"message" : "Reset Succeeded"}
    else:
        appendStatusStack(rm.status_bar,"RESET FAILED - INCORRECT MASTER KEY")
        return {"message" : "Reset Failed"}
    
@app.get("/sessions" , tags=["Session Management"])
async def fetchAliveSessions(master_key):
    if(verifyMasterKey(master_key)):
        data = sessionMetaData()
        l=[]
        for i in data:
            l.append(i)
        return {"sessions" : l}
    else:
        return {"message" : "Fetch failed"}

@app.post("/upload",tags=["Single File Relay"])
async def uploadFile(file: UploadFile,authkey,master_key):
    if(verifyMasterKey(master_key)):
        if(file.size<rm.maxFileSize):
            print(file.filename)
            openR = rm.findOpenRoute()
            if(openR!=None):
                print(openR)
                appendStatusStack(rm.status_bar,f"RECEIVED FILE '{file.filename}' AT ROUTE '{openR.rid}' : SIZE = {file.size} BYTES")
                openR.Close(file)
                openR.auth= RouteAuthSession(openR,authkey)
                return {"route_id" : openR.rid, "timeout":rm.timeout}
            else:
                return {"message":"ALL ROUTES OCCUPIED"}
        else:
            return {"message" : f"Exceeded maxFileSize = {rm.maxFileSize} bytes"}
    else:
        appendStatusStack(rm.status_bar,"UPLOAD FAILED - INCORRECT MASTER KEY")
        return {"message" : "Upload Failed"}

def deleter(path):
    time.sleep(rm.timeout)
    os.remove(path)

def clearRoute(rid):
    i = rm.routeLookup(rid)
    i.Open(remv=False)
    threading.Thread(target=deleter,args=(os.getcwd()+r"/tmp/"+str(i.rid)+"."+i.ext,),daemon=True).start()

@app.get("/fetch/{route_id}",tags=["Single File Relay"])
async def fetchFile(route_id,authkey,master_key,ses):
    if(verifyMasterKey(master_key)):
        i = rm.routeLookup(route_id)
        if(i!=None and i.isOpen==False and i.auth.verifyPass(authkey)):
            appendStatusStack(rm.status_bar,f"DELIVERING FILE AT '/fetch/{route_id}'")
            returner = FileResponse(os.getcwd()+r"/tmp/"+str(i.rid)+"."+i.ext)
            if(ses=="0"):
                i.Open(remv=False)
                threading.Thread(target=deleter,args=(os.getcwd()+r"/tmp/"+str(i.rid)+"."+i.ext,),daemon=True).start()
            return returner

        else:
            return {"message":f"route id {route_id} doesnt exit."}
    else:
        appendStatusStack(rm.status_bar,"FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}

@app.get("/routes",tags=["Single File Relay"])
async def routesfetch(master_key):
    if(verifyMasterKey(master_key)):
        d = {}
        for i in rm.route_pool:
            d[i.rid] = i.isOpen
        return d
    else:
        appendStatusStack(rm.status_bar,"FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}

