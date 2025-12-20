"""
Open-Automator Common Utilities
Funzioni condivise tra tutti i moduli con supporto logging
"""

import pprint
import inspect
import chardet
import paramiko
import logging
from logger_config import AutomatorLogger
import os
import re
from wallet import Wallet
# Logger per questo modulo
logger = AutomatorLogger.get_logger('oacommon')

gdict = {}


def trace(f):
    """Decorator per tracciare l'esecuzione delle funzioni"""
    def wrap(*args, **kwargs):
        if gdict.get('TRACE', False):
            logger.debug(f"TRACE: func={f.__name__}, args={args}, kwargs={kwargs}")
        return f(*args, **kwargs)
    return wrap


myself = lambda: inspect.stack()[1][3]

# Cache del wallet (caricato una volta sola)
_wallet_instance = None

def get_wallet():
    """Ottiene istanza del wallet (lazy loading)"""
    global _wallet_instance
    
    if _wallet_instance is None:
        try:
            wallet_password = os.environ.get('OA_WALLET_PASSWORD')
            if wallet_password:
                _wallet_instance = Wallet(wallet_file='wallet.enc', master_password=wallet_password)
                _wallet_instance.load_wallet()
                logger.debug(f"Wallet loaded: {len(_wallet_instance.secrets)} secrets")
            else:
                logger.warning("OA_WALLET_PASSWORD not set - wallet unavailable")
        except Exception as e:
            logger.error(f"Failed to load wallet: {e}")
            _wallet_instance = None
    
    return _wallet_instance


def effify(nonfstr):
    """
    Evalua f-string con interpolazione variabili da gdict e wallet
    Supporta:
    - {VARNAME} -> variabili da gdict
    - ${WALLET:key} -> variabili dal wallet cifrato
    - ${ENV:VAR} -> variabili ambiente
    """
    try:
        result = str(nonfstr)
        #print(f"DEBUG effify INPUT: {result}")
        
        # 1. PRIMA: Interpola {VARNAME} da gdict
        globals().update(gdict)
        result = eval(f'f"{result}"')
        #print(f"DEBUG after gdict eval: {result}")
        
        # 2. POI: Sostituisci ${WALLET:key}
        wallet_pattern = r'\$\{WALLET:(\w+)\}'
        wallet_matches = list(re.finditer(wallet_pattern, result))
        
        #print(f"DEBUG wallet matches: {len(wallet_matches)}")
        
        if wallet_matches:
            wallet = get_wallet()
            #print(f"DEBUG wallet loaded: {wallet is not None and wallet.loaded}")
            if wallet and wallet.loaded:
                for match in wallet_matches:
                    key = match.group(1)
                    try:
                        value = wallet.get_secret(key)
                        result = result.replace(match.group(0), str(value))
                        #print(f"DEBUG Wallet substitution: ${{WALLET:{key}}} -> ***")
                    except KeyError:
                        logger.warning(f"Wallet key not found: {key}")
            else:
                logger.warning("Wallet not available - skipping ${WALLET:...} substitution")
        
        # 3. INFINE: Sostituisci ${ENV:VAR}
        env_pattern = r'\$\{ENV:(\w+)\}'
        for match in re.finditer(env_pattern, result):
            var = match.group(1)
            value = os.environ.get(var)
            if value:
                result = result.replace(match.group(0), value)
                #print(f"DEBUG Env substitution: ${{ENV:{var}}} -> {value}")
        
        print(f"DEBUG effify OUTPUT: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to interpolate variable: '{nonfstr}' - {e}")
        return nonfstr





def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param


def checkandloadparam(self, modulename, *paramneed, param):
    """
    Verifica e carica parametri obbligatori nel gdict

    Args:
        self: istanza modulo
        modulename: nome modulo chiamante
        *paramneed: parametri obbligatori
        param: dizionario parametri attuali

    Returns:
        True se tutti i parametri sono presenti, False altrimenti
    """
    if self.gdict.get('DEBUG', False):
        logger.debug(f"Checking parameters for {modulename.__name__ if callable(modulename) else modulename}")
        logger.debug(f"Required: {paramneed}")
        logger.debug(f"Received: {list(param.keys())}")

    ret = True
    missing_params = []

    for par in paramneed:
        if par in param:
            self.gdict[par] = param.get(par)
        else:
            missing_params.append(par)
            ret = False

    if not ret:
        module_name = modulename.__name__ if callable(modulename) else modulename
        logger.error(f"Missing required parameters for {module_name}: {missing_params}")
        logger.error(f"Required parameters: {paramneed}")

    return ret


logstart = lambda x: logger.info(f"{x[:30]:.<30} start")
logend = lambda x: logger.info(f"{x[:30]:.<30} end")


@trace
def checkparam(paramname, param):
    """Verifica se un parametro opzionale è presente"""
    ret = paramname in param
    if ret:
        logger.debug(f"Optional parameter '{paramname}' found")
    return ret


@trace
def createSSHClient(server, port, user, password):
    """
    Crea e restituisce un client SSH connesso

    Args:
        server: hostname o IP del server
        port: porta SSH
        user: username
        password: password

    Returns:
        paramiko.SSHClient connesso
    """
    logger.info(f"Creating SSH connection to {user}@{server}:{port}")

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()

        # ATTENZIONE: AutoAddPolicy è insicuro, considera di usare RejectPolicy in produzione
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logger.warning("Using AutoAddPolicy for SSH - consider using known_hosts in production")

        client.connect(server, int(port), user, password, timeout=30)
        logger.info(f"SSH connection established to {server}")

        return client
    except paramiko.AuthenticationException:
        logger.error(f"SSH authentication failed for {user}@{server}")
        raise
    except paramiko.SSHException as e:
        logger.error(f"SSH connection error to {server}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create SSH client: {e}")
        raise


def sshremotecommand(server, port, user, password, commandtoexecute):
    """
    Esegue un comando su un server remoto via SSH

    Args:
        server: hostname o IP
        port: porta SSH
        user: username
        password: password
        commandtoexecute: comando da eseguire

    Returns:
        Output del comando come bytes
    """
    logger.info(f"Executing remote command on {server}")
    logger.debug(f"Command: {commandtoexecute}")

    ssh = None
    try:
        ssh = createSSHClient(server, port, user, password)

        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(commandtoexecute)
        ssh_stdin.flush()

        output = ssh_stdout.read()
        error = ssh_stderr.read()

        if error:
            logger.warning(f"Command stderr output: {error.decode('utf-8', errors='ignore')}")

        logger.info(f"Remote command executed successfully, output size: {len(output)} bytes")

        return output

    except Exception as e:
        logger.error(f"Failed to execute remote command: {e}")
        raise
    finally:
        if ssh:
            ssh.close()
            logger.debug("SSH connection closed")


@trace
def findenc(filename):
    """Rileva l'encoding di un file"""
    logger.debug(f"Detecting encoding for: {filename}")
    rawdata = open(filename, 'rb').read()
    result = chardet.detect(rawdata)
    encoding = result['encoding']
    logger.debug(f"Detected encoding: {encoding} (confidence: {result['confidence']})")
    return encoding


@trace
def writefile(filename, data):
    """
    Scrive dati in un file

    Args:
        filename: path del file
        data: contenuto da scrivere
    """
    logger.info(f"Writing to file: {filename}")
    logger.debug(f"Data size: {len(str(data))} characters")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"File written successfully: {filename}")
    except Exception as e:
        logger.error(f"Failed to write file {filename}: {e}")
        raise


@trace
def readfile(filename):
    """
    Legge il contenuto di un file con rilevamento automatico encoding

    Args:
        filename: path del file

    Returns:
        Contenuto del file come stringa
    """
    logger.info(f"Reading file: {filename}")

    try:
        encoding = findenc(filename)
        with open(filename, mode='r', encoding=encoding) as f:
            data = f.read()

        logger.info(f"File read successfully: {filename} ({len(data)} characters)")
        return data

    except Exception as e:
        logger.error(f"Failed to read file {filename}: {e}")
        raise


@trace
def appendfile(filename, data):
    """
    Appende dati a un file esistente

    Args:
        filename: path del file
        data: contenuto da appendere
    """
    logger.info(f"Appending to file: {filename}")
    logger.debug(f"Data size: {len(str(data))} characters")

    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"Data appended successfully to: {filename}")
    except Exception as e:
        logger.error(f"Failed to append to file {filename}: {e}")
        raise

# def get_param(param_dict, key, wallet=None):
#     from wallet import resolve_placeholders

#     if key not in param_dict:
#         return None

#     value = param_dict[key]

#     if not isinstance(value, str):
#         return value

#     # Risolvi placeholder WALLET/ENV/VAULT
#     if wallet and ('{WALLET:' in value or '{VAULT:' in value or '{ENV:' in value):
#         value = resolve_placeholders(value, wallet)

#     # Risolvi placeholder variabili workflow ${VARNAME}
#     if "${" in value and "}" in value:
#         import re
#         pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
        
#         def replace_var(match):
#             varname = match.group(1)
#             # Cerca nel gdict globale
#             if varname in gdict:
#                 resolved = gdict[varname]
#                 logger.debug(f"Resolved ${{{varname}}} -> {resolved}")
#                 return str(resolved)
#             else:
#                 logger.warning(f"Variable ${{{varname}}} not found in workflow variables")
#                 return match.group(0)  # Lascia invariato
        
#         value = re.sub(pattern, replace_var, value)
    

#     # Risolvi variabili gdict con effify (retrocompatibilita)
#     if value and ('f"' in str(value) or "f'" in str(value)):
#         value = effify(value)

#     return value

def get_param(paramdict, key, wallet=None):
    """
    Ottiene parametro con risoluzione placeholder WALLET/ENV/VAULT e variabili gdict
    Supporta stringhe e liste di stringhe
    """
    from wallet import resolve_placeholders
    
    if key not in paramdict:
        return None
    
    value = paramdict[key]
    
    # ✅ AGGIUNGI: Gestione liste
    if isinstance(value, list):
        resolved_list = []
        for item in value:
            if isinstance(item, str):
                resolved_item = _resolve_string_value(item, wallet)
                resolved_list.append(resolved_item)
            else:
                resolved_list.append(item)
        return resolved_list
    
    # Gestione stringhe
    if not isinstance(value, str):
        return value
    
    return _resolve_string_value(value, wallet)


def _resolve_string_value(value, wallet=None):
    """
    Helper per risolvere placeholder in una stringa
    """
    from wallet import resolve_placeholders
    
    if not isinstance(value, str):
        return value
    
    # 1. Risolvi placeholder WALLET/ENV/VAULT
    if wallet and ("WALLET" in value or "VAULT" in value or "ENV" in value):
        value = resolve_placeholders(value, wallet)
    
    # 2. Risolvi placeholder variabili workflow ${VARNAME}
    if "${" in value and "}" in value:
        import re
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
        
        def replace_var(match):
            varname = match.group(1)
            # Cerca nel gdict globale
            if varname in gdict:
                resolved = gdict[varname]
                logger.debug(f"Resolved ${{{varname}}} -> {resolved}")
                return str(resolved)
            else:
                logger.warning(f"Variable ${{{varname}}} not found in workflow variables")
                return match.group(0)  # Lascia invariato
        
        value = re.sub(pattern, replace_var, value)
    
    # 3. Risolvi variabili gdict con effify (retrocompatibilità)
    if value and ("{" in str(value) or "}" in str(value)):
        value = effify(value)
    
    return value

def resolve_param(param_dict, key, default=None, wallet=None):
    value = get_param(param_dict, key, wallet)
    return value if value is not None else default
