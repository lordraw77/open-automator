"""
Open-Automator PostgreSQL Module
Gestisce operazioni su database PostgreSQL con data propagation
"""

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
    """Helper per eseguire SELECT e fetchare tutte le righe"""
    conn = psycopg2.connect(
        host=pgdbhost,
        port=pgdbport,
        database=pgdatabase,
        user=pgdbusername,
        password=pgdbpassword
    )
    cur = conn.cursor()
    cur.execute(statement)
    
    # Recupera anche i nomi delle colonne
    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return rows, columns


def executeStatement(pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport, statement):
    """Helper per eseguire INSERT/UPDATE/DELETE"""
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
    Esegue SELECT su PostgreSQL con data propagation

    Args:
        param: dict con:
            - pgdatabase: nome database
            - pgdbhost: host
            - pgdbusername: username
            - pgdbpassword: password
            - pgdbport: porta
            - statement: query SQL (può usare input da task precedente)
            - printout: (opzionale) stampa risultato, default False
            - tojsonfile: (opzionale) percorso file JSON
            - saveonvar: (opzionale) salva in variabile
            - format: (opzionale) 'rows', 'dict', 'json' - default 'dict'
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_data) con risultati query
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL SELECT")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se statement non è specificato, prova a costruirlo dall'input
        if 'statement' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'statement' in prev_input:
                    param['statement'] = prev_input['statement']
                elif 'query' in prev_input:
                    param['statement'] = prev_input['query']
                logger.info("Using SQL statement from previous task")
        
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

        printout = param.get('printout', False)
        format_type = param.get('format', 'dict')

        logger.info(f"Executing SELECT on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement}")

        resultset, columns = executeFatchAll(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Query returned {len(resultset)} row(s) with {len(columns)} column(s)")

        # Formatta i risultati in base al formato richiesto
        if format_type == 'dict':
            # Converti in lista di dict (più facile da usare nei task successivi)
            formatted_results = []
            for row in resultset:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    row_dict[col_name] = row[i]
                formatted_results.append(row_dict)
            logger.debug(f"Results formatted as list of dicts")
        elif format_type == 'json':
            # JSON string
            temp_results = []
            for row in resultset:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                temp_results.append(row_dict)
            formatted_results = json.dumps(temp_results, default=str, indent=2)
        else:  # 'rows'
            # Tuple raw
            formatted_results = resultset

        # Salva in variabile (retrocompatibilità)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = formatted_results
            logger.debug(f"Result saved to variable: {saveonvar}")

        # Printout
        if printout:
            if format_type == 'json':
                print(formatted_results)
            else:
                print(tabulate.tabulate(resultset, headers=columns, tablefmt='grid'))

        # Salva su file JSON
        if oacommon.checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']
            if format_type == 'json':
                oacommon.writefile(filename=tojsonfile, data=formatted_results)
            else:
                # Converti in dict per JSON
                temp_results = []
                for row in resultset:
                    row_dict = {columns[i]: row[i] for i in range(len(columns))}
                    temp_results.append(row_dict)
                oacommon.writefile(filename=tojsonfile, data=json.dumps(temp_results, default=str, indent=2))
            logger.info(f"Result saved to JSON file: {tojsonfile}")

        # Output data per propagation
        output_data = {
            'rows': formatted_results,
            'row_count': len(resultset),
            'columns': columns,
            'database': pgdatabase,
            'host': pgdbhost,
            'statement': statement
        }

        logger.info(f"{func_name} completed successfully")

    except psycopg2.OperationalError as e:
        task_success = False
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except psycopg2.ProgrammingError as e:
        task_success = False
        error_msg = f"SQL syntax error: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.select failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def execute(self, param):
    """
    Esegue INSERT/UPDATE/DELETE su PostgreSQL con data propagation

    Args:
        param: dict con:
            - pgdatabase: nome database
            - pgdbhost: host
            - pgdbusername: username
            - pgdbpassword: password
            - pgdbport: porta
            - statement: statement SQL (può usare input da task precedente)
            - printout: (opzionale) stampa risultato, default False
            - fail_on_zero: (opzionale) fallisce se 0 righe affette, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_data) con numero righe affette
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL EXECUTE")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se statement non è specificato, prova a costruirlo dall'input
        if 'statement' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'statement' in prev_input:
                    param['statement'] = prev_input['statement']
                elif 'query' in prev_input:
                    param['statement'] = prev_input['query']
                # Se l'input ha 'rows', costruisci INSERT dinamico
                elif 'rows' in prev_input and 'table' in param:
                    rows_data = prev_input['rows']
                    table_name = param['table']
                    if isinstance(rows_data, list) and len(rows_data) > 0:
                        # Genera INSERT multipli (esempio base)
                        first_row = rows_data[0]
                        if isinstance(first_row, dict):
                            columns = ', '.join(first_row.keys())
                            values_list = []
                            for row in rows_data:
                                values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in row.values()])
                                values_list.append(f"({values})")
                            param['statement'] = f"INSERT INTO {table_name} ({columns}) VALUES {', '.join(values_list)}"
                            logger.info(f"Generated INSERT statement from input data")
                logger.info("Using SQL statement from previous task")
        
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

        printout = param.get('printout', False)
        fail_on_zero = param.get('fail_on_zero', False)

        logger.info(f"Executing statement on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement}")

        rows_affected = executeStatement(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Statement affected {rows_affected} row(s)")

        # Opzionale: considera 0 righe come failure
        if fail_on_zero and rows_affected == 0:
            task_success = False
            error_msg = "No rows affected by statement"
            logger.warning(error_msg)

        if printout:
            print(f"Rows affected: {rows_affected}")

        # Salva su file JSON se richiesto
        if oacommon.checkparam('tojsonfile', param):
            tojsonfile = param['tojsonfile']
            result_json = {
                'rows_affected': rows_affected,
                'statement': statement,
                'database': pgdatabase
            }
            oacommon.writefile(filename=tojsonfile, data=json.dumps(result_json, indent=2))
            logger.info(f"Result saved to JSON file: {tojsonfile}")

        # Output data per propagation
        output_data = {
            'rows_affected': rows_affected,
            'statement': statement,
            'database': pgdatabase,
            'host': pgdbhost,
            'success': task_success
        }

        logger.info(f"{func_name} completed successfully")

    except psycopg2.OperationalError as e:
        task_success = False
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except psycopg2.ProgrammingError as e:
        task_success = False
        error_msg = f"SQL syntax error: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except psycopg2.IntegrityError as e:
        task_success = False
        error_msg = f"Database integrity error: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.execute failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def insert(self, param):
    """
    Helper per INSERT con data propagation da input precedente

    Args:
        param: dict con:
            - pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport
            - table: nome tabella
            - data: (opzionale) dict o lista di dict da inserire
            - input: (opzionale) dati dal task precedente (se formato corretto)
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_data)
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL INSERT helper")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Determina i dati da inserire
        insert_data = None
        
        if 'data' in param:
            insert_data = param['data']
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'rows' in prev_input:
                    insert_data = prev_input['rows']
                else:
                    # Singolo dict = singola riga
                    insert_data = [prev_input]
            elif isinstance(prev_input, list):
                insert_data = prev_input
            logger.info("Using data from previous task for INSERT")
        
        if not insert_data:
            raise ValueError("No data to insert (provide 'data' or pipe from previous task)")
        
        if not oacommon.checkandloadparam(
            self, myself,
            'pgdatabase', 'pgdbhost', 'pgdbusername', 'pgdbpassword', 'pgdbport', 'table',
            param=param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        table_name = gdict['table']
        
        # Converti in lista se è un singolo dict
        if isinstance(insert_data, dict):
            insert_data = [insert_data]
        
        if not isinstance(insert_data, list) or len(insert_data) == 0:
            raise ValueError("Insert data must be a non-empty list of dicts")
        
        # Genera statement INSERT
        first_row = insert_data[0]
        columns = ', '.join(first_row.keys())
        
        # Usa parametrizzazione per sicurezza
        placeholders = ', '.join(['%s'] * len(first_row))
        statement = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        logger.info(f"Inserting {len(insert_data)} row(s) into {table_name}")
        logger.debug(f"Statement template: {statement}")

        # Connessione
        pgdatabase = oacommon.effify(gdict['pgdatabase'])
        pgdbhost = oacommon.effify(gdict['pgdbhost'])
        pgdbusername = oacommon.effify(gdict['pgdbusername'])
        pgdbpassword = oacommon.effify(gdict['pgdbpassword'])
        pgdbport = oacommon.effify(gdict['pgdbport'])
        
        conn = psycopg2.connect(
            host=pgdbhost,
            port=pgdbport,
            database=pgdatabase,
            user=pgdbusername,
            password=pgdbpassword
        )
        cur = conn.cursor()
        
        # Execute many per performance
        values_list = [tuple(row.values()) for row in insert_data]
        cur.executemany(statement, values_list)
        conn.commit()
        rows_affected = cur.rowcount
        
        cur.close()
        conn.close()

        logger.info(f"Successfully inserted {rows_affected} row(s)")

        # Output data
        output_data = {
            'rows_inserted': rows_affected,
            'table': table_name,
            'database': pgdatabase,
            'host': pgdbhost
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"oa-pg.insert failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data
