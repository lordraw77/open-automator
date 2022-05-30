import oacommon
import time
import inspect
import json
gdict={}

myself = lambda: inspect.stack()[1][3]

def setgdict(self,gdict):
     self.gdict=gdict
     
@oacommon.trace    
def setsleep(self,param):
    """
    - name: "sleep"
      oa-utility.setsleep:
            seconds: 6
         
    """  
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('seconds',),param):
        seconds=gdict['seconds']
        time.sleep(seconds)
        oacommon.logend(myself())
    else:
        exit()


@oacommon.trace
def printvar(self,param):
    """ 
      - name: printvar
        oa-utility.printvar:
            varname: aaa
    """         
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('varname',),param):
        varname=gdict['varname']
        print (gdict[varname])
        oacommon.logend(myself())
    else:
        exit()
        



@oacommon.trace
def setvar(self,param):
    """ 
      - name: set variable
        oa-utility.setvar:
            varname: zzz
            varvalue: pluto
    """        
    oacommon.logstart(myself()) 
    if oacommon.checkandloadparam(self,myself(),('varname','varvalue'),param):
        varname=gdict['varname']
        varvalue=gdict['varvalue']
        gdict[varname] = varvalue
        oacommon.logend(myself())
    else:
        exit()
@oacommon.trace
def dumpvar(self,param):
    """ 
      - name: dump  variable
        oa-utility.dumpvar:
            savetofile: ./onlinevar.json #optional
    """    
    if oacommon._checkparam('savetofile',param):
        savetofile=param['savetofile']
        oacommon.writefile(savetofile,json.dumps(self.gdict, indent=4, sort_keys=True))
    print(json.dumps(self.gdict, indent=4, sort_keys=True))
    
     
     