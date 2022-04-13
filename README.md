# open-automator
***beta version***

Open Automator is a python project, for the automation of development support scripts, 
similar in concept to ansilbe, but seen from the development side.

**All YAML parameters are required.**

python required are ***python 3.10.4+***

#### python module:
- Jinja2
- MarkupSafe
- protobuf
- PyYAML
- six
- xmltodict
- zipfile36
- paramiko
- scp
- requests


 ```console
/usr/local/bin/python3.10 /opt/open-automator/automator.py -h
usage: automator.py [-h] [-d] [-t] tasks

exec open-automator tasks

positional arguments:
  tasks       yaml for task description

options:
  -h, --help  show this help message and exit
  -d          debug enable
  -t          trace enable
 ```

## module available

- setvar
- rename
- copy
- readfile
- remove
- systemclt
- scp
- writefile
- printtext
- makezip
- unzip
- regexreplaceinfile
- replace
- remotecommand
- loadvarfromjeson
- template
- httpget
- httpsget

# setvar:  

### This module is for set a varible during execution of automator 

| Parameter Name   |  Parameter Description      |      
|-------------|:----------: 
| varname |  variable name  |
| varvalue |  value to set in variable | 
 
Config exemple:
``` yaml
   - name setvar #set pluto in zzz var 
     setvar:
       varname: zzz
       varvalue: pluto

``` 
# rename: 

### This module is for rename one file or one directory in local in local
#### In path variable can use F-string sintax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| srcpath |  file or directory source  |
| dstpath |  file or directory destination | 

Config exemple:
``` yaml
    - name: renamefile file or directory
      rename:
          srcpath: /opt/exportremote
          dstpath: /opt/export{zzz} 

``` 
# copy:  

### This moduleis for copy file or directory in local
#### In path variable can use F-string sintax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| srcpath |  file or directory source  |
| dstpath |  file or directory destination | 
| recursive |  True if is directory | 

Config exemple:
``` yaml
   - name: copy file or directory
     copy:
         srcpath: /opt/exportremote
         dstpath: /opt/export{zzz} 
         recursive: True

``` 
# readfile: 

### This module is for read file in a variable
#### In path variable can use F-string sintax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filename |  file name and path for file to load|
| varname |   var where store the file context | 
 
Config exemple:
``` yaml
   - name: readfile
     readfile:
         filename: /opt/a.t
         varname: aaa

``` 
# remove: 

### This module is for delete file or file with wildcard or directory in local 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| pathtoremove |  file name or path to remove  |
| recursive |     True if is directory | 

**NOTE: IF PATH TERMINATE WITH WILDCARD REMOVE FILE IN PATH**

**NOTE: WildCard option is enabled only with recursive false**

Config exemple:
``` yaml
    - name: remove file or directory
      remove:
          pathtoremove: /opt/exportremote 
          recursive: True

``` 
# systemclt

### This module is for manage systemctl on remote server

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| remoteserver |  ip or host name for remote server  |
| remoteuser |     user with greant for manage service | 
| remoteport |  ssh port number  |
| remotepassword |     user password | 
| servicename |  name of service to mange  |
| servicestate | the systemctl state | 

Config exemple:
``` yaml        
      - name: systemd  
        systemd:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "PaSsWoRd"
            servicename: ntp
            servicestate: stop 

``` 
### scp: copy file or folder from local to remote server via scp

## Note: if use multiple file config, the number of elements must be the same on local and remote path. 
``` yaml
    - name: scp to remote  
      scp:
          remoteserver: "10.70.7.7"
          remoteuser: "root"
          remoteport: 22
          remotepassword: "PaSsWoRd"
          localpath: /opt/a.zip #for single file
          localpath: #for multipe file
             - /opt/a.zip
             - /opt/b.zip
          remotepath: /root/pippo.zip #for single file
          remotepath:  #for multipe file
             - /root/pippo.zip
             - /root/pluto.zip
          recursive: False
          direction: localtoremote

``` 
### writefile: write file in local
``` yaml      
      - name: write file
        writefile:
            filename: /opt/a.t2
            varname: aaa

``` 
### printtext: print to console a variable
``` yaml
    - name: printtext
      printtext:
          varname: aaa

``` 
### makezip: make zip in local
``` yaml
   - name: make zip
     makezip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"

``` 
### unzip: unzip file in local
``` yaml
   - name: unzip
     unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/

``` 
### regexreplaceinfile:   
``` yaml 
    - name: "replace with regex in file 
      regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t

``` 
### replace: replace text in variable in memory
``` yaml
    - name: "replace test con \"test \""
      replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "

```         
       
### remotecommand:  execute remote command over ssh
``` yaml
    - name: execute remote command over ssh 
      remotecommand:
          remoteserver: "10.70.7.7"
          remoteuser: "root"
          remoteport: 22
          remotepassword: "PaSsWoRd"
          command: ls -al /root
          saveonvar: outputvar #optional save output in var the param are variablename

``` 
###  loadvarfromjeson: load variable form json
``` yaml
   - name: load variable form json
     loadvarfromjeson:
         filename: /opt/uoc-generator/jtable
```
### template: render j2 template  
``` yaml
    - name:  render j2 template 
      template:
        templatefile: ./info.j2
        dstfile: /opt/info{zzz}.txt 
```

### httpget: make an http get 
``` yaml
    - name: make http get 
      httpget: 
        host: "10.70.7.7"
        port: 9999
        get: "/"
        printout: True #optional default false 
        saveonvar: "outputvar" #optional save output in var
```

### httpsget: make an http get 

``` yaml
    - name: make https get 
      httpsget: 
        host: "10.70.7.7"
        port: 443
        get: "/"
        printout: True
        saveonvar: outputVarPPP 
        verify: False
```

### Yaml conifigurazion exemple:
``` yaml
# YAML
- name: 
  tasks:
  - name: make https get 
    httpsget: 
      host: "10.70.7.7"
      port: 443
      get: "/"
      printout: True
      saveonvar: outputVarPPP 
      verify: False
  - name: make http get 
    httpget: 
      host: "10.70.7.7"
      port: 9999
      get: "/"
      printout: True #optional default false 
      saveonvar: "outputvar" #optional save output in var
  - name: set variable
    setvar:
      varname: zzz
      varvalue: pluto
  - name: load variable form json
    loadvarfromjeson:
        filename: /opt/a.json
  - name: readfile
    readfile:
      filename: /opt/a.t
      varname: aaa
  - name: print variable
    printtext:
      varname: aaa
  - name: "replace test con \"test \""
    replace:
      varname: aaa
      leftvalue: "test"
      rightvalue: "test "
  - name: print variable
    printtext:
      varname: aaa
  - name: write file
    writefile:
      filename: /opt/a.t2
      varname: aaa
  - name: make zip
    makezip:
      zipfilename: /opt/a.zip
      pathtozip: 
        - /opt/export/
        - /opt/exportv2/
      zipfilter: "*"
  - name: unzip
    unzip:
      zipfilename: /opt/a.zip
      pathwhereunzip: /tmp/test/
  - name: scp to remote  
    scp:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      localpath: /opt/a.zip
      remotepath: /root/pippo.zip
      recursive: False
      direction: localtoremote
  - name: scp to remote folder
    scp:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      localpath: /opt/export
      remotepath: /root/export
      recursive: True
      direction: localtoremote
  - name: scp from remote  
    scp:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      localpath: /opt/aremote.zip
      remotepath: /root/pipporemote.zip
      recursive: False
      direction: remotetolocal
  - name: scp from remote folder
    scp:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      localpath: /opt/exportremote 
      remotepath: /root/exporttemote
      recursive: True
      direction: remotetolocal
  - name: copy file or directory
    copy:
      srcpath: /opt/exportremote
      dstpath: /opt/export{zzz} 
      recursive: True
  - name: copy file or directory
    copy:
      srcpath: /opt/aremote.zip
      dstpath: /opt/aremote{zzz}.zip 
      recursive: False
  - name: remove directory
    remove:
      pathtoremove: /opt/exportremote 
      recursive: True
  - name: remove file  
    remove:
      pathtoremove: /opt/aremote.zip 
      recursive: False
  - name: print variable
    printtext:
      varname: zzz
  - name: scp to remote  
    systemd:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      servicename: ntpd
      servicestate: stop 
  - name: scp to remote  
    systemd:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      servicename: ntpd
      servicestate: start
  - name: scp to remote  
    systemd:
      remoteserver: "10.70.7.7"
      remoteuser: "root"
      remoteport: 22
      remotepassword: "PaSsWoRd"
      servicename: ntpd
      servicestate: status 
  - name: replace with regex in file 
    regexreplaceinfile:
      filein: /opt/a.t
      regexmatch: test2
      regexvalue: pluto2
      fileout: /opt/az.t
  - name: renamefile file or directory
    rename:
      srcpath: /opt/az.t
      dstpath: /opt/az.t{zzz} 
  - name: execute remote command over ssh 
        remotecommand:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "PaSsWoRd"
            command: ls -al /root
  - name:  render j2 template 
      templete:
          templatefile: ./info.j2
          dstfile: /opt/info{zzz}.txt 
 ```
      
      
 ### Console output
 
 
 ```console
 /usr/local/bin/python3.10 /opt/open-automator/automator.py
start process tasks form automator.yaml
[{'name': None, 'tasks': [{'name': 'set variable', 'setvar': {'varname': 'zzz', 'varvalue': 'pluto'}}, {'name': 'readfile', 'readfile': {'filename': '/opt/a.t', 'varname': 'aaa'}}, {'name': 'print variable', 'printtext': {'varname': 'aaa'}}, {'name': 'replace test con "test "', 'replace': {'varname': 'aaa', 'leftvalue': 'test', 'rightvalue': 'test '}}, {'name': 'print variable', 'printtext': {'varname': 'aaa'}}, {'name': 'write file', 'writefile': {'filename': '/opt/a.t2', 'varname': 'aaa'}}, {'name': 'make zip', 'makezip': {'zipfilename': '/opt/a.zip', 'pathtozip': ['/opt/export/', '/opt/exportv2/'], 'zipfilter': '*'}}, {'name': 'unzip', 'unzip': {'zipfilename': '/opt/a.zip', 'pathwhereunzip': '/tmp/test/'}}, {'name': 'scp to remote', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/a.zip', 'remotepath': '/root/pippo.zip', 'recursive': False, 'direction': 'localtoremote'}}, {'name': 'scp to remote folder', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/export', 'remotepath': '/root/export', 'recursive': True, 'direction': 'localtoremote'}}, {'name': 'scp from remote', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/aremote.zip', 'remotepath': '/root/pipporemote.zip', 'recursive': False, 'direction': 'remotetolocal'}}, {'name': 'scp from remote folder', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/exportremote', 'remotepath': '/root/exporttemote', 'recursive': True, 'direction': 'remotetolocal'}}, {'name': 'copy file or directory', 'copy': {'srcpath': '/opt/exportremote', 'dstpath': '/opt/export{zzz}', 'recursive': True}}, {'name': 'copy file or directory', 'copy': {'srcpath': '/opt/aremote.zip', 'dstpath': '/opt/aremote{zzz}.zip', 'recursive': False}}, {'name': 'remove directory', 'remove': {'pathtoremove': '/opt/exportremote', 'recursive': True}}, {'name': 'remove file', 'remove': {'pathtoremove': '/opt/aremote.zip', 'recursive': False}}, {'name': 'print variable', 'printtext': {'varname': 'zzz'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'stop'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'start'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'status'}}, {'name': 'replace with regex in file', 'regexreplaceinfile': {'filein': '/opt/a.t', 'regexmatch': 'test2', 'regexvalue': 'pluto2', 'fileout': '/opt/az.t'}}, {'name': 'renamefile file or directory', 'rename': {'srcpath': '/opt/az.t', 'dstpath': '/opt/az.t{zzz}'}}]}]
task:.....set variable
task:.....readfile
task:.....print variable
test1
test2
test3

task:.....replace test con "test "
task:.....print variable
test 1
test 2
test 3

task:.....write file
task:.....make zip
task:.....unzip
task:.....scp to remote
task:.....scp to remote folder
task:.....scp from remote
task:.....scp from remote folder
task:.....copy file or directory
task:.....copy file or directory
task:.....remove directory
task:.....remove file
task:.....print variable
pluto
task:.....scp to remote
b''
task:.....scp to remote
b''
task:.....scp to remote
b'\xe2\x97\x8f ntpd.service - Network Time Service\n   Loaded: loaded (/usr/lib/systemd/system/ntpd.service; disabled; vendor preset: disabled)\n   Active: active (running) since Sun 2022-04-10 20:08:14 CEST; 295ms ago\n  Process: 21369 ExecStart=/usr/sbin/ntpd -u ntp:ntp $OPTIONS (code=exited, status=0/SUCCESS)\n Main PID: 21370 (ntpd)\n    Tasks: 1\n   CGroup: /system.slice/ntpd.service\n           \xe2\x94\x94\xe2\x94\x8021370 /usr/sbin/ntpd -u ntp:ntp -g\n\nApr 10 20:08:14 vmtest007 ntpd[21370]: ntp_io: estimated max descriptors: 1024, initial socket boundary: 16\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen and drop on 0 v4wildcard 0.0.0.0 UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen and drop on 1 v6wildcard :: UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen normally on 2 lo 127.0.0.1 UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen normally on 3 ens192 10.70.7.7 UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen normally on 4 lo ::1 UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listen normally on 5 ens192 fe80::250:56ff:fe96:ad7e UDP 123\nApr 10 20:08:14 vmtest007 ntpd[21370]: Listening on routing socket on fd #22 for interface updates\nApr 10 20:08:15 vmtest007 ntpd[21370]: 0.0.0.0 c016 06 restart\nApr 10 20:08:15 vmtest007 ntpd[21370]: 0.0.0.0 c012 02 freq_set kernel -6.055 PPM\n'
task:.....replace with regex in file
task:.....renamefile file or directory 
 ```
