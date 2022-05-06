 
import psycopg2
import inspect
import oacommon
import tabulate
import json
gdict={}
def setgdict(self,gdict):
     self.gdict=gdict
myself = lambda: inspect.stack()[1][3]


 
def _executeFatchAll(pgdatabase,pgdbhost,pgdbusername,pgdbpassword,pgdbport,statement):
    conn = psycopg2.connect(
            host=pgdbhost,
            port=pgdbport,
            database=pgdatabase,
            user=pgdbusername,
            password=pgdbpassword)
  
    cur = conn.cursor()
    cur.execute(statement)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def _execute(pgdatabase,pgdbhost,pgdbusername,pgdbpassword,pgdbport,statement):
    conn = psycopg2.connect(
            host=pgdbhost,
            port=pgdbport,
            database=pgdatabase,
            user=pgdbusername,
            password=pgdbpassword)
  
    cur = conn.cursor()
    cur.execute(statement)
    conn.commit()
    rows = cur.rowcount
    cur.close()
    conn.close()
    return rows
 

@oacommon.trace
def select(self,param):
    """
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
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('pgdatabase','pgdbhost','pgdbusername','pgdbpassword','pgdbport','statement'),param):
        pgdatabase=oacommon.effify(gdict['pgdatabase'])
        pgdbhost=oacommon.effify(gdict['pgdbhost'])
        pgdbusername=oacommon.effify(gdict['pgdbusername'])
        pgdbpassword=oacommon.effify(gdict['pgdbpassword'])
        pgdbport=oacommon.effify(gdict['pgdbport'])
        statement=oacommon.effify(gdict['statement'])
        printout=True
        tojsonfile=None
        resultset = _executeFatchAll(pgdatabase=pgdatabase,pgdbhost=pgdbhost,pgdbpassword=pgdbpassword,pgdbport=pgdbport,pgdbusername=pgdbusername,statement=statement)
        if oacommon._checkparam('printout',param):
            printout=param['printout']
        if printout:
                print(tabulate.tabulate(resultset))
        if oacommon._checkparam('tojsonfile',param):
            tojsonfile=param['tojsonfile']
        if tojsonfile:
            f = open(tojsonfile,"w")
            f.write(json.dumps(resultset))
            f.close()    

        oacommon.logend(myself())
    else:
        exit()
        

@oacommon.trace
def exexute(self,param):
    """
    - name: name and description
      oa-pg.exexute:
        pgdatabase: "ouid"
        pgdbhost: "10.70.7.1" 
        pgdbusername: "postgres"
        pgdbpassword: "password.123"
        pgdbport: 5432
        statement: "INSERT INTO public.accounts (id, username, firstname, lastname, email, \"password\", shortlink, isactive) VALUES(uuid_generate_v4(), '{username}', '{firstname}', '{lastname}', '{email}', '{passwrod}', upper(substr(md5(random()::text), 0, 7)), true);"
        printout: True #optional default value True 
        tojsonfile: ./a.json #optional if you need save on file set full path 
    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('pgdatabase','pgdbhost','pgdbusername','pgdbpassword','pgdbport','statement'),param):
        pgdatabase=oacommon.effify(gdict['pgdatabase'])
        pgdbhost=oacommon.effify(gdict['pgdbhost'])
        pgdbusername=oacommon.effify(gdict['pgdbusername'])
        pgdbpassword=oacommon.effify(gdict['pgdbpassword'])
        pgdbport=oacommon.effify(gdict['pgdbport'])
        statement=oacommon.effify(gdict['statement'])
        printout=True
        tojsonfile=None
        resultset = _execute(pgdatabase=pgdatabase,pgdbhost=pgdbhost,pgdbpassword=pgdbpassword,pgdbport=pgdbport,pgdbusername=pgdbusername,statement=statement)
        if oacommon._checkparam('printout',param):
            printout=param['printout']
        if printout:
                print(resultset)
        if oacommon._checkparam('tojsonfile',param):
            tojsonfile=param['tojsonfile']
        if tojsonfile:
            f = open(tojsonfile,"w")
            f.write(json.dumps(resultset))
            f.close()    

        oacommon.logend(myself())
    else:
        exit()
        
