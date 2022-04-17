import requests
import oacommon
import inspect
import http.client
gdict={}

def setgdict(self,gdict):
     self.gdict=gdict

myself = lambda: inspect.stack()[1][3]
     


@oacommon.trace
def httpget(self,param):
    """
    - name: make http get 
      oa-network.httpget: 
        host: 10.70.1.15
        port: 9999
        get:/zSirtaAnagraficaList
        printout: True #optional default false 
        saveonvar: outputvar #optional save output in var
        
    """  
    oacommon.logstart(myself())

    if oacommon.checkandloadparam(self,myself(),('host','port','get'),param):
        try:
            host = gdict['host']
            port=  gdict['port']
            get=  gdict['get']
            connection = http.client.HTTPConnection(host,port)
            connection.request("GET", get)
            response = connection.getresponse()
            print(f"Status: {response.status} and reason: {response.reason}")
            output= response.read().decode()
            if oacommon._checkparam('printout',param):
                printout=param['printout']
                if printout:
                    print(output)
            if oacommon._checkparam('saveonvar',param):
                saveonvar=param['saveonvar']
                gdict[saveonvar]=output

            connection.close()
        except Exception as e:
            print(e)
        oacommon.logend(myself())
    else:
        exit()
        
@oacommon.trace
def httpsget(self,param):
    """
    - name: make http get 
      oa-network.httpsget: 
        host: w3vcs05.emslabw3.local
        port: 443
        get:/
        verify: True #optional default false
        printout: True #optional default false 
        saveonvar: outputvar #optional save output in var
        
    """  
    oacommon.logstart(myself())

    if oacommon.checkandloadparam(self,myself(),('host','port','get'),param):
        try:
            host = gdict['host']
            port=  gdict['port']
            get=  gdict['get']
            verify=False
            if oacommon._checkparam('verify',param):
                verify=param['verify']
            response = requests.get(f'https://{host}:{port}{get}', verify = verify)
            print(f"Status: {response.status_code} and reason: {response.reason}")
            output= response.content
            if oacommon._checkparam('printout',param):
                printout=param['printout']
                if printout:
                    print(output)
            if oacommon._checkparam('saveonvar',param):
                saveonvar=param['saveonvar']
                gdict[saveonvar]=output

            
        except Exception as e:
            print(e)
        oacommon.logend(myself())
    else:
        exit()


