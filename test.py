 
import json
import dbpg
import dbmysql
import logging
import sys, getopt
import yaml
import logging.handlers
import json
import os
import platform
from jinja2 import Environment, FileSystemLoader

cwd = os.getcwd()
fileconfig = cwd +'/generator.yaml'
with open(fileconfig,'r') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
logger = logging.getLogger('Generator: ')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(config['logfile'])
handler = logging.handlers.TimedRotatingFileHandler(config['logfile'], when='midnight',  backupCount=10)
handler.suffix = "%Y-%m-%d"  
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
  

def preparateTableList(tablelist,category,prjname): 
    tables = []
    for table in tablelist:
        tab= {}
        tab['name'] = table[0]
        tab['category'] = category
        tab['prjname'] = prjname
        tables.append(tab)
    return tables
def extractRowsInfo( rows):
    
    rowstype = []
    for row in rows: 
        dictrow ={}
        logger.debug(row)
        typejava = "String"
        type = "string"
        for it in config['datamapping']:
            datamap = it['datamap']
            if datamap['type'] in row[2]:
                type=datamap['typeuoc']
                typejava=datamap['typejava']
                break    
        dictrow['field_name'] = row[1]
        dictrow['type'] = type
        dictrow['columnName'] = row[1]
        dictrow['columnType'] = typejava
        if None is not row[3]:
            dictrow['character_maximum_length'] = row[3]
        title = row[1]
        dictrow['title'] = title.capitalize()
        dictrow['key'] = title.lower()
        dictrow['columnKey'] = row[4]
        
        rowstype.append(dictrow)     
        
        logger.debug(dictrow)    
  
    return rowstype


def main2():

    schema = config['schema']
    category= config['category']
    version=config['version']
    prjname =config['prjname']

        
    
    tablelist = dbmysql.getTableList(config=config,logger=logger,schema=schema)
    tablelist2 = preparateTableList(tablelist=tablelist,category=category,prjname=prjname)
    rowsdefinitions = {}
    for table in tablelist:
        table_name=table[0]
        row = extractRowsInfo(dbmysql.getTableDefinition(config=config,logger=logger,schema=schema,tablename=table_name))
        rowsdefinitions[table_name]=row
    
    print (rowsdefinitions)
    print ('\n')
    print ('\n\n\n') 
     
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.rstrip_blocks = True
    template = env.get_template("aaa.j2")
    output = template.render(tables=tablelist2,rowsdefinitions=rowsdefinitions)
    #print(output)
    f = open("/opt/test","w")
    f.write(output)
    f.close()
    
    
    
    jtable = json.dumps(tablelist)
    jrowdefinitions= json.dumps(rowsdefinitions)
     
    f = open('jtable', "w")
    f.write(jtable)
    f.close()
    
    f = open('jrowdefinitions', "w")
    f.write(jrowdefinitions)
    f.close()
    
    f = open('jtable', "r")
    listtable = json.loads(f.read())
    f.close()
    
    f = open('jrowdefinitions', "r")
    listrowdefinition = json.loads(f.read())
    f.close()
    print
    
def main():
    param = {
        "zipfilename": "Ford",
        "pathtozip":"aaa",
        "zipfilter": "*" 
    }
    paramneed = ("zipfilename","pathtozip","zipfilter")
    for par in paramneed:
        if par in param:
            globals()[par]= param.get(par)
        else:
            print(f'the param need for xxx is {paramneed}')
            break
    
    for par in paramneed:
        print(f'{par}:  {globals()[par]}')
    
if __name__ == "__main__":
   main()
 