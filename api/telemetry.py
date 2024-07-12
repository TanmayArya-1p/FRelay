import time
import json
import os
from tabulate import tabulate
from termcolor import colored
import datetime

with open('config.json') as f:
    config = json.load(f)
VERSION = config["VERSION"]

def RenderMoniter(rm):
    if(os.name == "nt"):
        os.system("cls")
        pass
    else:
        os.system("clear")

    print("FRelay",VERSION,end="\n\n")
    l=[]
    enum = 0
    for i in rm.route_pool:
        enum+=1
        if(i.isOpen==True):
            stat=colored("OPEN","green")
        else:
            stat=colored("CLOSE","red")
        l.append([enum,str(i.rid), stat])
    try:
        print(tabulate(l, headers=["SNO","ROUTE ID", "STATUS"], tablefmt="rounded_outline",colalign=("center","center","center")))
        print("\nTASK HISTORY:")
        [print(i) for i in rm.status_bar[:5]]
    except:
        pass