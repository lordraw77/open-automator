from glob import glob
import yaml
import shutil
import argparse
import os
import zipfile
import inspect
import paramiko
from scp import SCPClient
import re

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
    return lambda x: True if paramname in param else False

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
def rename(param):
    """_summary_
    - name: renamefile file or directory
        rename:
            srcpath: /opt/exportremote
            dstpath: /opt/export{zzz} 
        

    """
    if checkandloadparam(myself(),('srcpath','dstpath'),param):
        srcpath=effify(globals()['srcpath'])
        dstpath=effify(globals()['dstpath'])
        os.rename(srcpath,dstpath)
    else:
        exit()
        

@trace
def copy(param):
    """_summary_
    - name: copy file or directory
        copy:
            srcpath: /opt/exportremote
            dstpath: /opt/export{zzz} 
            recursive: True

    """
    if checkandloadparam(myself(),('srcpath','dstpath','recursive'),param):
        srcpath=globals()['srcpath']
        dstpath=globals()['dstpath']
        recursive=globals()['recursive']
        dstpath = effify(dstpath) 
        srcpath = effify(srcpath)
        if recursive:
            shutil.copytree(srcpath,dstpath,dirs_exist_ok=True)
        else:
            shutil.copy(srcpath,dstpath)
    else:
        exit()
        
@trace
def remove(param):
    """_summary_
    - name: remove file or directory
        remove:
            pathtoremove: /opt/exportremote 
            recursive: True

    """
    if checkandloadparam(myself(),('pathtoremove','recursive'),param):
        pathtoremove=globals()['pathtoremove']
        recursive=globals()['recursive']
        if recursive:
            try:
                shutil.rmtree(pathtoremove)
            except OSError as e:
                print(f"Error: {pathtoremove} : {e.strerror}")
        else:
            if os.path.exists(pathtoremove):
                os.remove(pathtoremove)
    else:
        exit()

@trace
def readfile(param):
    """_summary_
      - name: readfile
        readfile:
            filename: /opt/a.t
            varname: aaa
    """
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=globals()['filename']
        f = open(filename,"r")
        globals()[varname] =f.read()
        f.close()
    else:
        exit()
@trace 
def systemd(param):
    
    """_summary_
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
    else:
        exit()
        


@trace
def scp(param):

    """_summary_
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
    if checkandloadparam(myself(),('remoteserver','remoteuser','remotepassword','remoteport','localpath','remotepath','recursive','direction'),param):
        remoteserver=globals()['remoteserver']
        remoteuser=globals()['remoteuser']
        remotepassword=globals()['remotepassword'] 
        remoteport=globals()['remoteport'] 
        localpath=globals()['localpath'] 
        remotepath=globals()['remotepath'] 
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
     
    else:
        exit()
        

@trace
def writefile(param):
    """_summary_
      - name: write file
        writefile:
            filename: /opt/a.t2
            varname: aaa
    """  
    if checkandloadparam(myself(),('varname','filename'),param):
        varname=globals()['varname']
        filename=globals()['filename']
        f = open(filename,"w")
        f.write(globals()[varname])
        f.close()
    else:
        exit()
        
@trace
def setvar(param):
    """_summary_
      - name: set variable
        setvar:
            varname: zzz
            varvalue: pluto
    """         
    if checkandloadparam(myself(),('varname','varvalue'),param):
        varname=globals()['varname']
        varvalue=globals()['varvalue']
        globals()[varname] = varvalue
    else:
        exit()
     
     
@trace
def printtext(param):
    """_summary_
      - name: printtext
        printtext:
            varname: aaa
    """         
    if checkandloadparam(myself(),('varname',),param):
        varname=globals()['varname']
        print (globals()[varname])
    else:
        exit()
     
@trace        
def makezip(param):
    """_summary_
    - name: make zip
        makezip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"
    """    
    if checkandloadparam(myself(),('zipfilename','pathtozip','zipfilter'),param):    
        zipfilename=globals()['zipfilename']
        pathtozip=globals()['pathtozip']
        zipfilter=globals()['zipfilter']
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            _zipdir(pathtozip,zipfilter, zipf)
            makezip
    else:
        exit()

@trace        
def unzip(param):
    """_summary_
    - name: unzip
        unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/
    """    
    if checkandloadparam(myself(),('zipfilename','pathwhereunzip'),param):    
        zipfilename=globals()['zipfilename']
        pathwhereunzip=globals()['pathwhereunzip']
        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            zipf.extractall(pathwhereunzip)

    else:
        exit()

@trace
def regexreplaceinfile(param):
    """_summary_
    - name: "replace with regex in file 
      regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t
    """  
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
         
    else:
        exit()


@trace
def replace(param):
    """_summary_
    - name: "replace test con \"test \""
        replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "
    """  
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
    aaa = "start process tasks form {tasksfile}"
    globals()['tasksfile']=tasksfile
    print(effify(aaa))
    with open(tasksfile) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    
    print(conf)
    tasks = conf[0]['tasks']
    for task in tasks:
        for key in task.keys():
            if "name" != key:
                if __DEBUG__:
                    print(f"\t{key} {task.get(key)}") 
                func = globals()[key]
                func(task.get(key))
            else:
                print(f"task:.....{task.get(key)}")

        #print(task)



if __name__ == '__main__':
    main()

