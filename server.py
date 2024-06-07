from rm import *
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import threading
from auth import RouteAuthSession
tags_metadata = [
    {
        "name": "Methods",
        "description": "",
    }]
rm = RouteManager()
app = FastAPI(debug=True, title="FRelay" , version=VERSION,docs_url="/simulate",openapi_tags=tags_metadata)


def appendStatusStack(l,i,bufferLimit = 4):
    if(len(l) == bufferLimit):
        l.pop(0)
        l.append(i+"    "+str(datetime.now()).split(".")[0])
    else:
        l.append(i+"    "+str(datetime.now()).split(".")[0])

@app.get("/",tags=["Methods"])
async def home():
    return {"message" : "Relay Server is Alive"}

@app.get("/reset",tags=["Methods"])
async def reset():
    print("RESET")
    appendStatusStack(rm.status_bar,"RE-POPULATING ROUTE POOL")
    rm.flush()
    return {"message" : "OK"}

@app.post("/upload",tags=["Methods"])
async def uploadFile(file: UploadFile,authkey):
    print(file.filename)
    openR = rm.findOpenRoute()
    if(openR!=None):
        print(openR)
        appendStatusStack(rm.status_bar,f"RECEIVED FILE '{file.filename}' AT ROUTE '{openR.rid}'")
        openR.Close(file)
        openR.auth= RouteAuthSession(openR,authkey)
        return {"route_id" : openR.rid, "timeout":rm.timeout}
    else:
        return {"message":"ALL ROUTES OCCUPIED"}

def deleter(path):
    time.sleep(rm.timeout)
    os.remove(path)

@app.get("/fetch/{route_id}",tags=["Methods"])
async def fetchFile(route_id,authkey):
    i = rm.routeLookup(route_id)
    if(i!=None and i.isOpen==False and i.auth.verifyPass(authkey)):
        appendStatusStack(rm.status_bar,f"DELIVERING FILE AT '/fetch/{route_id}'")
        returner = FileResponse(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext)
        i.Open(remv=False)
        threading.Thread(target=deleter,args=(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext,),daemon=True).start()
        return returner

    else:
        return {"message":f"route id {route_id} doesnt exit."}

@app.get("/routes",tags=["Methods"])
async def routesfetch():
    d = {}
    for i in rm.route_pool:
        d[i.rid] = i.isOpen
    return d

