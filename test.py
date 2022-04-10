 
import json
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
 