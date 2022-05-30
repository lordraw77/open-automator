import oacommon
import os
import shutil
import zipfile
import glob
import json
import re
from jinja2 import Environment, BaseLoader
import inspect

gdict={}

def setgdict(self,gdict):
     self.gdict=gdict

myself = lambda: inspect.stack()[1][3]


@oacommon.trace
def copy(self,param):
    """
    - name: copy file or directory
      oa-io.copy:
        srcpath: /opt/exportremote
        dstpath: /opt/export{zzz} 
        recursive: True

    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('srcpath','dstpath','recursive'),param):
        srcpath=oacommon.effify(gdict['srcpath'])
        dstpath=oacommon.effify(gdict['dstpath'])
        print(dstpath)
        print(srcpath)
        recursive=gdict['recursive']
        if recursive:
            shutil.copytree(srcpath,dstpath,dirs_exist_ok=True)
        else:
            shutil.copy(srcpath,dstpath)
        
        oacommon.logend(myself())
    else:
        exit()
        
def _zipdir(paths,zipfilter, ziph):
    for path in paths:
        path = oacommon.effify(path)
        for root, dirs, files in os.walk(path):
            for file in files:
                if "*" in zipfilter or zipfilter in file:
                    ziph.write(os.path.join(root, file), 
                            os.path.relpath(os.path.join(root, file), 
                                            os.path.join(path, '..')))
    ziph.close()
    
@oacommon.trace        
def zip(self,param):
    """
    - name: make zip
        oa-io.zip:
        zipfilename: /opt/a.zip
        pathtozip: 
            - /opt/export/
            - /opt/exportv2/
        zipfilter: "*"
    """    
    oacommon.logstart(myself())

    if oacommon.checkandloadparam(self,myself(),('zipfilename','pathtozip','zipfilter'),param):    
        zipfilename=oacommon.effify(gdict['zipfilename'])
        pathtozip=gdict['pathtozip']
        zipfilter=gdict['zipfilter']
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            _zipdir(pathtozip,zipfilter, zipf)
        oacommon.logend(myself())
    else:
        exit()

@oacommon.trace        
def unzip(self,param):
    """ 
    - name: unzip
        oa-io.unzip:
        zipfilename: /opt/a.zip
        pathwhereunzip: /tmp/test/
    """    
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('zipfilename','pathwhereunzip'),param):    
        zipfilename=oacommon.effify(gdict['zipfilename'])
        pathwhereunzip=oacommon.effify(gdict['pathwhereunzip'])
        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            zipf.extractall(pathwhereunzip)
        oacommon.logend(myself())

    else:
        exit()

@oacommon.trace
def rename(self,param):
    """
    - name: renamefile file or directory
      oa-io.rename:
        srcpath: /opt/exportremote
        dstpath: /opt/export{zzz} 
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('srcpath','dstpath'),param):
        srcpath=oacommon.effify(gdict['srcpath'])
        dstpath=oacommon.effify(gdict['dstpath'])
        os.rename(srcpath,dstpath)
        oacommon.logend(myself())
    else:
        exit()
        
@oacommon.trace
def remove(self,param):
    """
    - name: remove file or directory
      oa-io.remove:
        pathtoremove: /opt/exportremote 
        recursive: True
        NOTE: IF PATH TERMINATE WITH WILDCARD REMOVE FILE IN PATH

    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('pathtoremove','recursive'),param):
        pathtoremove=oacommon.effify(gdict['pathtoremove'])
        recursive=gdict['recursive']
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
        
        oacommon.logend(myself())
    else:
        exit()

@oacommon.trace
def readfile(self,param):

    """
      - name: readfile
        oa-io.readfile:
            filename: /opt/a.t
            varname: aaa
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('varname','filename'),param):
        varname=gdict['varname']
        filename=oacommon.effify(gdict['filename'])
        f = open(filename,"r")
        gdict[varname] =f.read()
        f.close()
        oacommon.logend(myself())

    else:
        exit()
    
@oacommon.trace
def loadvarfromjson(self,param):
    
    """ 
        load variable form json
      - name: load variable form json
        oa-io.loadvarfromjson:
            filename: /opt/uoc-generator/jtable
             
    """         
    #print(f"{myself(): <30}.....start")
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('filename', ),param):
        
        filename=oacommon.effify(gdict['filename'])
        with open(filename,'r') as f:
            data = f.read()
            jdata = json.loads(data)
            for d in jdata.keys():
                gdict[d]=jdata.get(d)
        oacommon.logend(myself())
    else:
        exit()
        
@oacommon.trace
def regexreplaceinfile(self,param):
    """
    - name: "replace with regex in file 
      oa-io.regexreplaceinfile:
        filein: /opt/a.t
        regexmatch:
        regexvalue:
        fileout: /opt/az.t
    """  
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('filein','regexmatch','regexvalue','fileout'),param):
        filein=oacommon.effify(gdict['filein'])
        regexmatch=gdict['regexmatch']
        regexvalue=oacommon.effify(gdict['regexvalue'])
        fileout=oacommon.effify(gdict['fileout'])
        with open (filein, 'r' ) as f:
            content = f.read()
            content_new = re.sub(regexmatch, regexvalue, content, flags = re.M)
            with open( fileout,'w')as fo:
                fo.write(content_new)
        oacommon.logend(myself())
    else:
        exit()

@oacommon.trace
def template(self,param):
    """
    - name:  render j2 template 
      oa-io.template:
        templatefile: ./info.j2
        dstfile: /opt/info{zzz}.txt 
            
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('templatefile','dstfile'),param):
        templatefile=oacommon.effify(gdict['templatefile'])
        dstfile=oacommon.effify(gdict['dstfile'])
        f = open(templatefile,'r')
        data= f.read()
        f.close()
        rtemplate = Environment(loader=BaseLoader).from_string(data)
        output = rtemplate.render(**gdict)
        f = open(dstfile,'w')
        f.write(output)
        f.close()
        oacommon.logend(myself())
    else:
        exit()
        
@oacommon.trace
def replace(self,param):
    """
    - name: "replace test con \"test \""
      oa-io.replace:
        varname: aaa
        leftvalue: "test"
        rightvalue: "test "
    """  
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('varname','leftvalue','rightvalue'),param):
        varname=gdict['varname']
        leftvalue=gdict['leftvalue']
        rightvalue=gdict['rightvalue']
        temp= gdict[varname]
        gdict[varname]= temp
        temp = str(temp).replace(leftvalue,rightvalue)
        oacommon.logend(myself())
    else:
        exit()
        
@oacommon.trace
def writefile(self,param):
    
    """
      - name: write file
        oa-io.writefile:
            filename: /opt/a.t2
            varname: aaa
    """  
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('varname','filename'),param):
        varname=gdict['varname']
        filename=oacommon.effify(gdict['filename'])
        f = open(filename,"w")
        f.write(str(gdict[varname]))
        f.close()
        oacommon.logend(myself())

    else:
        exit()