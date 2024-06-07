import math
from datetime import datetime, date
import logging
import hashlib
import time
import threading
from termcolor import colored
import os
import uuid
import random
import glob
from tabulate import tabulate

def generateID():
	return(str(uuid.uuid4()).split("-")[-1])


class RouteManager():
	def __init__(self,poolSize : int = 10,route_pool : list = [] ,timeout : int = 10 ):
		self.route_pool = []`
		self.poolSize = poolSize
		self.status_bar = ""
		if(route_pool==[]):
			self.populatePool(poolSize)
		else:
			self.route_pool= route_pool
		self.RunTerminator = True
		self.timeout = timeout
		self.terminatorThread = threading.Thread(target=self.__terminator,daemon=True)
		self.terminatorThread.start()

	def __terminator(self):
		os.system('mode con: cols=35 lines=20')
		while self.RunTerminator:
			time.sleep(0.25)
			os.system("cls")
			l=[]
			enum = 0
			for i in self.route_pool:
				enum+=1
				if(i.isOpen==True):
					stat=colored("OPEN","green")
					#stat = "OPEN"
				else:
					stat=colored("CLOSE","red")
					#stat = "CLOSE"
				l.append([enum,str(i.rid), stat])
				if(i.isOpen==False and (datetime.now() - i.uploaded_time).seconds >=self.timeout):
					i.Open()
			try:
				print(tabulate(l, headers=["SNO","ROUTE ID", "STATUS"], tablefmt="rounded_outline",colalign=("center","center","center")))
				print(self.status_bar)
			except:
				pass
			

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
		files = glob.glob(os.getcwd()+"\\tmp\\*")
		for f in files:
			os.remove(f)
		self.populatePool(self.poolSize)

	def populatePool(self,newMem):
		for i in range(newMem):
			time.sleep(random.random())
			self.route_pool.append(Route(rid=generateID()))



class Route():
	def __init__(self,bufferLimit=math.inf,isOpen=True,uploaded_time = datetime.now(),rid=None):
		if(rid==None):
			self.rid = generateID()
		else:
			self.rid = rid
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
		self.isOpen = True
		self.file = None

		self.uploaded_time = None
		ret = (os.getcwd()+"\\tmp\\"+str(self.rid)+"."+self.ext)

		if(remv):
			os.remove(f".//tmp//{self.rid}.{self.ext}")
			self.ext = None
		return ret






	