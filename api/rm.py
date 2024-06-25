import math
from datetime import datetime, date
import time
import threading
from termcolor import colored
import os
import uuid
import random
import glob
from tabulate import tabulate
from auth import RouteAuthSession
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")
VERSION = dict(config._sections["frelay"])["version"]

def appendStatusStack(l,i,bufferLimit = 4):
    if(len(l) == bufferLimit):
        l.pop(0)
        l.append(i+"    "+str(datetime.now()).split(".")[0])
    else:
        l.append(i+"    "+str(datetime.now()).split(".")[0])

def generateID():
	return(str(uuid.uuid4()).split("-")[-1])

class RouteManager():
	def __init__(self,poolSize : int = 10,route_pool : list = [] ,timeout : int = 30 , maxFileSize = math.inf, autopopulate=True , autopopulateconfig={'poolUpperLimit':25,'threshold':0.7}):
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
			if(os.name == "nt"):
				os.system("cls")
			else:
				os.system("clear")

			print("FRelay",VERSION,end="\n\n")
			l=[]
			enum = 0
			closedRoutes=0
			for i in self.route_pool:
				enum+=1
				if(i.isOpen==True):
					stat=colored("OPEN","green")
					#stat = "OPEN"
				else:
					closedRoutes+=1
					stat=colored("CLOSE","red")
					#stat = "CLOSE"
				l.append([enum,str(i.rid), stat])
				if(i.isOpen==False and (datetime.now() - i.uploaded_time).seconds >=self.timeout):
					if(self.timeout != -1):
						i.Open()
					pass
			try:
				print(tabulate(l, headers=["SNO","ROUTE ID", "STATUS"], tablefmt="rounded_outline",colalign=("center","center","center")))
				print("\nTASK HISTORY:")
				[print(i) for i in self.status_bar]
			except:
				pass
			if(self.autopopulate and self.currPoolSize!=self.autopopulateconfig["poolUpperLimit"] and closedRoutes >= 0.7*self.currPoolSize):
				appendStatusStack(self.status_bar , "CROWD THRESHOLD EXCEEDED- POPULATING POOL")
				if(self.currPoolSize+self.poolSize>self.autopopulateconfig["poolUpperLimit"]):
					self.populatePool(self.autopopulateconfig["poolUpperLimit"]-self.currPoolSize)
				else:
					self.populatePool(self.poolSize)
			

	def findOpenRoute(self):
		for i in self.route_pool:
			if(i.isOpen==True):
				return i
		else:
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
		files = glob.glob(os.getcwd()+"\\tmp\\*")
		for f in files:
			os.remove(f)
		self.populatePool(self.poolSize)

	def populatePool(self,newMem):
		self.currPoolSize+=newMem
		for i in range(newMem):
			time.sleep(random.random())
			self.route_pool.append(Route(rid=generateID()))



class Route():
	def __init__(self,bufferLimit=math.inf,isOpen=True,uploaded_time = datetime.now(),rid=None):
		if(rid==None):
			self.rid = generateID()
		else:
			self.rid = rid
		self.auth = None
		self.bufferLimit = bufferLimit
		self.isOpen =isOpen
		self.uploaded_time = uploaded_time
		self.file= None
		self.ext = None

	def Close(self,file):
		if(self.isOpen==True):
			self.file = file.file
			self.isOpen=False
			self.uploaded_time = datetime.now()
	
			contents = self.file.read()
			self.ext = file.filename.split(".")[-1]
			with open(f"{os.getcwd()}\\tmp\\{self.rid}.{self.ext}", 'wb') as f:
				f.write(contents)
				return True
		else:
			print(f"{self} is already bound")

	def Open(self,remv=True):
		self.auth.destroy()
		self.isOpen = True
		self.file = None

		self.uploaded_time = None
		ret = (os.getcwd()+"\\tmp\\"+str(self.rid)+"."+self.ext)

		if(remv):
			os.remove(f".//tmp//{self.rid}.{self.ext}")
			self.ext = None
		return ret






	
