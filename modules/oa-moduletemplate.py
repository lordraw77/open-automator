from responses import logger
import oacommon
import inspect
### TEMPLATE FOR MAKE CUSTOM MODULES

### FIXED FUNCTION AND VARIABLE
### global dict for sync variable between modules 
gdict={}
### set global dict in module like class module
def setgdict(self,gdict):
     self.gdict=gdict
### retrive module name
myself = lambda: inspect.stack()[1][3]



#### TEMPLATE FOR FUNCTION

### trace annotation
@oacommon.trace
### the parameter fixed self module and param dict read from yaml config
def templatefunction(self,param):
    #TEMPLATE DOCUMENTATION FOR TASK YAML
    """
    - name: name and description
      oa-moduletemplate.templatefunction:
        param1: valueparam1
        param2: valueparam2{zzz} 
        param3: val3 #optional parameter
        

    """
    ### log start task don't change 
    oacommon.logstart(myself())
    ### check and load needded parameter 
    task_id = param.get("task_id")  # obbligatorio se usi multi-thread
    task_store = param.get("task_store")  # istanza di TaskResultStore

    if oacommon.checkandloadparam(self,myself(),('param1','param1'),param):
        param1=gdict['param1']
        param2=oacommon.effify(gdict['param2'])
        param3=False
        #optional parameter check is present
        if oacommon._checkparam('param3',param):
            param3=gdict['param3']
        #place your code for make do 
        
        #log end task execution    
        oacommon.logend(myself())
        try:
        # codice del task...
            pass
        except Exception as e:
            task_success = False
            error_msg = str(e)
            logger.error(f"Task {myself} failed: {e}", exc_info=True)

        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

        oacommon.logend(myself)
        return task_success
        
    else:
        exit()
        