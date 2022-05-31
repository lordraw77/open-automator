import pprint
import inspect
import chardet    

import paramiko

gdict={}

def trace(f):
    def wrap(*args, **kwargs):
        if gdict['__TRACE__']:
            print(f"[TRACE] func: {f.__name__}, args: {args}, kwargs: {kwargs}")
        return f(*args, **kwargs)
    return wrap

myself = lambda: inspect.stack()[1][3]

def effify(non_f_str: str):
    globals().update(gdict)
    return eval(f'f"""{non_f_str}"""')

def setgdict(self,gdict :dict):
    self.gdict = gdict
    
def checkandloadparam(self,modulename,paramneed,param ):
    if self.gdict['__DEBUG__']:
        print(modulename)
        pprint.pprint(param)
    ret=True
    for par in paramneed:
        if par in param:
            self.gdict[par]= param.get(par)
        else:
            print(f'the param {par} need for {modulename}, nedded parameter are {paramneed}')
            ret=False
            break
    return ret


logstart= lambda x: print(f"{x:.<30}.....start")
logend  = lambda x: print(f"{x:.<30}.....end") 

@trace
def _checkparam(paramname, param):
    ret=False
    if paramname in param:
        ret=True
    return ret

@trace
def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, int(port), user, password)
    return client

def _sshremotecommand(server, port, user, password,commandtoexecute):
    ssh =  createSSHClient(server, port, user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(commandtoexecute)
    ssh_stdin.flush()
    output = ssh_stdout.read()
    return output

def _findenc(filename):
    rawdata = open(filename,'rb').read()
    result = chardet.detect(rawdata)
    return result['encoding']

@trace
def writefile(filename,data):
    f = open(filename,"w")
    f.write(data)
    f.close()
    
@trace
def readfile(filename):
    f = open(filename,mode="r",encoding=_findenc(filename=filename))
    data = f.read()
    f.close()
    return data

@trace
def appendfile(filename,data):
    f = open(filename,"a")
    f.write(data)
    f.close()
    