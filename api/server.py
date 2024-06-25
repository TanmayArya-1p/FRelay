from rm import *
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import threading
from auth import RouteAuthSession,verifyMasterKey
import uvicorn


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
async def ping():
    return {"message" : "Relay Server is Alive"}

@app.get("/reset",tags=["Methods"])
async def reset(master_key):
    print("RESET")
    if(verifyMasterKey(master_key)):
        appendStatusStack(rm.status_bar,"RE-POPULATING ROUTE POOL")
        rm.flush()
        return {"message" : "Reset Succeeded"}
    else:
        appendStatusStack(rm.status_bar,"RESET FAILED - INCORRECT MASTER KEY")
        return {"message" : "Reset Failed"}

@app.post("/upload",tags=["Methods"])
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

@app.get("/fetch/{route_id}",tags=["Methods"])
async def fetchFile(route_id,authkey,master_key):
    if(verifyMasterKey(master_key)):
        i = rm.routeLookup(route_id)
        if(i!=None and i.isOpen==False and i.auth.verifyPass(authkey)):
            appendStatusStack(rm.status_bar,f"DELIVERING FILE AT '/fetch/{route_id}'")
            returner = FileResponse(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext)
            i.Open(remv=False)
            threading.Thread(target=deleter,args=(os.getcwd()+"\\tmp\\"+str(i.rid)+"."+i.ext,),daemon=True).start()
            return returner

        else:
            return {"message":f"route id {route_id} doesnt exit."}
    else:
        appendStatusStack(rm.status_bar,"FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}

@app.get("/routes",tags=["Methods"])
async def routesfetch(master_key):
    if(verifyMasterKey(master_key)):
        d = {}
        for i in rm.route_pool:
            d[i.rid] = i.isOpen
        return d
    else:
        appendStatusStack(rm.status_bar,"FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}

