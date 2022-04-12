import yaml
import shutil
import json
import argparse
import os
import zipfile
import inspect
import paramiko
from jinja2 import Environment, BaseLoader
from scp import SCPClient
import re
import pprint
import glob
import sys
import http.client
import requests


if os.path.exists("modules"):
    sys.path.append("modules")

myself = lambda: inspect.stack()[1][3]
findinlist = lambda y,_list:  [x for x in _list if y in x]
__TRACE__=False
__DEBUG__=False

def effify(non_f_str: str):
    return eval(f'f"""{non_f_str}"""')

def trace(f):
    def wrap(*args, **kwargs):
        if __TRACE__:
            print(f"[TRACE] func: {f.__name__}, args: {args}, kwargs: {kwargs}")
        return f(*args, **kwargs)
    return wrap


@trace
def _checkparam(paramname, param):
    ret=False
    if paramname in param:
        ret=True
    return ret
    
    #rrturn lambda x: True if paramname in param else False

@trace
def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def _sshremotecommand(server, port, user, password,commandtoexecute):
    ssh =  createSSHClient(server, port, user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(commandtoexecute)
    ssh_stdin.flush()
    output = ssh_stdout.read()
    return output


@trace
def checkandloadparam(modulename,paramneed,param ):
    if __DEBUG__:
        print(modulename)
        pprint.pprint(param)
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
        path = effify(path)
        for root, dirs, files in os.walk(path):
            for file in files:
                if "*" in zipfilter or zipfilter in file:
                    ziph.write(os.path.join(root, file), 
                            os.path.relpath(os.path.join(root, file), 
                                            os.path.join(path, '..')))
    ziph.close()


@trace
def rename(param):
    """
    - name: renamefile file or directory
        rename:
            srcpath: /opt/exportremote
            dstpath: /opt/export{zzz} 
        

    """
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('srcpath','dstpath'),param):
        srcpath=effify(globals()['srcpath'])
        dstpath=effify(globals()['dstpath'])
        os.rename(srcpath,dstpath)
        print(f"{myself():.<30}.....end")
    else:
        exit()
        

@trace
def template(param):
    """
    - name:  render j2 template 
        templete:
            templatefile: ./info.j2
            dstfile: /opt/info{zzz}.txt 
            
    """
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('templatefile','dstfile'),param):
        templatefile=effify(globals()['templatefile'])
        dstfile=effify(globals()['dstfile'])
        f = open(templatefile,'r')
        data= f.read()
        f.close()
        rtemplate = Environment(loader=BaseLoader).from_string(data)
        output = rtemplate.render(**globals())
        f = open(dstfile,'w')
        f.write(output)
        f.close()
        print(f"{myself():.<30}.....end")
    else:
        exit()
        
@trace
def copy(param):
    """
    - name: copy file or directory
        copy:
            srcpath: /opt/exportremote
            dstpath: /opt/export{zzz} 
            recursive: True

    """
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('srcpath','dstpath','recursive'),param):
        srcpath=effify(globals()['srcpath'])
        dstpath=effify(globals()['dstpath'])
        recursive=globals()['recursive']
        if recursive:
            shutil.copytree(srcpath,dstpath,dirs_exist_ok=True)
        else:
            shutil.copy(srcpath,dstpath)
        
        print(f"{myself():.<30}.....end")
    else:
        exit()
        
@trace
def remove(param):
    """
    - name: remove file or directory
        remove:
            pathtoremove: /opt/exportremote 
            recursive: True
        NOTE: IF PATH TERMINATE WITH WILDCARD REMOVE FILE IN PATH

    """
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('pathtoremove','recursive'),param):
        pathtoremove=effify(globals()['pathtoremove'])
        recursive=globals()['recursive']
        if recursive:
            try:
                shutil.rmtree(pathtoremove)
            except OSError as e:
                print(f"Error: {pathtoremove} : {e.strerror}")
        else:
            if "*" in pathtoremove:
                files = glob.glob(pathtoremove)
                for f in files:
                    os.remove(f)
            else:    
                if os.path.exists(pathtoremove):
                    os.remove(pathtoremove)
        
        print(f"{myself():.<30}.....end")
    else:
        exit()

@trace
def readfile(param):
    """
      - name: readfile
        readfile:
            filename: /opt/a.t
            varname: aaa
    """
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=effify(globals()['filename'])
        f = open(filename,"r")
        globals()[varname] =f.read()
        f.close()
        print(f"{myself():.<30}.....end")

    else:
        exit()
@trace 
def systemd(param):
    
    """
        manage systemctl
      - name: scp to remote  
        systemd:
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
        servicename: ntp
        servicestate: stop 
    """
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('remoteserver','remoteuser','remotepassword','remoteport','servicename','servicestate'),param):
        remoteserver=globals()['remoteserver']
        remoteuser=globals()['remoteuser']
        remotepassword=globals()['remotepassword'] 
        remoteport=globals()['remoteport'] 
        servicename=globals()['servicename'] 
        servicestate=globals()['servicestate'] 
        
        command=f"systemctl {servicestate} {servicename}"
        output = _sshremotecommand(remoteserver,remoteport,remoteuser,remotepassword,command)
        print(output)
        print(f"{myself():.<30}.....end")

    else:
        exit()
        

@trace
def remotecommand(param):

    """
        execute remote command over ssh
      - name: execute remote command over ssh 
        remotecommand:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "password.123"
            command: ls -al /root
            saveonvar: outputvar #optional save output in var
    """
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('remoteserver','remoteuser','remotepassword','remoteport','command'),param):
        remoteserver=globals()['remoteserver']
        remoteuser=globals()['remoteuser']
        remotepassword=globals()['remotepassword'] 
        remoteport=globals()['remoteport'] 
        command=globals()['command']
        output= _sshremotecommand(remoteserver, remoteport, remoteuser, remotepassword,command)
        if _checkparam('saveonvar',param):
            saveonvar=param['saveonvar']
            globals()[saveonvar]=output
        
        print(output)
        print(f"{myself():.<30}.....end")
    else:
        exit()

@trace
def scp(param):

    """
        copy file or folder from local to remote server via scp
      - name: scp to remote  
        scp:
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
        localpath: /opt/a.zip
        remotepath: /root/pippo.zip
        recursive: False
        direction: localtoremote
    """
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('remoteserver','remoteuser','remotepassword','remoteport','localpath','remotepath','recursive','direction'),param):
        remoteserver=globals()['remoteserver']
        remoteuser=globals()['remoteuser']
        remotepassword=globals()['remotepassword'] 
        remoteport=globals()['remoteport'] 
        localpath=effify(globals()['localpath'])
        remotepath=effify(globals()['remotepath']) 
        recursive=globals()['recursive'] 
        direction=globals()['direction']
        ssh=  createSSHClient(remoteserver, remoteport, remoteuser, remotepassword)  
        _scp= SCPClient(ssh.get_transport())  
        if "localtoremote" in direction:
            if recursive:
                _scp.put(localpath, recursive=True, remote_path=remotepath)
            else:
                _scp.put(localpath,remotepath)
        elif "remotetolocal":
            if recursive:
                _scp.get(remote_path=remotepath, local_path=localpath, recursive=True)
            else:
                _scp.get(remote_path=remotepath,local_path=localpath)
        
        _scp.close()
        ssh.close()
        print(f"{myself():.<30}.....end")

    else:
        exit()
        

@trace
def writefile(param):
    """
      - name: write file
        writefile:
            filename: /opt/a.t2
            varname: aaa
    """  
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=effify(globals()['filename'])
        f = open(filename,"w")
        f.write(globals()[varname])
        f.close()
        print(f"{myself():.<30}.....end")

    else:
        exit()
@trace
def loadvarfromjeson(param):
    
    """ 
        load variable form json
      - name: load variable form json
        loadvarfromjeson:
            filename: /opt/uoc-generator/jtable
             
    """         
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('filename', ),param):
        
        filename=effify(globals()['filename'])
        with open(filename,'r') as f:
            data = f.read()
            jdata = json.loads(data)
            for d in jdata.keys():
                globals()[d]=jdata.get(d)
        print(f"{myself():.<30}.....end")
    else:
        exit()
     
@trace
def setvar(param):
    """ 
      - name: set variable
        setvar:
            varname: zzz
            varvalue: pluto
    """        
    print(f"{myself():.<30}.....start") 
    if checkandloadparam(myself(),('varname','varvalue'),param):
        varname=globals()['varname']
        varvalue=globals()['varvalue']
        globals()[varname] = varvalue
        print(f"{myself():.<30}.....end")
    else:
        exit()
     
     
@trace
def printtext(param):
    """ 
      - name: printtext
        printtext:
            varname: aaa
    """         
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('varname',),param):
        varname=globals()['varname']
        print (globals()[varname])
        print(f"{myself():.<30}.....end")
    else:
        exit()
     
@trace        
def makezip(param):
    """
    - name: make zip
        makezip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"
    """    
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('zipfilename','pathtozip','zipfilter'),param):    
        zipfilename=effify(globals()['zipfilename'])
        pathtozip=globals()['pathtozip']
        zipfilter=globals()['zipfilter']
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            _zipdir(pathtozip,zipfilter, zipf)
        print(f"{myself():.<30}.....end")
    else:
        exit()

@trace        
def unzip(param):
    """ 
    - name: unzip
        unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/
    """    
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('zipfilename','pathwhereunzip'),param):    
        zipfilename=effify(globals()['zipfilename'])
        pathwhereunzip=effify(globals()['pathwhereunzip'])
        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            zipf.extractall(pathwhereunzip)
        print(f"{myself():.<30}.....end")

    else:
        exit()

@trace
def httpget(param):
    """
    - name: make http get 
      httpget: 
        host: 10.70.7.7
        port: 9999
        get:/
        printout: True #optional default false 
        saveonvar: outputvar #optional save output in var
        
    """  
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('host','port','get'),param):
        try:
            host = globals()['host']
            port=  globals()['port']
            get=  globals()['get']
            connection = http.client.HTTPConnection(host,port)
            connection.request("GET", get)
            response = connection.getresponse()
            print(f"Status: {response.status} and reason: {response.reason}")
            output= response.read().decode()
            if _checkparam('printout',param):
                printout=param['printout']
                if printout:
                    print(output)
            if _checkparam('saveonvar',param):
                saveonvar=param['saveonvar']
                globals()[saveonvar]=output

            connection.close()
        except Exception as e:
            print(e)
        print(f"{myself():.<30}.....end")
    else:
        exit()
        
trace
def httpsget(param):
    """
    - name: make http get 
      httpsget: 
        host: https://www.ssllabs.com/ssltest/
        port: 443
        get:/
        verify: True #optional default false
        printout: True #optional default false 
        saveonvar: outputvar #optional save output in var
        
    """  
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('host','port','get'),param):
        try:
            host = globals()['host']
            port=  globals()['port']
            get=  globals()['get']
            verify=False
            if _checkparam('verify',param):
                verify=param['verify']
            response = requests.get(f'https://{host}:{port}{get}', verify = verify) 
            print(f"Status: {response.status_code} and reason: {response.reason}")
            output= response.content
            if _checkparam('printout',param):
                printout=param['printout']
                if printout:
                    print(output)
            if _checkparam('saveonvar',param):
                saveonvar=param['saveonvar']
                globals()[saveonvar]=output

            
        except Exception as e:
            print(e)
        print(f"{myself():.<30}.....end")
    else:
        exit()

@trace
def regexreplaceinfile(param):
    """
    - name: "replace with regex in file 
      regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t
    """  
    print(f"{myself():.<30}.....start")

    if checkandloadparam(myself(),('filein','regexmatch','regexvalue','fileout'),param):
        filein=effify(globals()['filein'])
        regexmatch=globals()['regexmatch']
        regexvalue=globals()['regexvalue']
        fileout=effify(globals()['fileout'])
        with open (filein, 'r' ) as f:
            content = f.read()
            content_new = re.sub(regexmatch, regexvalue, content, flags = re.M)
            with open( fileout,'w')as fo:
                fo.write(content_new)
        print(f"{myself():.<30}.....end")
    else:
        exit()


@trace
def replace(param):
    """
    - name: "replace test con \"test \""
        replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "
    """  
    print(f"{myself():.<30}.....start")
    if checkandloadparam(myself(),('varname','leftvalue','rightvalue'),param):
        varname=globals()['varname']
        leftvalue=globals()['leftvalue']
        rightvalue=globals()['rightvalue']
        temp= globals()[varname]
        temp = str(temp).replace(leftvalue,rightvalue)
        globals()[varname]= temp
        print(f"{myself():.<30}.....end")
    else:
        exit()

def main():
    my_parser = argparse.ArgumentParser(description='exec open-automator tasks',allow_abbrev=True)
    my_parser.add_argument('tasks',metavar='tasks',type=str,help='yaml for task description')
    my_parser.add_argument('-d', action='store_true',help='debug enable')
    my_parser.add_argument('-t', action='store_true',help='trace enable')
    args = my_parser.parse_args()
    tasksfile =args.tasks
    __DEBUG__=args.d
    __TRACE__=args.t

 
    #tasksfile = "automator.yaml"
    print(f"start process tasks form {tasksfile}")
    with open(tasksfile) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    
    #print(conf)
    pprint.pprint(conf)
    tasks = conf[0]['tasks']
    sizetask = len(tasks)
    currtask = 1 
    for task in tasks:
        for key in task.keys():
            if "name" != key:
                print("\n")
                print(f"exec task {currtask} of {sizetask}")
                if __DEBUG__:
                    print(f"\t{key} {task.get(key)}") 
                if "." in key:
                    module = __import__(key.split('.')[0])
                    func = getattr(module, key.split('.')[1])
                    func(task.get(key))
                else:
                    func = globals()[key]
                    func(task.get(key))
                currtask = currtask +1 
            else:
                print(f"task:..............................{task.get(key)}")

        #print(task)



if __name__ == '__main__':
    main()

