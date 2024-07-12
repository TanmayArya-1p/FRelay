from rm import *
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, Response
import threading
from auth import RouteAuthSession,verifyMasterKey
from contextlib import asynccontextmanager
import threading

tags_metadata = [
    {
        "name": "Methods",
        "description": "",
    }]
rm = RouteManager()
app = FastAPI(title="FRelay" , version=VERSION,docs_url="/simulate",openapi_tags=tags_metadata)

def startup():
    time.sleep(2)
    RenderMoniter(rm)
    return True
threading.Thread(target=startup,daemon=True).start()

@app.get("/",tags=["Methods"])
async def ping():
    logging.info("Server Ping Received")
    rm.status_bar.append("Server Ping Received "+str(datetime.now()).split(".")[0])
    RenderMoniter(rm)
    return {"message" : "Relay Server is Alive"}

@app.get("/reset",tags=["Methods"])
async def reset(master_key):
    print("RESET")
    if(verifyMasterKey(master_key)):
        rm.status_bar.append("RE-POPULATING ROUTE POOL "+str(datetime.now()).split(".")[0])

        logging.info("RE-POPULATING ROUTE POOL")
        rm.flush()
        RenderMoniter(rm)
        return {"message" : "Reset Succeeded"}
    else:
        rm.status_bar.append("RESET FAILED - INCORRECT MASTER KEY "+str(datetime.now()).split(".")[0])
        RenderMoniter(rm)
        logging.critical("RESET FAILED - INCORRECT MASTER KEY")
        return {"message" : "Reset Failed"}

@app.post("/upload",tags=["Methods"])
async def uploadFile(file: UploadFile,authkey,master_key):
    if(verifyMasterKey(master_key)):
        if(file.size<rm.maxFileSize):
            print(file.filename)
            openR = rm.findOpenRoute()
            if(openR!=None):
                print(openR)
                rm.status_bar.append(f"RECEIVED FILE '{file.filename}' AT ROUTE '{openR.rid}' : SIZE = {file.size} BYTES {(file.content_type)} "+str(datetime.now()).split(".")[0])

                logging.info(f"RECEIVED FILE '{file.filename}' AT ROUTE '{openR.rid}' : SIZE = {file.size} BYTES {(file.content_type)}")
                openR.Close(file)
                openR.auth= RouteAuthSession(openR,authkey)
                RenderMoniter(rm)
                return {"route_id" : openR.rid, "timeout":rm.timeout}
            else:
                logging.critical("ALL ROUTES OCCUPIED")
                rm.status_bar.append("ALL ROUTES OCCUPIED "+str(datetime.now()).split(".")[0])
                RenderMoniter(rm)
                return {"message":"ALL ROUTES OCCUPIED"}
        else:
            logging.critical(f"Exceeded maxFileSize = {rm.maxFileSize} bytes")
            rm.status_bar.append(f"Exceeded maxFileSize = {rm.maxFileSize} bytes "+str(datetime.now()).split(".")[0])
            RenderMoniter(rm)
            return {"message" : f"Exceeded maxFileSize = {rm.maxFileSize} bytes"}
    else:
        rm.status_bar.append("UPLOAD FAILED - INCORRECT MASTER KEY "+str(datetime.now()).split(".")[0])
        RenderMoniter(rm)
        logging.critical("UPLOAD FAILED - INCORRECT MASTER KEY")
        return {"message" : "Upload Failed"}

def deleter(path):
    time.sleep(rm.timeout)
    logging.debug("Deleter Called")
    os.remove(path)

@app.get("/fetch/{route_id}",tags=["Methods"])
async def fetchFile(route_id,authkey,master_key):
    if(verifyMasterKey(master_key)):
        i = rm.routeLookup(route_id)
        if(i!=None and i.isOpen==False and i.auth.verifyPass(authkey)):
            rm.status_bar.append(f"DELIVERING FILE AT '/fetch/{route_id}' " + f"{i.file.content_type} "+str(datetime.now()).split(".")[0])
            logging.info(f"DELIVERING FILE AT '/fetch/{route_id}'" + f"image/{i.ext}")
            if(not i.cached):
                returner = FileResponse(os.getcwd()+"/tmp/"+str(i.rid)+"."+i.ext)
            else:
                print(i.file.file)
                logging.info(f"DELIVERING CACHED FILE")
                rm.status_bar.append(f"DELIVERING CACHED FILE "+str(datetime.now()).split(".")[0])
                RenderMoniter(rm)
                returner = Response(content=i.contents, media_type=i.file.content_type)
            i.Open(remv=False)
            if(i.cached==False):
                threading.Thread(target=deleter,args=(os.getcwd()+"/tmp/"+str(i.rid)+"."+i.ext,),daemon=True).start()
            else:
                def cachedDeleter():
                    i.file = None
                    i.ext = None
                threading.Thread(target=cachedDeleter,daemon=True).start()
            RenderMoniter(rm)
            return returner

        else:
            logging.critical(f"route id {route_id} doesnt exit.")
            rm.status_bar.append(f"route id {route_id} doesnt exit. "+str(datetime.now()).split(".")[0])
            RenderMoniter(rm)
            return {"message":f"route id {route_id} doesnt exit."}
    else:
        rm.status_bar.append("FETCH FAILED - INCORRECT MASTER KEY "+str(datetime.now()).split(".")[0])
        RenderMoniter(rm)
        logging.critical("FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}

@app.get("/routes",tags=["Methods"])
async def routesfetch(master_key):
    if(verifyMasterKey(master_key)):
        d = {}
        logging.info("Fetching Routes...")
        rm.status_bar.append("Fetching Routes... "+str(datetime.now()).split(".")[0])

        for i in rm.route_pool:
            d[i.rid] = i.isOpen
        RenderMoniter(rm)
        return d
    else:
        rm.status_bar.append("FETCH FAILED - INCORRECT MASTER KEY "+str(datetime.now()).split(".")[0])
        RenderMoniter(rm)
        logging.critical("FETCH FAILED - INCORRECT MASTER KEY")
        return {"message" : "Fetch Failed"}
