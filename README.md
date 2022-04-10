# open-automator
A python automator for developer automation
beta version

## module available

### setvar: set variable for reuse
    - setvar:
        varname: zzz
        varvalue: pluto

### rename: rename file in local
    - name: renamefile file or directory
        rename:
            srcpath: /opt/exportremote
            dstpath: /opt/export{zzz} 

### copy:  file or directory in local
    - name: copy file or directory
            copy:
                srcpath: /opt/exportremote
                dstpath: /opt/export{zzz} 
                recursive: True

### remove: file or directory in local 
    - name: remove file or directory
        remove:
            pathtoremove: /opt/exportremote 
            recursive: True

### readfile: read file in a variable
      - name: readfile
        readfile:
            filename: /opt/a.t
            varname: aaa

### remove: delete file or directory in local

    - name: remove file or directory
        remove:
            pathtoremove: /opt/exportremote 
            recursive: True


### systemclt: manage systemctl
        
      - name: scp to remote  
        systemd:
            remoteserver: "10.70.7.7"
            remoteuser: "root"
            remoteport: 22
            remotepassword: "PaSsWoRd"
            servicename: ntp
            servicestate: stop 

### scp: copy file or folder from local to remote server via scp
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

### writefile: write file in local
      - name: write file
        writefile:
            filename: /opt/a.t2
            varname: aaa

### printtext: print to console a variable
      - name: printtext
        printtext:
            varname: aaa
### makezip: make zip in local
    - name: make zip
        makezip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"

### unzip: unzip file in local
    - name: unzip
        unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/

### regexreplaceinfile:   
    - name: "replace with regex in file 
      regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t

### replace: replace text in variable in memory
    - name: "replace test con \"test \""
        replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "

## Yaml conifigurazion exemple:

---

`- name: 
  tasks:
  - name: set variable
    setvar:
      varname: zzz
      varvalue: pluto
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
      dstpath: /opt/az.t{zzz} `