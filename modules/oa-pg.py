 
from fileinput import filename
import psycopg2
import inspect
import oacommon
import tabulate
import json

import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-pg')



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
def select(self, param):
    """
    - name: name and description
      oa-pg.select:
        pgdatabase: "ouid"
        pgdbhost: "10.70.7.1" 
        pgdbusername: "postgres"
        pgdbpassword: "password.123"
        pgdbport: 5432
        statement: 'select * from accounts'
        printout: True   # opzionale, default True 
        tojsonfile: ./a.json  # opzionale percorso file
        task_id: <id univoco>        # opzionale
        task_store: <TaskResultStore>  # opzionale
    """
    func_name = myself()
    oacommon.logstart(func_name)

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(
            self, myself(),
            ('pgdatabase', 'pgdbhost', 'pgdbusername', 'pgdbpassword', 'pgdbport', 'statement'),
            param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        pgdatabase = oacommon.effify(gdict['pgdatabase'])
        pgdbhost = oacommon.effify(gdict['pgdbhost'])
        pgdbusername = oacommon.effify(gdict['pgdbusername'])
        pgdbpassword = oacommon.effify(gdict['pgdbpassword'])
        pgdbport = oacommon.effify(gdict['pgdbport'])
        statement = oacommon.effify(gdict['statement'])

        printout = True
        tojsonfile = None

        resultset = _executeFatchAll(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        # opzionale: salvi il resultset in una variabile globale
        if oacommon._checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = resultset

        if oacommon._checkparam('printout', param):
            printout = param['printout']
        if printout:
            print(tabulate.tabulate(resultset))

        if oacommon._checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']
        if tojsonfile:
            oacommon.writefile(filename=tojsonfile, data=json.dumps(resultset))

        oacommon.logend(func_name)

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.select failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success

        
@oacommon.trace
def execute(self, param):
    """
    - name: name and description
      oa-pg.execute:
        pgdatabase: "ouid"
        pgdbhost: "10.70.7.1" 
        pgdbusername: "postgres"
        pgdbpassword: "password.123"
        pgdbport: 5432
        statement: "INSERT INTO ..."
        printout: True       # opzionale, default True 
        tojsonfile: ./a.json # opzionale
        task_id: <id univoco>        # opzionale
        task_store: <TaskResultStore>  # opzionale
    """
    func_name = myself()
    oacommon.logstart(func_name)

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(
            self, myself(),
            ('pgdatabase', 'pgdbhost', 'pgdbusername', 'pgdbpassword', 'pgdbport', 'statement'),
            param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        pgdatabase = oacommon.effify(gdict['pgdatabase'])
        pgdbhost = oacommon.effify(gdict['pgdbhost'])
        pgdbusername = oacommon.effify(gdict['pgdbusername'])
        pgdbpassword = oacommon.effify(gdict['pgdbpassword'])
        pgdbport = oacommon.effify(gdict['pgdbport'])
        statement = oacommon.effify(gdict['statement'])

        printout = True
        tojsonfile = None

        resultset = _execute(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        # esempio: consideri 0 righe come failure logico
        if resultset == 0:
            task_success = False
            error_msg = "No rows affected by statement"

        if oacommon._checkparam('printout', param):
            printout = param['printout']
        if printout:
            print(resultset)

        if oacommon._checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']
        if tojsonfile:
            oacommon.writefile(filename=tojsonfile, data=json.dumps(resultset))

        oacommon.logend(func_name)

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.execute failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
