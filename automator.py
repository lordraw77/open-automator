# This is a sample Python script.
import yaml
import argparse
import os
import zipfile
import inspect
import paramiko
from scp import SCPClient

myself = lambda: inspect.stack()[1][3]
findinlist = lambda y,_list:  [x for x in _list if y in x]
TRACE=True


def trace(f):
    def wrap(*args, **kwargs):
        if TRACE:
            print(f"[TRACE] func: {f.__name__}, args: {args}, kwargs: {kwargs}")
        return f(*args, **kwargs)
    return wrap


@trace
def _checkparam(paramname, param):
    return lambda x: True if paramname in param else False

@trace
def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

@trace
def checkandloadparam(modulename,paramneed,param ):
    ret=True
    for par in paramneed:
        if par in param:
            globals()[par]= param.get(par)
        else:
            print(f'the param need for {modulename} are {paramneed}')
            ret=False
            break
    return ret
    
def _zipdir(paths,zipfilter, ziph):
    for path in paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if "*" in zipfilter or zipfilter in file:
                    ziph.write(os.path.join(root, file), 
                            os.path.relpath(os.path.join(root, file), 
                                            os.path.join(path, '..')))
    ziph.close()

@trace
def readfile(param):
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=globals()['filename']
        f = open(filename,"r")
        globals()[varname] =f.read()
        f.close()
    else:
        exit()

    """_summary_
        copy file or folder from local to remote server via scp
      - name: scp to remote  
        scpto:
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
        localpath: /opt/a.zip
        remontepath: /root/pippo.zip
        recursive: False
    """
def scpto(param):
    if checkandloadparam(myself(),('remoteserver','remoteuser','remotepassword','localpath','remontepath','recursive'),param):
        remoteserver=globals()['remoteserver']
        remoteuser=globals()['remoteuser']
        remotepassword=globals()['remotepassword'] 
        localpath=globals()['localpath'] 
        remontepath=globals()['remontepath'] 
        recursive=globals()['recursive'] 
 
        
    else:
        exit()
        

@trace
def writefile(param):
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=globals()['filename']
        f = open(filename,"w")
        f.write(globals()[varname])
        f.close()
    else:
        exit()
        
@trace
def printtext(param):
    if checkandloadparam(myself(),('varname',),param):
        varname=globals()['varname']
        print (globals()[varname])
    else:
        exit()
@trace        
def makezip(param):
    if checkandloadparam(myself(),('zipfilename','pathtozip','zipfilter'),param):    
        zipfilename=globals()['zipfilename']
        pathtozip=globals()['pathtozip']
        zipfilter=globals()['zipfilter']
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            _zipdir(pathtozip,zipfilter, zipf)
    else:
        exit()

@trace        
def unzip(param):
    if checkandloadparam(myself(),('zipfilename','pathwhereunzip'),param):    
        zipfilename=globals()['zipfilename']
        pathwhereunzip=globals()['pathwhereunzip']
        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            zipf.extractall(pathwhereunzip)

    else:
        exit()


@trace
def replace(param):
    if checkandloadparam(myself(),('varname','leftvalue','rightvalue'),param):
        varname=globals()['varname']
        leftvalue=globals()['leftvalue']
        rightvalue=globals()['rightvalue']
        temp= globals()[varname]
        temp = str(temp).replace(leftvalue,rightvalue)
        globals()[varname]= temp
    else:
        exit()

def main():
    # my_parser = argparse.ArgumentParser(description='exec automator tasks',allow_abbrev=True)
    # my_parser.add_argument('tasks',
    #                     metavar='tasks',
    #                     type=str,
    #                     help='yaml for task description')
    # args = my_parser.parse_args()
    # tasksfile =args.tasks
    
    tasksfile = "automator.yaml"
    with open(tasksfile) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    
    print(conf)
    tasks = conf[0]['tasks']
    for task in tasks:
        for key in task.keys():
            if "name" not in key:
                print(f"\t{key} {task.get(key)}")
                func = globals()[key]
                func(task.get(key))
            else:
                print(f"task:.....{task.get(key)}")

        #print(task)



if __name__ == '__main__':
    main()

