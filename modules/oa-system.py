import oacommon
import inspect
from scp import SCPClient
import os
import zipfile
import shutil
gdict={}

myself = lambda: inspect.stack()[1][3]


def setgdict(self,gdict):
     self.gdict=gdict
     



@oacommon.trace
def systemd(self,param):
    
    """
        manage systemctl
      - name: systemd
        oa-system.systemd:
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
        servicename: ntp
        servicestate: stop 
    """
    oacommon.logstart(myself())

    if oacommon.checkandloadparam(self,myself(),('remoteserver','remoteuser','remotepassword','remoteport','servicename','servicestate'),param):
        remoteserver=gdict['remoteserver']
        remoteuser=gdict['remoteuser']
        remotepassword=gdict['remotepassword'] 
        remoteport=gdict['remoteport'] 
        servicename=gdict['servicename'] 
        servicestate=gdict['servicestate'] 
        
        command=f"systemctl {servicestate} {servicename}"
        output = oacommon._sshremotecommand(remoteserver,remoteport,remoteuser,remotepassword,command)
        print(output)
        oacommon.logend(myself())

    else:
        exit()
        

@oacommon.trace
def remotecommand(self,param):

    """
        execute remote command over ssh
      - name: execute remote command over ssh 
        oa-system.remotecommand:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "password.123"
            command: ls -al /root
            saveonvar: outputvar #optional save output in var
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('remoteserver','remoteuser','remotepassword','remoteport','command'),param):
        remoteserver=gdict['remoteserver']
        remoteuser=gdict['remoteuser']
        remotepassword=gdict['remotepassword'] 
        remoteport=gdict['remoteport'] 
        command=gdict['command']
        output= oacommon._sshremotecommand(remoteserver, remoteport, remoteuser, remotepassword,command)
        if oacommon._checkparam('saveonvar',param):
            saveonvar=param['saveonvar']
            gdict[saveonvar]=output
        
        print(output)
        oacommon.logend(myself())
    else:
        exit()



@oacommon.trace
def scp(self,param):

    """
        copy file or folder from local to remote server via scp
      - name: scp to remote  
        oa-system.scp:
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
        localpath: /opt/a.zip
        localpath: 
            - /opt/a.zip
        remotepath: /root/pippo.zip
        remotepath:
            - /root/pippo.zip
        recursive: False
        direction: localtoremote
    """
    oacommon.logstart(myself())

    if oacommon.checkandloadparam(self,myself(),('remoteserver','remoteuser','remotepassword','remoteport','localpath','remotepath','recursive','direction'),param):
        remoteserver=gdict['remoteserver']
        remoteuser=gdict['remoteuser']
        remotepassword=gdict['remotepassword'] 
        remoteport=gdict['remoteport'] 
        if isinstance(gdict['localpath'],list):
            localpath=list(gdict['localpath'])
        else:
            localpath=oacommon.effify(gdict['localpath'])
        if isinstance(gdict['remotepath'],list):
            remotepath=list(gdict['remotepath'])
        else:
            remotepath=oacommon.effify(gdict['remotepath'])
        recursive=gdict['recursive'] 
        direction=gdict['direction']
        ismultipath=False
        lres =""
        if isinstance(localpath,list) and isinstance(remotepath,list):
            if len(localpath) == len(remotepath):
                res = ','.join('%s=%s' % i for i in zip(localpath, remotepath))
                lres = list(res.split(','))
                print("is multipath")
                print(lres)
                ismultipath=True
            else:
                print("ERROR: if using multiple path, set seme size for {local|remote}path bye.")
                exit()
        elif  isinstance(localpath,list) or isinstance(remotepath,list):
            print("ERROR: if set local or remote path as multiple, set all path are multiple bye.")
            exit()
        else:
            ismultipath=False
            
            
        ssh=  oacommon.createSSHClient(remoteserver, remoteport, remoteuser, remotepassword)  
        _scp= SCPClient(ssh.get_transport())  
        if "localtoremote" in direction:
            if ismultipath:
                for res in lres:
                    localpath = oacommon.effify(res.split('=')[0])
                    remotepath = oacommon.effify(res.split('=')[1])
                    _scp.put(localpath, recursive=recursive, remote_path=remotepath)
            else:
                _scp.put(localpath, recursive=recursive,remote_path=remotepath)
        elif "remotetolocal":
            if ismultipath:
                 for res in lres:
                    localpath = oacommon.effify(res.split('=')[0])
                    remotepath = oacommon.effify(res.split('=')[1])
                    _scp.get(remote_path=remotepath, local_path=localpath, recursive=recursive)
            else:
                _scp.get(remote_path=remotepath,local_path=localpath, recursive=recursive)
        
        _scp.close()
        ssh.close()
        oacommon.logend(myself())

    else:
        exit()
        
@oacommon.trace        
def remoteunzip(self,param):
    """ 
    - name: remoteunzip
        oa-system.remoteunzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "password.123"
    """    
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('zipfilename','pathwhereunzip','remoteserver','remoteuser','remotepassword','remoteport'),param):
        remoteserver=gdict['remoteserver']
        remoteuser=gdict['remoteuser']
        remotepassword=gdict['remotepassword'] 
        remoteport=gdict['remoteport']             
        zipfilename=oacommon.effify(gdict['zipfilename'])
        pathwhereunzip=oacommon.effify(gdict['pathwhereunzip'])
        tmpfolder = os.curdir + os.path.sep + "tmp" + os.path.sep
        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            zipf.extractall(tmpfolder)
        
        ssh=  oacommon.createSSHClient(remoteserver, remoteport, remoteuser, remotepassword)  
        _scp= SCPClient(ssh.get_transport())  
        _scp.put(tmpfolder, recursive=True,remote_path=pathwhereunzip)
        _scp.close()
        ssh.close()
        if os.path.exists(tmpfolder):
            try:
                shutil.rmtree(tmpfolder)
            except OSError as e:
                print(f"Error: {tmpfolder} : {e.strerror}")  
                
        oacommon.logend(myself())

    else:
        exit()
