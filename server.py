from rm import *
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import threading
from auth import RouteAuthSession

rm = RouteManager()

app = FastAPI(debug=True)


@app.get("/")
async def home():
    return {"message" : "Relay Server is Alive"}

@app.get("/reset")
async def reset():
    print("RESET")
    rm.status_bar="RESETTING......"
    rm.flush()
    rm.status_bar=""
    return {"message" : "OK"}

@app.post("/upload")
async def uploadFile(file: UploadFile,authkey):
    print(file.filename)
    openR = rm.findOpenRoute()
    if(openR!=None):
        print(openR)
        openR.Close(file)
        openR.auth= RouteAuthSession(openR,authkey)
        return {"route_id" : openR.rid, "timeout":rm.timeout}
    else:
        return {"message":"ALL ROUTES OCCUPIED"}

def deleter(path):
    time.sleep(rm.timeout)
    os.remove(path)

@app.get("/fetch/{route_id}")
async def fetchFile(route_id,authkey):
    i = rm.routeLookup(route_id)
    if(i!=None and i.isOpen==False and i.auth.verifyPass(authkey)):
        returner = FileResponse(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext)
        i.Open(remv=False)
        threading.Thread(target=deleter,args=(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext,),daemon=True).start()
        return returner

    else:
        return {"message":f"route id {route_id} doesnt exit."}

@app.get("/routes")
async def routesfetch():
    d = {}
    for i in rm.route_pool:
        d[i.rid] = i.isOpen
    return d

