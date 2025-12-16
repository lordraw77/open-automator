from fileinput import filename
import psycopg2
import inspect
import oacommon
import tabulate
import json
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-pg')

gdict = {}


def setgdict(self, gdict_param):
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param


myself = lambda: inspect.stack()[1][3]


def executeFatchAll(pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport, statement):
    conn = psycopg2.connect(
        host=pgdbhost,
        port=pgdbport,
        database=pgdatabase,
        user=pgdbusername,
        password=pgdbpassword
    )
    cur = conn.cursor()
    cur.execute(statement)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def execute(pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport, statement):
    conn = psycopg2.connect(
        host=pgdbhost,
        port=pgdbport,
        database=pgdatabase,
        user=pgdbusername,
        password=pgdbpassword
    )
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
    Esegue SELECT su PostgreSQL
    
    - name: name and description
      oa-pg.select:
        pgdatabase: ouid
        pgdbhost: 10.70.7.1
        pgdbusername: postgres
        pgdbpassword: password.123
        pgdbport: 5432
        statement: "select * from accounts"
        printout: True  # opzionale, default True
        tojsonfile: "./a.json"  # opzionale percorso file
        saveonvar: result_var  # opzionale, salva in variabile
        task_id: id univoco (opzionale)
        task_store: TaskResultStore (opzionale)
    """
    func_name = myself()
    logger.info(f"{func_name}........................ start")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        # SINTASSI CORRETTA: argomenti separati, non tupla
        if not oacommon.checkandloadparam(
            self, myself, 
            'pgdatabase', 'pgdbhost', 'pgdbusername', 'pgdbpassword', 'pgdbport', 'statement', 
            param=param
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

        logger.info(f"Executing SELECT on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement}")

        resultset = executeFatchAll(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Query returned {len(resultset)} row(s)")

        # opzionale: salvi il resultset in una variabile globale
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = resultset
            logger.debug(f"Result saved to variable: {saveonvar}")

        if oacommon.checkparam('printout', param):
            printout = param['printout']

        if printout:
            print(tabulate.tabulate(resultset))

        if oacommon.checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']

        if tojsonfile:
            oacommon.writefile(filename=tojsonfile, data=json.dumps(resultset))
            logger.info(f"Result saved to JSON file: {tojsonfile}")

        logger.info(f"{func_name}........................ end")

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
    Esegue INSERT/UPDATE/DELETE su PostgreSQL
    
    - name: name and description
      oa-pg.execute:
        pgdatabase: ouid
        pgdbhost: 10.70.7.1
        pgdbusername: postgres
        pgdbpassword: password.123
        pgdbport: 5432
        statement: "INSERT INTO ..."
        printout: True  # opzionale, default True
        tojsonfile: "./a.json"  # opzionale
        task_id: id univoco (opzionale)
        task_store: TaskResultStore (opzionale)
    """
    func_name = myself()
    logger.info(f"{func_name}........................ start")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        # SINTASSI CORRETTA
        if not oacommon.checkandloadparam(
            self, myself,
            'pgdatabase', 'pgdbhost', 'pgdbusername', 'pgdbpassword', 'pgdbport', 'statement',
            param=param
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

        logger.info(f"Executing statement on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement}")

        resultset = execute(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Statement affected {resultset} row(s)")

        # esempio: consideri 0 righe come failure logico
        if resultset == 0:
            task_success = False
            error_msg = "No rows affected by statement"
            logger.warning(error_msg)

        if oacommon.checkparam('printout', param):
            printout = param['printout']

        if printout:
            print(resultset)

        if oacommon.checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']

        if tojsonfile:
            oacommon.writefile(filename=tojsonfile, data=json.dumps(resultset))
            logger.info(f"Result saved to JSON file: {tojsonfile}")

        logger.info(f"{func_name}........................ end")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.execute failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
