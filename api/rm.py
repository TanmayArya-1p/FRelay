import math
from datetime import datetime, date
import time
import threading
from termcolor import colored
import os
import uuid
import glob
from tabulate import tabulate
from auth import RouteAuthSession
import psutil
import logging
import json
from telemetry import RenderMoniter

logging.basicConfig(filename='frelay.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s' , filemode='w')

with open('config.json') as f:
    config = json.load(f)
logging.info(f"LOADING CONFIG AT CONFIG.JSON : {str(config)}")

VERSION = config["VERSION"]

pre_maxFileSize = config["FILE_SIZE_LIMIT"]
if(pre_maxFileSize == -1):
	pre_maxFileSize = math.inf

pre_ap = False
if(config["AUTOPOPULATE"]):
	pre_ap = True


def generateID():
	return(str(uuid.uuid4()).split("-")[-1])

class RouteManager():
	def __init__(self,poolSize : int = config["INITIAL_ROUTE_POOL_SIZE"],route_pool : list = [] ,timeout : int = config["TIMEOUT"] , maxFileSize = pre_maxFileSize, autopopulate=pre_ap , autopopulateconfig=config["AUTOPOPULATE"]):
		self.maxFileSize= maxFileSize
		self.route_pool = [] 	
		self.poolSize = poolSize
		self.status_bar = []
		self.currPoolSize=0
		self.autopopulate = autopopulate
		self.autopopulateconfig = autopopulateconfig
		if(route_pool==[]):
			self.populatePool(poolSize)
		else:
			self.route_pool= route_pool
		self.RunTerminator = True
		self.timeout = timeout
		self.terminatorThread = threading.Thread(target=self.__terminator,daemon=True)
		self.terminatorThread.start()

	def __terminator(self):
		while self.RunTerminator:
			time.sleep(0.25)
			# time.sleep(0.25)
			# if(os.name == "nt"):
			# 	#os.system("cls")
			# 	pass
			# else:
			# 	os.system("clear")

			# print("FRelay",VERSION,end="\n\n")
			closedRoutes=0
			for i in self.route_pool:
				if(i.isOpen==True):
					#stat = "OPEN"
					pass
				else:
					closedRoutes+=1
					#stat = "CLOSE"
				if(i.isOpen==False and (datetime.now() - i.uploaded_time).seconds >=self.timeout):
					if(self.timeout != -1):
						logging.info(f"Route {i.rid} TIMEOUT")
						self.status_bar.append(f"Route {i.rid} TIMEOUT "+str(datetime.now()).split(".")[0])
						i.Open()
						RenderMoniter(self)
					pass
			if(self.autopopulate and self.currPoolSize!=self.autopopulateconfig["poolUpperLimit"] and closedRoutes >= 0.7*self.currPoolSize):
				self.status_bar.append("CROWD THRESHOLD EXCEEDED- POPULATING POOL "+str(datetime.now()).split(".")[0])

				logging.info("CROWD THRESHOLD EXCEEDED- POPULATING POOL")
				if(self.currPoolSize+self.autopopulateconfig['incr']>self.autopopulateconfig["poolUpperLimit"]):
					self.populatePool(self.autopopulateconfig["poolUpperLimit"]-self.currPoolSize)
				else:
					self.populatePool(self.autopopulateconfig['incr'])
				RenderMoniter(self)
			

	def findOpenRoute(self):
		for i in self.route_pool:
			if(i.isOpen==True):
				logging.debug(f"FOUND OPEN ROUTE AT {i.rid}")
				return i
		else:
			logging.debug("OPEN ROUTE NOT FOUND")
			return None

	def routeLookup(self,rid):
		for i in self.route_pool:
			if(str(i.rid) == str(rid)):
				return i
		else:
			return None

	def flush(self):
		self.route_pool = []
		RouteAuthSession.resetTable()
		files = glob.glob(os.getcwd()+"/tmp/*")
		for f in files:
			os.remove(f)
		self.populatePool(self.poolSize)

	def populatePool(self,newMem):
		self.currPoolSize+=newMem
		for i in range(newMem):
			#time.sleep(random.random())
			self.route_pool.append(Route(rid=generateID(), manager=self))



class Route():
	def __init__(self,manager=None,bufferLimit=math.inf,isOpen=True,uploaded_time = datetime.now(),rid=None,cacheLimit=lambda x: config["CACHE_FILE_SIZE_LIMIT"], RAMcacheLimit = config["RAM_LIMIT_ON_CACHING"]):
		if(rid==None):
			self.rid = generateID()
		else:
			self.rid = rid
		self.manager = manager
		self.auth = None
		self.bufferLimit = bufferLimit
		self.isOpen =isOpen
		self.uploaded_time = uploaded_time
		self.file= None
		self.ext = None
		self.cached = False
		self.cacheLimit = cacheLimit
		self.RAMcacheLimit = RAMcacheLimit
		RenderMoniter(self.manager)

	def Close(self,file):

		if(self.isOpen==True):
			self.file = file
			self.isOpen=False
			self.uploaded_time = datetime.now()
			contents = self.file.file.read()
			self.contents = contents
			self.ext = file.filename.split(".")[-1]
			if(self.file.size>self.cacheLimit(psutil.virtual_memory().percent) or psutil.virtual_memory().percent>self.RAMcacheLimit):
				with open(rf"{os.getcwd()}/tmp/{self.rid}.{self.ext}", 'wb') as f:
					f.write(contents)
					RenderMoniter(self.manager)
					return True
			else:
				self.cached = True
			RenderMoniter(self.manager)
			return True
		else:
			logging.warn(f"{self} is already bound")

	def Open(self,remv=True):

		self.auth.destroy()
		self.isOpen = True
		self.uploaded_time = None
		ret = None
		if(remv):
			try:
				ret = (os.getcwd()+r"/tmp/"+str(self.rid)+"."+self.ext)
				os.remove(rf"./tmp/{self.rid}.{self.ext}")
			except:
				pass
			self.file = None
			self.ext = None
		RenderMoniter(self.manager)
		return ret






	
