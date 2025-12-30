"""
Open-Automator JSON Module

Manages advanced JSON data operations with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import oacommon
import inspect
import json
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.getlogger("oa-json")

gdict = {}

myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdictparam):
    """Sets the global dictionary"""
    global gdict
    gdict = gdictparam
    self.gdict = gdictparam

@oacommon.trace
def jsonfilter(self, param):
    """
    Filters elements in a JSON array based on conditions

    Args:
        param (dict) with:
            - data: optional JSON data (can use input from previous task)
            - field: field to filter on - supports {WALLET:key}, {ENV:var}
            - operator: ==, !=, >, <, >=, <=, contains, in, exists, not_exists
            - value: comparison value - supports {WALLET:key}, {ENV:var}
            - case_sensitive: optional (default: True)
            - saveonvar: optional save result to variable
            - input: optional data from previous task
            - workflowcontext: optional workflow context
            - taskid: optional unique task id
            - taskstore: optional TaskResultStore instance

    Returns:
        tuple (success, filtered_data)

    Example YAML:
        # Filter users by age
        - name: filter_adults
          module: oa-json
          function: jsonfilter
          data:
            - {name: "Alice", age: 30}
            - {name: "Bob", age: 25}
            - {name: "Charlie", age: 35}
          field: age
          operator: ">"
          value: 26
          # Output: [{name: "Alice", age: 30}, {name: "Charlie", age: 35}]

        # Filter with contains operator
        - name: filter_emails
          module: oa-json
          function: jsonfilter
          field: email
          operator: contains
          value: "@gmail.com"
          case_sensitive: false

        # Filter from previous task
        - name: filter_active_users
          module: oa-json
          function: jsonfilter
          # data from previous API call or database query
          field: status
          operator: "=="
          value: "active"

        # Check field existence
        - name: filter_has_address
          module: oa-json
          function: jsonfilter
          field: address
          operator: exists
          value: true

        # Filter with wallet value
        - name: filter_by_category
          module: oa-json
          function: jsonfilter
          field: category
          operator: "=="
          value: "{WALLET:target_category}"
    """
    funcname = myself()
    logger.info("JSON Filter operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation: retrieve JSON data
        data = None
        if "data" in param:
            data = param["data"]
            # If it's JSON string, parse it
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                # Look for common fields
                if "json" in previnput:
                    data = previnput["json"]
                elif "data" in previnput:
                    data = previnput["data"]
                elif "rows" in previnput:
                    data = previnput["rows"]
                elif "content" in previnput:
                    # Might be JSON string
                    content = previnput["content"]
                    if isinstance(content, str):
                        data = json.loads(content)
                    else:
                        data = content
                else:
                    # Use all input
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to filter: provide 'data' or pipe from previous task")

        if not isinstance(data, list):
            raise ValueError("Filter operation requires array/list data")

        # Validate parameters
        requiredparams = ["field", "operator", "value"]
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        # Extract parameters with placeholder support
        field = oacommon.getparam(param, "field", wallet) or gdict.get("field")
        operator = oacommon.getparam(param, "operator", wallet) or gdict.get("operator")
        value = oacommon.getparam(param, "value", wallet)
        if value is None:
            value = param.get("value")

        case_sensitive = param.get("case_sensitive", True)

        logger.info(f"Filter: {field} {operator} {value}")
        logger.debug(f"Input data: {len(data)} items")

        # Apply filter
        filtered = []

        for item in data:
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-dict item: {type(item)}")
                continue

            item_value = item.get(field)

            # Convert for case-insensitive comparison if needed
            if not case_sensitive and isinstance(item_value, str) and isinstance(value, str):
                item_value = item_value.lower()
                compare_value = value.lower()
            else:
                compare_value = value

            # Apply operator
            match = False

            try:
                if operator == "==":
                    match = item_value == compare_value
                elif operator == "!=":
                    match = item_value != compare_value
                elif operator == ">":
                    match = float(item_value) > float(compare_value)
                elif operator == "<":
                    match = float(item_value) < float(compare_value)
                elif operator == ">=":
                    match = float(item_value) >= float(compare_value)
                elif operator == "<=":
                    match = float(item_value) <= float(compare_value)
                elif operator == "contains":
                    match = compare_value in str(item_value)
                elif operator == "in":
                    # value must be a list
                    if isinstance(compare_value, str):
                        compare_value = json.loads(compare_value)
                    match = item_value in compare_value
                elif operator == "exists":
                    match = field in item
                elif operator == "not_exists":
                    match = field not in item
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

                if match:
                    filtered.append(item)

            except (ValueError, TypeError) as e:
                logger.warning(f"Comparison error for item {item}: {e}")
                continue

        logger.info(f"Filtered: {len(data)} -> {len(filtered)} items")

        # Save to variable if requested
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = filtered
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "filtered": filtered,
            "count": len(filtered),
            "original_count": len(data),
            "filter": {
                "field": field,
                "operator": operator,
                "value": value
            }
        }

    except json.JSONDecodeError as e:
        tasksuccess = False
        errormsg = f"Invalid JSON: {str(e)}"
        logger.error(errormsg)

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON filter failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsonextract(self, param):
    """
    Extracts specific fields from JSON objects

    Args:
        param (dict) with:
            - data: optional JSON data (can use input)
            - fields: list of fields to extract - supports {WALLET:key}, {ENV:var}
            - flatten: optional flatten nested objects (default: False)
            - keep_nulls: optional keep null fields (default: False)
            - saveonvar: optional save result
            - input: optional data from previous task
            - taskid, taskstore, workflowcontext

    Returns:
        tuple (success, extracted_data)

    Example YAML:
        # Extract specific fields from array
        - name: extract_user_info
          module: oa-json
          function: jsonextract
          data:
            - {name: "Alice", age: 30, city: "Rome", country: "Italy"}
            - {name: "Bob", age: 25, city: "Milan", country: "Italy"}
          fields:
            - name
            - city
          # Output: [{name: "Alice", city: "Rome"}, {name: "Bob", city: "Milan"}]

        # Extract with dot notation for nested fields
        - name: extract_nested
          module: oa-json
          function: jsonextract
          data:
            user:
              name: "Alice"
              email: "alice@example.com"
              address:
                city: "Rome"
          fields:
            - user.name
            - user.address.city
          flatten: true
          # Output: {"user.name": "Alice", "user.address.city": "Rome"}

        # Extract from previous task
        - name: extract_from_api
          module: oa-json
          function: jsonextract
          # data from previous API call
          fields: "id,name,email"  # comma-separated string also supported

        # Keep null values
        - name: extract_with_nulls
          module: oa-json
          function: jsonextract
          fields:
            - name
            - optional_field
          keep_nulls: true
    """
    funcname = myself()
    logger.info("JSON Extract operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "json" in previnput:
                    data = previnput["json"]
                elif "filtered" in previnput:
                    data = previnput["filtered"]
                elif "data" in previnput:
                    data = previnput["data"]
                else:
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to extract from")

        # Validate parameters
        if not oacommon.checkandloadparam(self, myself, ["fields"], param=param):
            raise ValueError(f"Missing required parameter 'fields' for {funcname}")

        fields = param.get("fields")

        # Support comma-separated string
        if isinstance(fields, str):
            # Resolve placeholder if present
            fields = oacommon.getparam(param, "fields", wallet) or fields
            fields = [f.strip() for f in fields.split(",")]

        flatten = param.get("flatten", False)
        keep_nulls = param.get("keep_nulls", False)

        logger.info(f"Extracting fields: {fields}")
        logger.debug(f"Flatten: {flatten}, Keep nulls: {keep_nulls}")

        # Extract fields
        extracted = None

        if isinstance(data, dict):
            # Single object
            result = {}
            for field in fields:
                # Support dot notation for nested fields
                if "." in field and flatten:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        if isinstance(value, dict):
                            value = value.get(part)
                        else:
                            value = None
                            break
                else:
                    value = data.get(field)

                if value is not None or keep_nulls:
                    result[field] = value

            extracted = result

        elif isinstance(data, list):
            # Array of objects
            results = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                result = {}
                for field in fields:
                    if "." in field and flatten:
                        parts = field.split(".")
                        value = item
                        for part in parts:
                            if isinstance(value, dict):
                                value = value.get(part)
                            else:
                                value = None
                                break
                    else:
                        value = item.get(field)

                    if value is not None or keep_nulls:
                        result[field] = value

                results.append(result)

            extracted = results

        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        logger.info(f"Extraction completed successfully")

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = extracted
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "extracted": extracted,
            "fields": fields,
            "count": len(extracted) if isinstance(extracted, list) else 1
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON extract failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsontransform(self, param):
    """
    Transforms JSON data by applying mapping and transformations

    Args:
        param (dict) with:
            - data: optional JSON data (can use input)
            - mapping: dict with {new_field: old_field} or {new_field: "function:old_field"}
            - functions: optional dict with custom functions
            - add_fields: optional dict with new static fields
            - remove_fields: optional list of fields to remove
            - saveonvar: optional
            - input: optional data from previous task

    Returns:
        tuple (success, transformed_data)

    Example YAML:
        # Rename fields
        - name: rename_user_fields
          module: oa-json
          function: jsontransform
          data:
            first_name: "Alice"
            last_name: "Smith"
            age: 30
          mapping:
            name: first_name
            surname: last_name
            years: age
          # Output: {name: "Alice", surname: "Smith", years: 30}

        # Transform with built-in functions
        - name: transform_case
          module: oa-json
          function: jsontransform
          mapping:
            NAME: "upper:name"
            email_lower: "lower:email"
            age_int: "int:age"
          # Built-in functions: upper, lower, int, float, str, bool, strip

        # Add static fields
        - name: add_metadata
          module: oa-json
          function: jsontransform
          add_fields:
            source: "import"
            import_date: "2025-12-30"
            version: 1

        # Remove unwanted fields
        - name: cleanup_data
          module: oa-json
          function: jsontransform
          remove_fields:
            - internal_id
            - temp_field
            - _metadata

        # Complex transformation
        - name: transform_users
          module: oa-json
          function: jsontransform
          data:
            - {first_name: "alice", email: "ALICE@EXAMPLE.COM", age: "30"}
          mapping:
            full_name: "upper:first_name"
            email: "lower:email"
            age: "int:age"
          add_fields:
            status: "active"
          remove_fields:
            - first_name
    """
    funcname = myself()
    logger.info("JSON Transform operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "extracted" in previnput:
                    data = previnput["extracted"]
                elif "filtered" in previnput:
                    data = previnput["filtered"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to transform")

        mapping = param.get("mapping", {})
        add_fields = param.get("add_fields", {})
        remove_fields = param.get("remove_fields", [])

        logger.info(f"Mapping: {len(mapping)} fields")
        if add_fields:
            logger.debug(f"Adding {len(add_fields)} static fields")
        if remove_fields:
            logger.debug(f"Removing {len(remove_fields)} fields")

        # Built-in transformation functions
        transform_functions = {
            "upper": lambda x: str(x).upper() if x else x,
            "lower": lambda x: str(x).lower() if x else x,
            "int": lambda x: int(x) if x else 0,
            "float": lambda x: float(x) if x else 0.0,
            "str": lambda x: str(x) if x is not None else "",
            "bool": lambda x: bool(x),
            "strip": lambda x: str(x).strip() if x else x,
        }

        # Add custom functions if provided
        custom_functions = param.get("functions", {})

        def transform_item(item):
            """Transform a single item"""
            if not isinstance(item, dict):
                return item

            result = {}

            # Apply mapping
            for new_field, old_field in mapping.items():
                if isinstance(old_field, str):
                    # Check if there's a function to apply
                    if ":" in old_field:
                        func_name, field_name = old_field.split(":", 1)
                        value = item.get(field_name)

                        if func_name in transform_functions:
                            try:
                                value = transform_functions[func_name](value)
                            except Exception as e:
                                logger.warning(f"Transform function {func_name} failed: {e}")
                    else:
                        value = item.get(old_field)

                    result[new_field] = value

            # Copy unmapped fields (if not in remove_fields)
            for key, value in item.items():
                if key not in remove_fields and key not in mapping.values():
                    # Only if not already present in result
                    if key not in result:
                        result[key] = value

            # Add static fields
            for key, value in add_fields.items():
                # Resolve placeholder in value
                if isinstance(value, str):
                    value = oacommon.getparam(f"{key}={value}", key, wallet) or value
                result[key] = value

            # Remove specified fields
            for field in remove_fields:
                result.pop(field, None)

            return result

        # Transform data
        if isinstance(data, dict):
            transformed = transform_item(data)
        elif isinstance(data, list):
            transformed = [transform_item(item) for item in data if isinstance(item, dict)]
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        logger.info("Transformation completed successfully")

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = transformed
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "transformed": transformed,
            "count": len(transformed) if isinstance(transformed, list) else 1
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON transform failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsonmerge(self, param):
    """
    Merges multiple JSON objects/arrays

    Args:
        param (dict) with:
            - sources: list of keys from workflowcontext or list of direct data
            - merge_type: "dict" (merge objects), "array" (concatenate arrays), "deep" (deep merge)
            - overwrite: optional for dict merge (default: True)
            - unique: optional remove duplicates in array merge (default: False)
            - saveonvar: optional
            - input: optional data from previous task (added to merge)
            - workflowcontext: optional workflow context

    Returns:
        tuple (success, merged_data)

    Example YAML:
        # Merge dict objects
        - name: merge_configs
          module: oa-json
          function: jsonmerge
          sources:
            - task_config_base
            - task_config_override
          merge_type: dict
          overwrite: true
          # Later values overwrite earlier ones

        # Concatenate arrays
        - name: merge_user_lists
          module: oa-json
          function: jsonmerge
          sources:
            - users_from_db
            - users_from_api
          merge_type: array
          unique: true
          # Removes duplicate entries

        # Deep merge nested objects
        - name: deep_merge_settings
          module: oa-json
          function: jsonmerge
          sources:
            - {db: {host: "localhost", port: 5432}}
            - {db: {user: "admin"}, cache: {enabled: true}}
          merge_type: deep
          # Output: {db: {host: "localhost", port: 5432, user: "admin"}, cache: {enabled: true}}

        # Merge with input from previous task
        - name: merge_with_previous
          module: oa-json
          function: jsonmerge
          # input from previous task automatically included
          sources:
            - static_data
          merge_type: dict
    """
    funcname = myself()
    logger.info("JSON Merge operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")
        merge_type = param.get("merge_type", "dict")
        overwrite = param.get("overwrite", True)
        unique = param.get("unique", False)

        # Collect data to merge
        data_list = []

        # From sources
        if "sources" in param:
            sources = param["sources"]
            workflowcontext = param.get("workflowcontext")

            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, str) and workflowcontext:
                        # Retrieve from workflowcontext
                        data = workflowcontext.get_task_output(source)
                        if data:
                            data_list.append(data)
                    else:
                        # Direct data
                        data_list.append(source)

        # Add input if present
        if "input" in param:
            previnput = param.get("input")
            if previnput:
                data_list.append(previnput)
                logger.info("Including input in merge")

        if len(data_list) < 2:
            raise ValueError("Need at least 2 data sources to merge")

        logger.info(f"Merging {len(data_list)} sources (type: {merge_type})")

        # Merge based on type
        merged = None

        if merge_type == "dict":
            # Merge dicts
            merged = {}
            for data in data_list:
                if isinstance(data, dict):
                    if overwrite:
                        merged.update(data)
                    else:
                        # Don't overwrite existing keys
                        for key, value in data.items():
                            if key not in merged:
                                merged[key] = value
                else:
                    logger.warning(f"Skipping non-dict data in dict merge: {type(data)}")

        elif merge_type == "array":
            # Concatenate arrays
            merged = []
            for data in data_list:
                if isinstance(data, list):
                    merged.extend(data)
                elif isinstance(data, dict):
                    merged.append(data)
                else:
                    logger.warning(f"Skipping incompatible data in array merge: {type(data)}")

            # Remove duplicates if requested
            if unique:
                # For dicts use JSON string as key
                seen = set()
                unique_merged = []
                for item in merged:
                    item_str = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                    if item_str not in seen:
                        seen.add(item_str)
                        unique_merged.append(item)
                merged = unique_merged
                logger.debug(f"Removed {len(data_list) - len(merged)} duplicates")

        elif merge_type == "deep":
            # Recursive deep merge for nested dicts
            def deep_merge(dict1, dict2):
                result = dict1.copy()
                for key, value in dict2.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result

            merged = {}
            for data in data_list:
                if isinstance(data, dict):
                    merged = deep_merge(merged, data)
                else:
                    logger.warning(f"Skipping non-dict data in deep merge: {type(data)}")

        else:
            raise ValueError(f"Unsupported merge_type: {merge_type}")

        logger.info(f"Merge completed successfully")

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = merged
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "merged": merged,
            "sources_count": len(data_list),
            "merge_type": merge_type
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON merge failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsonaggregate(self, param):
    """
    Aggregates JSON data (sum, avg, count, min, max, group)

    Args:
        param (dict) with:
            - data: optional JSON array data (can use input)
            - operation: sum, avg, count, min, max, group
            - field: field to aggregate on - supports {WALLET:key}, {ENV:var}
            - group_by: optional field for grouping
            - saveonvar: optional
            - input: optional data from previous task

    Returns:
        tuple (success, aggregated_data)

    Example YAML:
        # Count items
        - name: count_users
          module: oa-json
          function: jsonaggregate
          data:
            - {name: "Alice", age: 30}
            - {name: "Bob", age: 25}
          operation: count
          # Output: 2

        # Sum values
        - name: total_sales
          module: oa-json
          function: jsonaggregate
          data:
            - {product: "A", amount: 100}
            - {product: "B", amount: 200}
            - {product: "C", amount: 150}
          operation: sum
          field: amount
          # Output: 450

        # Average with grouping
        - name: avg_age_by_department
          module: oa-json
          function: jsonaggregate
          data:
            - {name: "Alice", age: 30, dept: "IT"}
            - {name: "Bob", age: 25, dept: "IT"}
            - {name: "Charlie", age: 35, dept: "Sales"}
          operation: avg
          field: age
          group_by: dept
          # Output: {"IT": 27.5, "Sales": 35}

        # Group by category
        - name: group_products
          module: oa-json
          function: jsonaggregate
          operation: group
          group_by: category
          # Groups all items by category field

        # Min/Max
        - name: price_range
          module: oa-json
          function: jsonaggregate
          field: price
          operation: min
          # Find minimum price
    """
    funcname = myself()
    logger.info("JSON Aggregate operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "filtered" in previnput:
                    data = previnput["filtered"]
                elif "transformed" in previnput:
                    data = previnput["transformed"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    # Look for array inside input
                    for key, value in previnput.items():
                        if isinstance(value, list):
                            data = value
                            break
            elif isinstance(previnput, list):
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to aggregate")

        if not isinstance(data, list):
            raise ValueError("Aggregate operation requires array data")

        # Validate parameters
        requiredparams = ["operation"]
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        operation = oacommon.getparam(param, "operation", wallet) or gdict.get("operation")
        field = oacommon.getparam(param, "field", wallet) or param.get("field")
        group_by = oacommon.getparam(param, "group_by", wallet) or param.get("group_by")

        logger.info(f"Operation: {operation}, Field: {field}, Group by: {group_by}")

        result = None

        if operation == "count":
            if group_by:
                # Count by group
                counts = {}
                for item in data:
                    if isinstance(item, dict):
                        group_value = item.get(group_by, "null")
                        counts[str(group_value)] = counts.get(str(group_value), 0) + 1
                result = counts
            else:
                result = len(data)

        elif operation in ["sum", "avg", "min", "max"]:
            if not field:
                raise ValueError(f"Field is required for {operation} operation")

            if group_by:
                # Aggregate by group
                groups = {}
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    group_value = str(item.get(group_by, "null"))
                    field_value = item.get(field)

                    if field_value is not None:
                        if group_value not in groups:
                            groups[group_value] = []
                        try:
                            groups[group_value].append(float(field_value))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping non-numeric value: {field_value}")

                # Calculate aggregation for each group
                result = {}
                for group, values in groups.items():
                    if values:
                        if operation == "sum":
                            result[group] = sum(values)
                        elif operation == "avg":
                            result[group] = sum(values) / len(values)
                        elif operation == "min":
                            result[group] = min(values)
                        elif operation == "max":
                            result[group] = max(values)

            else:
                # Aggregate on entire dataset
                values = []
                for item in data:
                    if isinstance(item, dict):
                        field_value = item.get(field)
                        if field_value is not None:
                            try:
                                values.append(float(field_value))
                            except (ValueError, TypeError):
                                logger.warning(f"Skipping non-numeric value: {field_value}")

                if values:
                    if operation == "sum":
                        result = sum(values)
                    elif operation == "avg":
                        result = sum(values) / len(values)
                    elif operation == "min":
                        result = min(values)
                    elif operation == "max":
                        result = max(values)
                else:
                    result = 0

        elif operation == "group":
            # Group elements
            if not group_by:
                raise ValueError("group_by is required for group operation")

            groups = {}
            for item in data:
                if isinstance(item, dict):
                    group_value = str(item.get(group_by, "null"))
                    if group_value not in groups:
                        groups[group_value] = []
                    groups[group_value].append(item)

            result = groups

        else:
            raise ValueError(f"Unsupported operation: {operation}")

        logger.info(f"Aggregation completed: {operation}")

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = result
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "result": result,
            "operation": operation,
            "field": field,
            "group_by": group_by,
            "input_count": len(data)
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON aggregate failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsonvalidate(self, param):
    """
    Validates JSON against a JSON Schema

    Args:
        param (dict) with:
            - data: optional JSON data (can use input)
            - schema: JSON Schema for validation
            - strict: optional fail on validation error (default: True)
            - saveonvar: optional
            - input: optional data from previous task

    Returns:
        tuple (success, validation_result)

    Example YAML:
        # Validate user data
        - name: validate_user
          module: oa-json
          function: jsonvalidate
          data:
            name: "Alice"
            email: "alice@example.com"
            age: 30
          schema:
            type: object
            required:
              - name
              - email
            properties:
              name:
                type: string
              email:
                type: string
                format: email
              age:
                type: integer
                minimum: 0
          strict: true

        # Validate array of items
        - name: validate_products
          module: oa-json
          function: jsonvalidate
          schema:
            type: array
            items:
              type: object
              required:
                - id
                - name
                - price
              properties:
                id:
                  type: integer
                name:
                  type: string
                price:
                  type: number
                  minimum: 0

        # Non-strict validation (doesn't fail on error)
        - name: check_optional_fields
          module: oa-json
          function: jsonvalidate
          schema:
            type: object
            properties:
              optional_field:
                type: string
          strict: false
          # Continues even if validation fails

    Note: Requires jsonschema library: pip install jsonschema
    """
    funcname = myself()
    logger.info("JSON Validate operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        # Optional import of jsonschema
        try:
            import jsonschema
            from jsonschema import validate, ValidationError
        except ImportError:
            raise ImportError("jsonschema library not installed. Run: pip install jsonschema")

        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "json" in previnput:
                    data = previnput["json"]
                elif "transformed" in previnput:
                    data = previnput["transformed"]
                else:
                    data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)
            else:
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to validate")

        if not oacommon.checkandloadparam(self, myself, ["schema"], param=param):
            raise ValueError(f"Missing required parameter 'schema' for {funcname}")

        schema = param.get("schema")
        strict = param.get("strict", True)

        logger.info("Validating JSON against schema")

        # Validate
        valid = True
        errors = []

        try:
            validate(instance=data, schema=schema)
            logger.info("✓ JSON validation passed")

        except ValidationError as e:
            valid = False
            errors.append({
                "message": e.message,
                "path": list(e.path),
                "validator": e.validator
            })
            logger.warning(f"✗ JSON validation failed: {e.message}")

            if strict:
                tasksuccess = False
                errormsg = f"JSON validation failed: {e.message}"

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = {"valid": valid, "errors": errors}
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "valid": valid,
            "errors": errors,
            "data": data,
            "strict_mode": strict
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON validate failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata

@oacommon.trace
def jsonsort(self, param):
    """
    Sorts JSON array by field

    Args:
        param (dict) with:
            - data: optional JSON array data (can use input)
            - sort_by: field for sorting - supports {WALLET:key}, {ENV:var}
            - reverse: optional descending order (default: False)
            - numeric: optional sort as numbers (default: auto-detect)
            - saveonvar: optional
            - input: optional data from previous task

    Returns:
        tuple (success, sorted_data)

    Example YAML:
        # Sort by name (alphabetical)
        - name: sort_users_by_name
          module: oa-json
          function: jsonsort
          data:
            - {name: "Charlie", age: 35}
            - {name: "Alice", age: 30}
            - {name: "Bob", age: 25}
          sort_by: name
          # Output: [{name: "Alice"...}, {name: "Bob"...}, {name: "Charlie"...}]

        # Sort by age (numeric, descending)
        - name: sort_by_age_desc
          module: oa-json
          function: jsonsort
          sort_by: age
          reverse: true
          numeric: true
          # Output: Oldest to youngest

        # Sort from previous filter task
        - name: sort_filtered_results
          module: oa-json
          function: jsonsort
          # data from previous jsonfilter task
          sort_by: created_date
          reverse: true

        # Auto-detect numeric sorting
        - name: sort_by_price
          module: oa-json
          function: jsonsort
          sort_by: price
          # Automatically detects if price is numeric

        # Sort with environment variable
        - name: sort_dynamic
          module: oa-json
          function: jsonsort
          sort_by: "{ENV:SORT_FIELD}"
          reverse: false
    """
    funcname = myself()
    logger.info("JSON Sort operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "filtered" in previnput:
                    data = previnput["filtered"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    # Look for array
                    for key, value in previnput.items():
                        if isinstance(value, list):
                            data = value
                            break
            elif isinstance(previnput, list):
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to sort")

        if not isinstance(data, list):
            raise ValueError("Sort operation requires array data")

        if not oacommon.checkandloadparam(self, myself, ["sort_by"], param=param):
            raise ValueError(f"Missing required parameter 'sort_by' for {funcname}")

        sort_by = oacommon.getparam(param, "sort_by", wallet) or gdict.get("sort_by")
        reverse = param.get("reverse", False)
        numeric = param.get("numeric", None)

        logger.info(f"Sorting by: {sort_by}, Reverse: {reverse}")

        # Determine if sorting as number
        if numeric is None:
            # Auto-detect: check first value
            for item in data:
                if isinstance(item, dict):
                    value = item.get(sort_by)
                    if value is not None:
                        numeric = isinstance(value, (int, float))
                        break

        # Sort
        def sort_key(item):
            if isinstance(item, dict):
                value = item.get(sort_by)
                if value is None:
                    return float('inf') if numeric else ''
                if numeric:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return float('inf')
                return str(value).lower()
            return item

        sorted_data = sorted(data, key=sort_key, reverse=reverse)

        logger.info(f"Sorted {len(sorted_data)} items")

        # Save to variable
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = sorted_data
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "sorted": sorted_data,
            "count": len(sorted_data),
            "sort_by": sort_by,
            "reverse": reverse,
            "numeric": numeric
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON sort failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata