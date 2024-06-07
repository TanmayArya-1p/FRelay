from typing import Union
import json
from rm import *
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import threading


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
async def uploadFile(file: UploadFile):
    print(file.filename)
    openR = rm.findOpenRoute()
    if(openR!=None):
        print(openR)
        openR.Close(file)

        return {"route_id" : openR.rid}
    else:
        return {"message":"ALL ROUTES OCCUPIED"}

def deleter(path):
    time.sleep(5)
    os.remove(path)

@app.get("/fetch/{route_id}")
async def fetchFile(route_id):
    i = rm.routeLookup(route_id)
    if(i!=None and i.isOpen==False):

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

