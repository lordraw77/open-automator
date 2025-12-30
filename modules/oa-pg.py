"""
Open-Automator PostgreSQL Module

Manages PostgreSQL database operations with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
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
    """Helper to execute SELECT and fetch all rows"""
    conn = psycopg2.connect(
        host=pgdbhost,
        port=pgdbport,
        database=pgdatabase,
        user=pgdbusername,
        password=pgdbpassword
    )
    cur = conn.cursor()
    cur.execute(statement)

    # Also retrieve column names
    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows, columns

def executeStatement(pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport, statement):
    """Helper to execute INSERT/UPDATE/DELETE"""
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
    Executes SELECT on PostgreSQL with data propagation

    Args:
        param: dict with:
            - pgdatabase: database name - supports {WALLET:key}, {ENV:var}
            - pgdbhost: host - supports {WALLET:key}, {ENV:var}
            - pgdbusername: username - supports {WALLET:key}, {ENV:var}
            - pgdbpassword: password - supports {WALLET:key}, {VAULT:key}
            - pgdbport: port - supports {ENV:var}
            - statement: SQL query (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - printout: (optional) print result, default False
            - tojsonfile: (optional) JSON file path
            - saveonvar: (optional) save to variable
            - format: (optional) 'rows', 'dict', 'json' - default 'dict'
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_data) with query results

    Example YAML:
        # Simple SELECT query
        - name: get_users
          module: oa-pg
          function: select
          pgdatabase: "myapp"
          pgdbhost: "localhost"
          pgdbusername: "postgres"
          pgdbpassword: "{VAULT:db_password}"
          pgdbport: 5432
          statement: "SELECT id, name, email FROM users WHERE active = true"
          printout: true

        # Query with credentials from wallet/vault
        - name: query_production_db
          module: oa-pg
          function: select
          pgdatabase: "{ENV:DB_NAME}"
          pgdbhost: "{ENV:DB_HOST}"
          pgdbusername: "{WALLET:db_user}"
          pgdbpassword: "{VAULT:db_pass}"
          pgdbport: 5432
          statement: "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'"
          format: "dict"

        # Save results to JSON file
        - name: export_data
          module: oa-pg
          function: select
          pgdatabase: "analytics"
          pgdbhost: "db-server"
          pgdbusername: "readonly"
          pgdbpassword: "{VAULT:readonly_pass}"
          pgdbport: 5432
          statement: "SELECT user_id, COUNT(*) as orders FROM orders GROUP BY user_id"
          tojsonfile: "/data/user_orders.json"
          format: "json"

        # Query with dynamic WHERE clause from wallet
        - name: filtered_query
          module: oa-pg
          function: select
          pgdatabase: "mydb"
          pgdbhost: "localhost"
          pgdbusername: "app"
          pgdbpassword: "{VAULT:app_pass}"
          pgdbport: 5432
          statement: "SELECT * FROM products WHERE category = '{WALLET:target_category}'"

        # Save to variable for next task
        - name: get_pending_tasks
          module: oa-pg
          function: select
          pgdatabase: "tasks"
          pgdbhost: "{ENV:TASK_DB_HOST}"
          pgdbusername: "{WALLET:db_user}"
          pgdbpassword: "{VAULT:db_pass}"
          pgdbport: 5432
          statement: "SELECT task_id, description FROM tasks WHERE status = 'pending'"
          saveonvar: pending_tasks
          format: "dict"

        # Complex JOIN query
        - name: user_orders_report
          module: oa-pg
          function: select
          pgdatabase: "ecommerce"
          pgdbhost: "prod-db"
          pgdbusername: "{WALLET:reporting_user}"
          pgdbpassword: "{VAULT:reporting_pass}"
          pgdbport: 5432
          statement: |
            SELECT u.name, u.email, COUNT(o.id) as order_count, SUM(o.total) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at > '2025-01-01'
            GROUP BY u.id, u.name, u.email
            ORDER BY total_spent DESC
            LIMIT 100
          format: "dict"
          printout: true

        # Query from previous task
        - name: execute_dynamic_query
          module: oa-pg
          function: select
          pgdatabase: "mydb"
          pgdbhost: "localhost"
          pgdbusername: "user"
          pgdbpassword: "{VAULT:pass}"
          pgdbport: 5432
          # statement from previous task output
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL SELECT")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If statement not specified, try to build from input
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders (CRITICAL for password!)
        pgdatabase = oacommon.get_param(param, 'pgdatabase', wallet) or gdict.get('pgdatabase')
        pgdbhost = oacommon.get_param(param, 'pgdbhost', wallet) or gdict.get('pgdbhost')
        pgdbusername = oacommon.get_param(param, 'pgdbusername', wallet) or gdict.get('pgdbusername')
        pgdbpassword = oacommon.get_param(param, 'pgdbpassword', wallet) or gdict.get('pgdbpassword')
        pgdbport = oacommon.get_param(param, 'pgdbport', wallet) or gdict.get('pgdbport')
        statement = oacommon.get_param(param, 'statement', wallet) or gdict.get('statement')

        printout = param.get('printout', False)
        format_type = param.get('format', 'dict')

        logger.info(f"Executing SELECT on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement[:100]}..." if len(statement) > 100 else f"Statement: {statement}")

        resultset, columns = executeFatchAll(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Query returned {len(resultset)} row(s) with {len(columns)} column(s)")

        # Format results based on requested format
        if format_type == 'dict':
            # Convert to list of dicts (easier to use in subsequent tasks)
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
            # Raw tuples
            formatted_results = resultset

        # Save to variable (backward compatibility)
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

        # Save to JSON file
        if oacommon.checkparam('tojsonfile', param):
            tojsonfile_param = oacommon.get_param(param, 'tojsonfile', wallet) or param.get('tojsonfile')
            if format_type == 'json':
                oacommon.writefile(filename=tojsonfile_param, data=formatted_results)
            else:
                # Convert to dict for JSON
                temp_results = []
                for row in resultset:
                    row_dict = {columns[i]: row[i] for i in range(len(columns))}
                    temp_results.append(row_dict)
                oacommon.writefile(filename=tojsonfile_param, data=json.dumps(temp_results, default=str, indent=2))
            logger.info(f"Result saved to JSON file: {tojsonfile_param}")

        # Output data for propagation
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
    Executes INSERT/UPDATE/DELETE on PostgreSQL with data propagation

    Args:
        param: dict with:
            - pgdatabase: database name - supports {WALLET:key}, {ENV:var}
            - pgdbhost: host - supports {WALLET:key}, {ENV:var}
            - pgdbusername: username - supports {WALLET:key}, {ENV:var}
            - pgdbpassword: password - supports {WALLET:key}, {VAULT:key}
            - pgdbport: port - supports {ENV:var}
            - statement: SQL statement (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - printout: (optional) print result, default False
            - fail_on_zero: (optional) fail if 0 rows affected, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_data) with affected rows count

    Example YAML:
        # Simple UPDATE
        - name: activate_user
          module: oa-pg
          function: execute
          pgdatabase: "myapp"
          pgdbhost: "localhost"
          pgdbusername: "postgres"
          pgdbpassword: "{VAULT:db_password}"
          pgdbport: 5432
          statement: "UPDATE users SET active = true WHERE id = 123"
          printout: true

        # INSERT with credentials from vault
        - name: create_order
          module: oa-pg
          function: execute
          pgdatabase: "{ENV:DB_NAME}"
          pgdbhost: "{ENV:DB_HOST}"
          pgdbusername: "{WALLET:db_user}"
          pgdbpassword: "{VAULT:db_pass}"
          pgdbport: 5432
          statement: |
            INSERT INTO orders (user_id, total, status, created_at)
            VALUES (456, 99.99, 'pending', NOW())

        # DELETE with fail_on_zero
        - name: delete_expired_sessions
          module: oa-pg
          function: execute
          pgdatabase: "sessions"
          pgdbhost: "db-server"
          pgdbusername: "cleanup"
          pgdbpassword: "{VAULT:cleanup_pass}"
          pgdbport: 5432
          statement: "DELETE FROM sessions WHERE expires_at < NOW()"
          fail_on_zero: false
          printout: true

        # UPDATE with dynamic values from wallet
        - name: update_config
          module: oa-pg
          function: execute
          pgdatabase: "config"
          pgdbhost: "localhost"
          pgdbusername: "admin"
          pgdbpassword: "{VAULT:admin_pass}"
          pgdbport: 5432
          statement: "UPDATE settings SET value = '{WALLET:new_value}' WHERE key = 'api_endpoint'"

        # Bulk INSERT
        - name: insert_multiple_logs
          module: oa-pg
          function: execute
          pgdatabase: "logs"
          pgdbhost: "{ENV:LOG_DB_HOST}"
          pgdbusername: "{WALLET:log_user}"
          pgdbpassword: "{VAULT:log_pass}"
          pgdbport: 5432
          statement: |
            INSERT INTO access_logs (user_id, action, timestamp)
            VALUES 
              (1, 'login', NOW()),
              (2, 'logout', NOW()),
              (3, 'view_page', NOW())

        # UPDATE with JOIN
        - name: bulk_update_prices
          module: oa-pg
          function: execute
          pgdatabase: "ecommerce"
          pgdbhost: "prod-db"
          pgdbusername: "{WALLET:admin_user}"
          pgdbpassword: "{VAULT:admin_pass}"
          pgdbport: 5432
          statement: |
            UPDATE products p
            SET price = p.price * 1.1
            FROM categories c
            WHERE p.category_id = c.id
            AND c.name = 'Electronics'
          fail_on_zero: true

        # Statement from previous task
        - name: execute_dynamic_statement
          module: oa-pg
          function: execute
          pgdatabase: "mydb"
          pgdbhost: "localhost"
          pgdbusername: "user"
          pgdbpassword: "{VAULT:pass}"
          pgdbport: 5432
          # statement from previous task

        # Save result to JSON file
        - name: archive_old_data
          module: oa-pg
          function: execute
          pgdatabase: "archive"
          pgdbhost: "archive-db"
          pgdbusername: "{WALLET:archive_user}"
          pgdbpassword: "{VAULT:archive_pass}"
          pgdbport: 5432
          statement: "DELETE FROM old_records WHERE created_at < NOW() - INTERVAL '1 year'"
          tojsonfile: "/logs/archive_result.json"
          printout: true
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL EXECUTE")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If statement not specified, try to build from input
        if 'statement' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'statement' in prev_input:
                    param['statement'] = prev_input['statement']
                elif 'query' in prev_input:
                    param['statement'] = prev_input['query']
                # If input has 'rows', build dynamic INSERT
                elif 'rows' in prev_input and 'table' in param:
                    rows_data = prev_input['rows']
                    table_name = param['table']
                    if isinstance(rows_data, list) and len(rows_data) > 0:
                        # Generate multiple INSERTs (basic example)
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders (CRITICAL for password!)
        pgdatabase = oacommon.get_param(param, 'pgdatabase', wallet) or gdict.get('pgdatabase')
        pgdbhost = oacommon.get_param(param, 'pgdbhost', wallet) or gdict.get('pgdbhost')
        pgdbusername = oacommon.get_param(param, 'pgdbusername', wallet) or gdict.get('pgdbusername')
        pgdbpassword = oacommon.get_param(param, 'pgdbpassword', wallet) or gdict.get('pgdbpassword')
        pgdbport = oacommon.get_param(param, 'pgdbport', wallet) or gdict.get('pgdbport')
        statement = oacommon.get_param(param, 'statement', wallet) or gdict.get('statement')

        printout = param.get('printout', False)
        fail_on_zero = param.get('fail_on_zero', False)

        logger.info(f"Executing statement on {pgdbhost}:{pgdbport}/{pgdatabase}")
        logger.debug(f"Statement: {statement[:100]}..." if len(statement) > 100 else f"Statement: {statement}")

        rows_affected = executeStatement(
            pgdatabase=pgdatabase,
            pgdbhost=pgdbhost,
            pgdbpassword=pgdbpassword,
            pgdbport=pgdbport,
            pgdbusername=pgdbusername,
            statement=statement
        )

        logger.info(f"Statement affected {rows_affected} row(s)")

        # Optional: consider 0 rows as failure
        if fail_on_zero and rows_affected == 0:
            task_success = False
            error_msg = "No rows affected by statement"
            logger.warning(error_msg)

        if printout:
            print(f"Rows affected: {rows_affected}")

        # Save to JSON file if requested
        if oacommon.checkparam('tojsonfile', param):
            tojsonfile_param = oacommon.get_param(param, 'tojsonfile', wallet) or param.get('tojsonfile')
            result_json = {
                'rows_affected': rows_affected,
                'statement': statement,
                'database': pgdatabase
            }
            oacommon.writefile(filename=tojsonfile_param, data=json.dumps(result_json, indent=2))
            logger.info(f"Result saved to JSON file: {tojsonfile_param}")

        # Output data for propagation
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
    Helper for INSERT with data propagation from previous input

    Args:
        param: dict with:
            - pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport - support {WALLET:key}, {ENV:var}
            - table: table name - supports {WALLET:key}, {ENV:var}
            - data: (optional) dict or list of dicts to insert
            - input: (optional) data from previous task (if correctly formatted)
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_data)

    Example YAML:
        # Insert single row
        - name: insert_user
          module: oa-pg
          function: insert
          pgdatabase: "myapp"
          pgdbhost: "localhost"
          pgdbusername: "postgres"
          pgdbpassword: "{VAULT:db_password}"
          pgdbport: 5432
          table: "users"
          data:
            name: "John Doe"
            email: "john@example.com"
            age: 30
            active: true

        # Insert multiple rows
        - name: bulk_insert_products
          module: oa-pg
          function: insert
          pgdatabase: "{ENV:DB_NAME}"
          pgdbhost: "{ENV:DB_HOST}"
          pgdbusername: "{WALLET:db_user}"
          pgdbpassword: "{VAULT:db_pass}"
          pgdbport: 5432
          table: "products"
          data:
            - name: "Product A"
              price: 19.99
              stock: 100
            - name: "Product B"
              price: 29.99
              stock: 50
            - name: "Product C"
              price: 39.99
              stock: 75

        # Insert with values from wallet
        - name: insert_api_key
          module: oa-pg
          function: insert
          pgdatabase: "config"
          pgdbhost: "localhost"
          pgdbusername: "admin"
          pgdbpassword: "{VAULT:admin_pass}"
          pgdbport: 5432
          table: "api_keys"
          data:
            service_name: "{WALLET:service_name}"
            api_key: "{VAULT:api_key}"
            created_at: "NOW()"

        # Insert from previous task (e.g., after JSON transformation)
        - name: insert_transformed_data
          module: oa-pg
          function: insert
          pgdatabase: "warehouse"
          pgdbhost: "data-db"
          pgdbusername: "{WALLET:etl_user}"
          pgdbpassword: "{VAULT:etl_pass}"
          pgdbport: 5432
          table: "staging_data"
          # data from previous jsontransform task

        # Insert filtered results
        - name: insert_filtered_users
          module: oa-pg
          function: insert
          pgdatabase: "reports"
          pgdbhost: "reporting-db"
          pgdbusername: "{WALLET:report_user}"
          pgdbpassword: "{VAULT:report_pass}"
          pgdbport: 5432
          table: "active_users_report"
          # data from previous jsonfilter task

    Note: Uses parameterized queries for SQL injection protection
    """
    func_name = myself()
    logger.info(f"{func_name} - PostgreSQL INSERT helper")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Determine data to insert
        insert_data = None

        if 'data' in param:
            insert_data = param['data']
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'rows' in prev_input:
                    insert_data = prev_input['rows']
                else:
                    # Single dict = single row
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        pgdatabase = oacommon.get_param(param, 'pgdatabase', wallet) or gdict.get('pgdatabase')
        pgdbhost = oacommon.get_param(param, 'pgdbhost', wallet) or gdict.get('pgdbhost')
        pgdbusername = oacommon.get_param(param, 'pgdbusername', wallet) or gdict.get('pgdbusername')
        pgdbpassword = oacommon.get_param(param, 'pgdbpassword', wallet) or gdict.get('pgdbpassword')
        pgdbport = oacommon.get_param(param, 'pgdbport', wallet) or gdict.get('pgdbport')
        table_name = oacommon.get_param(param, 'table', wallet) or gdict.get('table')

        # Convert to list if it's a single dict
        if isinstance(insert_data, dict):
            insert_data = [insert_data]

        if not isinstance(insert_data, list) or len(insert_data) == 0:
            raise ValueError("Insert data must be a non-empty list of dicts")

        # Generate INSERT statement
        first_row = insert_data[0]
        columns = ', '.join(first_row.keys())

        # Use parameterization for security
        placeholders = ', '.join(['%s'] * len(first_row))
        statement = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        logger.info(f"Inserting {len(insert_data)} row(s) into {table_name}")
        logger.debug(f"Statement template: {statement}")

        # Connection
        conn = psycopg2.connect(
            host=pgdbhost,
            port=pgdbport,
            database=pgdatabase,
            user=pgdbusername,
            password=pgdbpassword
        )
        cur = conn.cursor()

        # Execute many for performance
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
