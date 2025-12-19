"""
Open-Automator Notify Module
Gestisce notifiche (Telegram, Email) con data propagation
Supporto per wallet, placeholder {WALLET:key}, {ENV:var} e {VAULT:key}
"""

import oacommon
import inspect
import requests
import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-notify')

gdict = {}

def setgdict(self, gdict_param):
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

myself = lambda: inspect.stack()[1][3]

@oacommon.trace
def sendtelegramnotify(self, param):
    """
    Invia un messaggio Telegram con bot API e data propagation

    Args:
        param: dict con:
            - tokenid: token del bot Telegram - supporta {WALLET:key}, {ENV:var}
            - chatid: lista di chat_id - supporta {WALLET:key}, {ENV:var}
            - message: messaggio da inviare (può venire da input precedente) - supporta {WALLET:key}, {ENV:var}
            - printresponse: (opzionale) stampa response
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con info sull'invio
    """
    func_name = myself()
    logger.info("Sending Telegram notification")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se message non è specificato, usa input dal task precedente
        if 'message' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # Cerca vari campi possibili
                if 'content' in prev_input:
                    param['message'] = prev_input['content']
                elif 'message' in prev_input:
                    param['message'] = prev_input['message']
                elif 'text' in prev_input:
                    param['message'] = prev_input['text']
                else:
                    # Converti tutto il dict in messaggio formattato
                    param['message'] = json.dumps(prev_input, indent=2)
                logger.info("Using message from previous task")
            elif isinstance(prev_input, str):
                param['message'] = prev_input
                logger.info("Using string from previous task as message")

        if not oacommon.checkandloadparam(self, myself, 'tokenid', 'chatid', 'message', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Usa get_param per supportare placeholder (IMPORTANTE per token sensibili!)
        tokenid = oacommon.get_param(param, 'tokenid', wallet) or gdict.get('tokenid')
        chatid_param = oacommon.get_param(param, 'chatid', wallet) or gdict.get('chatid')
        message = oacommon.get_param(param, 'message', wallet) or gdict.get('message')

        # Assicurati che chatid sia una lista
        if isinstance(chatid_param, str):
            chatid = [chatid_param]
        else:
            chatid = chatid_param

        logger.debug(f"Sending to {len(chatid)} chat(s)")
        logger.debug(f"Message length: {len(message)} chars")

        successful_sends = []
        failed_sends = []

        for cid in chatid:
            send_text = (
                'https://api.telegram.org/bot' + tokenid +
                '/sendMessage?chat_id=' + cid +
                '&parse_mode=Markdown&text=' + message
            )

            try:
                response = requests.get(send_text, timeout=10)

                if response.status_code != 200:
                    error_detail = f"Telegram API error for chat {cid}: {response.status_code} {response.reason}"
                    logger.error(error_detail)
                    failed_sends.append({
                        'chat_id': cid,
                        'error': error_detail,
                        'status_code': response.status_code
                    })
                else:
                    logger.info(f"Message sent successfully to chat {cid}")
                    successful_sends.append({
                        'chat_id': cid,
                        'response': response.json()
                    })

                if oacommon.checkparam('printresponse', param):
                    if param['printresponse']:
                        logger.info(f"Response: {response.json()}")

            except requests.exceptions.RequestException as e:
                error_detail = f"Connection error for chat {cid}: {str(e)}"
                logger.error(error_detail)
                failed_sends.append({
                    'chat_id': cid,
                    'error': error_detail
                })

        # Se almeno una chat ha fallito, considera il task come fallito
        if failed_sends:
            task_success = False
            error_msg = f"{len(failed_sends)} chat(s) failed"

        logger.info(f"Telegram notification completed: {len(successful_sends)} sent, {len(failed_sends)} failed")

        # Output data per propagation
        output_data = {
            'total_chats': len(chatid),
            'successful': len(successful_sends),
            'failed': len(failed_sends),
            'successful_chats': successful_sends,
            'failed_chats': failed_sends,
            'message_length': len(message)
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"sendtelegramnotify failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def sendmailbygmail(self, param):
    """
    Invia email tramite Gmail SMTP SSL con data propagation

    Args:
        param: dict con:
            - senderemail: email mittente - supporta {WALLET:key}, {ENV:var}
            - receiveremail: email destinatario - supporta {WALLET:key}, {ENV:var}
            - senderpassword: password mittente - supporta {WALLET:key}, {VAULT:key}
            - subject: oggetto email - supporta {WALLET:key}, {ENV:var}
            - messagetext: (opzionale) testo plain - supporta {WALLET:key}, {ENV:var}
            - messagehtml: (opzionale) testo HTML - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con info sull'invio
    """
    func_name = myself()
    logger.info("Sending email via Gmail")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se messagetext/messagehtml non specificati, usa input dal task precedente
        if 'messagetext' not in param and 'messagehtml' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # Cerca campo content
                if 'content' in prev_input:
                    param['messagetext'] = prev_input['content']
                # O converti tutto in JSON formattato
                else:
                    param['messagetext'] = json.dumps(prev_input, indent=2)
                logger.info("Using message content from previous task")
            elif isinstance(prev_input, str):
                param['messagetext'] = prev_input
                logger.info("Using string from previous task as message")

        if not oacommon.checkandloadparam(
            self, myself, 'senderemail', 'receiveremail', 'senderpassword', 'subject', param=param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Usa get_param per supportare placeholder (CRITICAMENTE IMPORTANTE per password!)
        senderemail = oacommon.get_param(param, 'senderemail', wallet) or gdict.get('senderemail')
        receiveremail = oacommon.get_param(param, 'receiveremail', wallet) or gdict.get('receiveremail')
        password = oacommon.get_param(param, 'senderpassword', wallet) or gdict.get('senderpassword')
        subject = oacommon.get_param(param, 'subject', wallet) or gdict.get('subject')

        logger.debug(f"From: {senderemail}")
        logger.debug(f"To: {receiveremail}")
        logger.debug(f"Subject: {subject}")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = senderemail
        message["To"] = receiveremail

        text = ""
        html = ""
        message_type = None

        if oacommon.checkparam('messagetext', param) and not oacommon.checkparam('messagehtml', param):
            text = oacommon.get_param(param, 'messagetext', wallet) or param.get('messagetext', '')
            part1 = MIMEText(text, "plain")
            message.attach(part1)
            message_type = "plain"
            logger.debug(f"Plain text message: {len(text)} chars")
        elif oacommon.checkparam('messagehtml', param) and not oacommon.checkparam('messagetext', param):
            html = oacommon.get_param(param, 'messagehtml', wallet) or param.get('messagehtml', '')
            part2 = MIMEText(html, "html")
            message.attach(part2)
            message_type = "html"
            logger.debug(f"HTML message: {len(html)} chars")
        elif oacommon.checkparam('messagetext', param) and oacommon.checkparam('messagehtml', param):
            text = oacommon.get_param(param, 'messagetext', wallet) or param.get('messagetext', '')
            part1 = MIMEText(text, "plain")
            html = oacommon.get_param(param, 'messagehtml', wallet) or param.get('messagehtml', '')
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            message_type = "multipart"
            logger.debug(f"Multipart message: plain={len(text)} chars, html={len(html)} chars")
        else:
            raise ValueError("messagetext or messagehtml are required.")

        context = ssl.create_default_context()

        logger.debug("Connecting to Gmail SMTP server...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(senderemail, password)
            logger.debug("SMTP login successful")
            server.sendmail(senderemail, receiveremail, message.as_string())

        logger.info(f"Email sent successfully to {receiveremail}")

        # Output data per propagation
        output_data = {
            'from': senderemail,
            'to': receiveremail,
            'subject': subject,
            'message_type': message_type,
            'text_length': len(text) if text else 0,
            'html_length': len(html) if html else 0,
            'sent': True
        }

    except smtplib.SMTPAuthenticationError as e:
        task_success = False
        error_msg = "SMTP Authentication failed - check email/password"
        logger.error(f"{error_msg}: {e}")
        logger.error("If using Gmail, ensure 'App Passwords' is configured")
    except smtplib.SMTPException as e:
        task_success = False
        error_msg = f"SMTP error: {str(e)}"
        logger.error(f"sendmailbygmail SMTP error: {e}", exc_info=True)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"sendmailbygmail failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def formatmessage(self, param):
    """
    Formatta un messaggio da dati strutturati (helper per notifiche)

    Args:
        param: dict con:
            - template: (opzionale) template del messaggio con placeholder {key} - supporta {WALLET:key}, {ENV:var}
            - data: (opzionale) dict con dati da formattare
            - format: (opzionale) 'json', 'text', 'markdown'
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, formatted_message)
    """
    func_name = myself()
    logger.info("Formatting message for notification")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Determina i dati da formattare
        data = None

        if 'data' in param:
            data = param['data']
        elif 'input' in param:
            data = param.get('input')
            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to format")

        # Formato (con supporto placeholder)
        format_type = oacommon.get_param(param, 'format', wallet) or param.get('format', 'text')

        formatted_message = None

        # Se c'è un template, usalo (con supporto placeholder nel template stesso!)
        if 'template' in param:
            template = oacommon.get_param(param, 'template', wallet) or param.get('template')
            if isinstance(data, dict):
                formatted_message = template.format(**data)
                logger.debug("Message formatted using template")
            else:
                formatted_message = template.format(data=data)

        # Altrimenti formatta secondo il tipo
        elif format_type == 'json':
            formatted_message = json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type == 'markdown':
            if isinstance(data, dict):
                lines = ['**Workflow Result:**', '']
                for key, value in data.items():
                    lines.append(f"• **{key}**: {value}")
                formatted_message = '\n'.join(lines)
            else:
                formatted_message = f"```{str(data)}```"
        else:  # text
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    lines.append(f"{key}: {value}")
                formatted_message = '\n'.join(lines)
            else:
                formatted_message = str(data)

        logger.info(f"Message formatted successfully ({format_type}): {len(formatted_message)} chars")

        # Output: il messaggio formattato
        output_data = {
            'content': formatted_message,
            'format': format_type,
            'length': len(formatted_message)
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"formatmessage failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data
