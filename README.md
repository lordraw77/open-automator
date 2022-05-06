# open-automator
***beta version***

Open Automator is a python project, for the automation of development support scripts and common task.


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
- psycopg2-binary
- tabulate

#### before exec:
pip3.10 install -r requirements.txt

 ```console
/usr/local/bin/python3.10 /opt/open-automator/automator.py -h
usage: automator.py [-h] [-d] [-t] tasks

exec open-automator tasks

positional arguments:
  tasks       yaml for task description

options:
  -h, --help  show this help message and exit
  -d          debug enable
  -d2         debug2 enable
  -t          trace enable
 ```

#### In task name can use F-string syntax for replace with variable loadded in running 


## module available

- [oa-utility.setvar](#oa-utilitysetvar)
- [oa-utility.printvar](#oa-utilityprintvar)
- [oa-utility.setsleep](#oa-utilitysetsleep)
- [oa-io.rename](#oa-iorename)
- [oa-io.copy](#oa-iocopy)
- [oa-io.readfile](#oa-ioreadfile)
- [oa-io.remove](#oa-ioremove)
- [oa-io.writefile](#oa-iowritefile)
- [oa-io.makezip](#oa-iomakezip)
- [oa-io.unzip](#oa-iounzip)
- [oa-io.regexreplaceinfile](#oa-ioregexreplaceinfile)
- [oa-io.replace](#oa-ioreplace)
- [oa-io.loadvarfromjeson](#oa-ioloadvarfromjeson)
- [oa-io.template](#oa-iotemplate)
- [os-network.httpget](#os-networkhttpget)
- [os-network.httpsget](#os-networkhttpsget)
- [oa-system.remotecommand](#oa-systemremotecommand)
- [oa-system.scp](#oa-systemscp)
- [oa-system.systemd](#oa-systemsystemd)
- [oa-system.remoteunzip](#oa-systemremoteunzip)
- [oa-system.runcmd](#oa-systemruncmd)
- [oa-notify.sendtelegramnotify](#oa-notifysendtelegramnotify)
- [oa-notify.sendmailbygmail](#oa-notifysendmailbygmail)
- [oa-pg.execute](#oa-pgexecute)
- [oa-pg.select](#oa-pgselect)

# oa-utility.setvar:  

### This module is for set a varible during execution of automator 

| Parameter Name   |  Parameter Description      |      
|-------------|:----------: 
| varname |  variable name  |
| varvalue |  value to set in variable | 
 
Config exemple:
``` yaml
   - name setvar #set pluto in zzz var 
     oa-utility.setvar:
       varname: zzz
       varvalue: pluto

``` 
# oa-io.rename: 

### This module is for rename one file or one directory in local in local
#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| srcpath |  file or directory source  |
| dstpath |  file or directory destination | 

Config exemple:
``` yaml
    - name: renamefile file or directory
      oa-io.rename:
          srcpath: /opt/exportremote
          dstpath: /opt/export{zzz} 

``` 
# oa-io.copy:  

### This moduleis for copy file or directory in local
#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| srcpath |  file or directory source  |
| dstpath |  file or directory destination | 
| recursive |  True if is directory | 

Config exemple:
``` yaml
   - name: copy file or directory
     oa-io.copy:
         srcpath: /opt/exportremote
         dstpath: /opt/export{zzz} 
         recursive: True

``` 
# oa-io.readfile: 

### This module is for read file in a variable
#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filename |  file name and path for file to load|
| varname |   var where store the file context | 
 
Config exemple:
``` yaml
   - name: readfile
     oa-io.readfile:
         filename: /opt/a.t
         varname: aaa

``` 
# oa-io.remove: 

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
      oa-io.remove:
          pathtoremove: /opt/exportremote 
          recursive: True

``` 
# oa-system.systemd

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
        oa-system.systemd:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "PaSsWoRd"
            servicename: ntp
            servicestate: stop 

``` 

# oa-system.scp:

### This moodule is for manage copy file or folder from local to remote or remote to local via scp 

#### In path variable can use F-string syntax for replace with variable loadded in running 


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| remoteserver |  ip or host name for remote server  |
| remoteuser |     user with greant for manage service | 
| remoteport |  ssh port number  |
| remotepassword |     user password | 
| localpath |  local path for get or put file see note for multifile config |
| remotepath | remote path for get or put file see note for multifile config | 
| recursive | True is directory | 
| direction | localtoremote (for put ) or remotetolocal ( for get )   | 


#### Note: if use multiple file config, the number of elements must be the same on local and remote path. 
####    For single file: 
``` yaml
   {local|remote}path: /opt/a.zip
```
####    For multipe file:
``` yaml
    {local|remote}path:
                    - /opt/a.zip
                    - /opt/b.zip
```

Config exemple:
``` yaml
    - name: scp to remote  
      oa-system.scp:
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

# oa-io.writefile:

### This module is for dump variable in local file

#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filename | full file path  |
| varname |  variable to dump | 

Config exemple:
``` yaml      
      - name: write file
        oa-io.writefile:
            filename: /opt/a.t2
            varname: aaa

``` 

# oa-utility.printvar: 

### This module is for print to console a variable

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| varname |  variable to print to console | 

Config exemple:
``` yaml
    - name: printvar
      oa-utility.printvar:
          varname: aaa
``` 

# oa-io.makezip:

### This module is for make zip in local

#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| zipfilename | full file path  |
| pathtozip |  only array, at min 1 element | 
| zipfilter | file name filter use * for all element  |


Config exemple:

``` yaml
   - name: make zip
     oa-io.makezip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"

```
# oa-io.unzip:

### This module is for unzip in local

#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| zipfilename | full file path  |
| pathwhereunzip | path to unzip file | 
 
Config exemple:

 ``` yaml
   - name: unzip
     oa-io.unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/

``` 

# oa-io.regexreplaceinfile:

### This module is for exec regexreplace in a file 

#### In path variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filein | full file path  |
| regexmatch | regex for match | 
| fileout | full file path  |
| regexvalue | path to unzip file | 
 
Config exemple:

``` yaml 
    - name: "replace with regex in file 
      oa-io.regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t

``` 

# oa-io.replace:

### This module is for exec replace in memory  


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| varname | variable name  |
| leftvalue | value to match | 
| rightvalue | value to replace  |

 
Config exemple:

``` yaml
    - name: "replace test con \"test \""
      oa-io.replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "

```         
# oa-system.remotecommand:

### This module is for execute remote command over ssh  


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| remoteserver |  ip or host name for remote server  |
| remoteuser |     user with greant for manage service | 
| remoteport |  ssh port number  |
| remotepassword |     user password | 
| command |  command to execute |
| saveonvar | optional, save output on variable | 
 
Config exemple:


``` yaml
    - name: execute remote command over ssh 
      oa-system.remotecommand:
          remoteserver: "10.70.7.7"
          remoteuser: "root"
          remoteport: 22
          remotepassword: "PaSsWoRd"
          command: ls -al /root
          saveonvar: outputvar #optional save output in var the param are variablename

``` 

# oa-io.loadvarfromjeson:

### This module is for load variable form json

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filename | full file name with json format  |
  
Config exemple:

``` yaml
   - name: load variable form json
     oa-io.loadvarfromjeson:
         filename: /opt/uoc-generator/jtable
```

# oa-io.template: 

### This module is for render j2 template

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| filename | full file name with json format  |
  
Config exemple:

``` yaml
    - name:  render j2 template 
      oa-io.template:
        templatefile: ./info.j2
        dstfile: /opt/info{zzz}.txt 
```

# os-network.httpget: 

### This module is for make an http get 

#### In host e port variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| host | ip o fqdn host to call  |
| port | port number for host to call  |
| get | get url  |
| printout | optional, if True print content to console    |
| saveonvar | optional, if set create a variable with content  |
  
Config exemple:
 
``` yaml
    - name: make http get 
      os-network.httpget: 
        host: "10.70.7.7"
        port: 9999
        get: "/"
        printout: True #optional default false 
        saveonvar: "outputvar" #optional save output in var
```

# os-network.httpsget: 

### This module is for make an https get 

#### In host e port variable can use F-string syntax for replace with variable loadded in running 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| host | ip o fqdn host to call  |
| port | port number for host to call  |
| get | get url  |
| printout | optional, if True print content to console    |
| saveonvar | optional, if set create a variable with content  |
| verify | True for ssl verify  |
  
Config exemple:
 


``` yaml
    - name: make https get 
      os-network.httpsget: 
        host: "10.70.7.7"
        port: 443
        get: "/"
        printout: True
        saveonvar: outputVarPPP 
        verify: False
```

# oa-utility.setsleep:

### This module is for sleep

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| seconds | sleep in second  |
  
Config exemple:

``` yaml
    - name: "sleep"
      oa-utility.setsleep:
            seconds: 6
```
# oa-system.runcmd:

### This module is for exec command in local shell ( bash cmd )  



| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| command |  command to execute  |
| printout |   print the output value of command | 
| saveonvar   | Optional the name of var to set with the output command | 



Config exemple:

``` yaml
    - name: runcmd
      oa-system.runcmd:
          command: echo hello
          printout: True
          saveonvar: xxx
```


# oa-system.remoteunzip:

### This module is unzip and trasfer on remote server 

#### In path variable can use F-string syntax for replace with variable loadded in running 


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| remoteserver |  ip or host name for remote server  |
| remoteuser |     user with greant for manage service | 
| remoteport |  ssh port number  |
| remotepassword |     user password | 
| zipfilename |   full file name of zip on local folder | 
| pathwhereunzip |     full file path remote for unzip file | 


Config exemple:

``` yaml
    - name: remoteunzip
      oa-system.remoteunzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/
        remoteserver: "10.70.7.7"
        remoteuser: "root"
        remoteport: 22
        remotepassword: "PaSsWoRd"
```


# oa-notify.sendtelegramnotify:

### This module send notification over telegram in a bot

#### In message  variable can use F-string syntax for replace with variable loadded in running 

#### Important for corret working 

    Assume the bot name is my_bot. for make a bot use: [botfather](https://t.me/botfather)
    1 Make /start on your bot
    2 Send a dummy message to the bot.
      You can use this example: /my_id @my_bot
    3 Go to following url: https://api.telegram.org/botXXX:YYYY/getUpdates
      replace XXX:YYYY with your bot token
      Or 
      join [RawDataBot](https://t.me/RawDataBot) /start 
    4 Look for "chat":{"id":zzzzzzzzzz, zzzzzzzzzz is your chat id 

| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| tokenid |  mail address of sender  |
| chatid |     mail address of reciver, separed by comma | 
| message |  password of mail address account sender |
| printresponse | Optional defalult false, if true print the output of telegram call NOT any response from telegram | 
 

Config exemple:

``` yaml
    
    - name: send telegram message
      oa-notify.sendtelegramnotify:
        tokenid: "XXXX:YYYY"
        chatid: 
           - "zzzzzzzz"
        message: "prova {zzz} test"
        printresponse: True #optional

```

# oa-notify.sendmailbygmail:

### This module send mail using gmail

#### In message  variable can use F-string syntax for replace with variable loadded in running 


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| senderemail |  mail address of sender  |
| receiveremail |     mail address of reciver, separed by comma | 
| senderpassword |  password of mail address account sender |
| subject |     mail subject | 
| messagetext |  body message in format textplain | 
| messagehtml |  body message in format html | 

#### Important specify or messagetext or messagehtml or both

Config exemple:

``` yaml
    
    - name: send mail by gmail
      oa-notify.sendmailbygmail:
        senderemail: "xxxx.yyyy@gmail.com"
        receiveremail: "xxxx2.yyyy2@gmail.com,xxxx.yyyy@gmail.com"
        senderpassword: "password"
        subject: "nofify"
        messagetext: >
            prova {zzz} test
        messagehtml: >
            <html>
            <body>
                <b>prova</b> {zzz} test
            </body>
            </html>
```


# oa-pg.select:

### This module is unzip and trasfer on remote server 

#### In variable can use F-string syntax for replace with variable loadded in running 


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| pgdatabase |  databasename  |
| pgdbhost |    ip or hostname | 
| pgdbpassword |   password  |
| pgdbusername |     user name | 
| pgdbport |   portnameber | 
| statement | the select to execute|
| printout | Optional,default value is true | 
| tojsonfile| Optional if you need save on file set full path |

Config exemple:

``` yaml
  - name: name and description
      oa-pg.select:
        pgdatabase: "ouid"
        pgdbhost: "10.70.7.1" 
        pgdbusername: "postgres"
        pgdbpassword: "password.123"
        pgdbport: 5432
        statement: 'select * from accounts'
        printout: True #optional default value True 
        tojsonfile: ./a.json #optional if you need save on file set full path 
```



# oa-pg.execute:

### This module is unzip and trasfer on remote server 

#### In variable can use F-string syntax for replace with variable loadded in running 


| Parameter Name   | Parameter Description       |      
|-------------|:----------: 
| pgdatabase |  databasename  |
| pgdbhost |    ip or hostname | 
| pgdbpassword |   password  |
| pgdbusername |     user name | 
| pgdbport |   portnameber | 
| statement | the insert update or delete to execute|
| printout | Optional,default value is true | 
| tojsonfile| Optional if you need save on file set full path |

Config exemple:

``` yaml
  - name: name and description
      oa-pg.execute:
        pgdatabase: "ouid"
        pgdbhost: "10.70.7.1" 
        pgdbusername: "postgres"
        pgdbpassword: "password.123"
        pgdbport: 5432
        statement: "INSERT INTO public.accounts (id, username, firstname, lastname, email, \"password\", shortlink, isactive) VALUES(uuid_generate_v4(), '{username}', '{firstname}', '{lastname}', '{email}', '{passwrod}', upper(substr(md5(random()::text), 0, 7)), true);"
        printout: True #optional default value True 
        tojsonfile: ./a.json #optional if you need save on file set full path 
    """
```


# Yaml conifigurazion exemple:
``` yaml
# YAML
- name: 
  tasks:
  - name: make https get 
    os-network.httpsget: 
      host: "10.70.7.7"
      port: 443
      get: "/"
      printout: False
      saveonvar: outputVarPPP 
      verify: False
  - name: print variable
    oa-utility.printvar:
      varname: outputVarPPP
 ```
      
      
 # Console output
 
 
 ```console
 /usr/local/bin/python3.10 /opt/open-automator/automator.py
start process tasks form automator.yaml
[{'name': None, 'tasks': [{'name': 'set variable', 'setvar': {'varname': 'zzz', 'varvalue': 'pluto'}}, {'name': 'readfile', 'readfile': {'filename': '/opt/a.t', 'varname': 'aaa'}}, {'name': 'print variable', 'printvar': {'varname': 'aaa'}}, {'name': 'replace test con "test "', 'replace': {'varname': 'aaa', 'leftvalue': 'test', 'rightvalue': 'test '}}, {'name': 'print variable', 'printvar': {'varname': 'aaa'}}, {'name': 'write file', 'writefile': {'filename': '/opt/a.t2', 'varname': 'aaa'}}, {'name': 'make zip', 'makezip': {'zipfilename': '/opt/a.zip', 'pathtozip': ['/opt/export/', '/opt/exportv2/'], 'zipfilter': '*'}}, {'name': 'unzip', 'unzip': {'zipfilename': '/opt/a.zip', 'pathwhereunzip': '/tmp/test/'}}, {'name': 'scp to remote', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/a.zip', 'remotepath': '/root/pippo.zip', 'recursive': False, 'direction': 'localtoremote'}}, {'name': 'scp to remote folder', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/export', 'remotepath': '/root/export', 'recursive': True, 'direction': 'localtoremote'}}, {'name': 'scp from remote', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/aremote.zip', 'remotepath': '/root/pipporemote.zip', 'recursive': False, 'direction': 'remotetolocal'}}, {'name': 'scp from remote folder', 'scp': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'localpath': '/opt/exportremote', 'remotepath': '/root/exporttemote', 'recursive': True, 'direction': 'remotetolocal'}}, {'name': 'copy file or directory', 'copy': {'srcpath': '/opt/exportremote', 'dstpath': '/opt/export{zzz}', 'recursive': True}}, {'name': 'copy file or directory', 'copy': {'srcpath': '/opt/aremote.zip', 'dstpath': '/opt/aremote{zzz}.zip', 'recursive': False}}, {'name': 'remove directory', 'remove': {'pathtoremove': '/opt/exportremote', 'recursive': True}}, {'name': 'remove file', 'remove': {'pathtoremove': '/opt/aremote.zip', 'recursive': False}}, {'name': 'print variable', 'printvar': {'varname': 'zzz'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'stop'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'start'}}, {'name': 'scp to remote', 'systemd': {'remoteserver': '10.70.7.7', 'remoteuser': 'root', 'remoteport': 22, 'remotepassword': 'password.123', 'servicename': 'ntpd', 'servicestate': 'status'}}, {'name': 'replace with regex in file', 'regexreplaceinfile': {'filein': '/opt/a.t', 'regexmatch': 'test2', 'regexvalue': 'pluto2', 'fileout': '/opt/az.t'}}, {'name': 'renamefile file or directory', 'rename': {'srcpath': '/opt/az.t', 'dstpath': '/opt/az.t{zzz}'}}]}]
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
