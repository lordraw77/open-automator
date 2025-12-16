from responses import logger
import oacommon
import inspect
import requests
import smtplib, ssl
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
    Invia un messaggio Telegram con bot API.

    Param obbligatori:
      - tokenid
      - chatid (lista di chat_id)
      - message
    Param opzionali:
      - printresponse (bool)
      - task_id
      - task_store
    """
    func_name = myself()
    logger.info("Sending Telegram notification")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        # SINTASSI CORRETTA: argomenti separati, non tupla + param=param
        if not oacommon.checkandloadparam(self, myself, 'tokenid', 'chatid', 'message', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        tokenid = gdict['tokenid']
        chatid = gdict['chatid']
        message = oacommon.effify(gdict['message'])

        logger.debug(f"Sending to {len(chatid)} chat(s)")

        for cid in chatid:
            send_text = (
                'https://api.telegram.org/bot' + tokenid +
                '/sendMessage?chat_id=' + cid +
                '&parse_mode=Markdown&text=' + message
            )
            response = requests.get(send_text)

            if response.status_code != 200:
                task_success = False
                error_msg = f"Telegram API error for chat {cid}: {response.status_code} {response.reason}"
                logger.error(error_msg)
            else:
                logger.info(f"Message sent successfully to chat {cid}")

            if oacommon.checkparam('printresponse', param):
                if param['printresponse']:
                    print(response.json())

        logger.info("Telegram notification completed")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"sendtelegramnotify failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success


@oacommon.trace
def sendmailbygmail(self, param):
    """
    Invia email tramite Gmail SMTP SSL.

    Param obbligatori:
      - senderemail
      - receiveremail
      - senderpassword
      - subject
    Param opzionali:
      - messagetext
      - messagehtml
      - task_id
      - task_store
    """
    func_name = myself()
    logger.info("Sending email via Gmail")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        # SINTASSI CORRETTA
        if not oacommon.checkandloadparam(
            self, myself, 'senderemail', 'receiveremail', 'senderpassword', 'subject', param=param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        senderemail = gdict['senderemail']
        receiveremail = gdict['receiveremail']
        password = gdict['senderpassword']
        subject = gdict['subject']

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = senderemail
        message["To"] = receiveremail

        text = ""
        html = ""

        if oacommon.checkparam('messagetext', param) and not oacommon.checkparam('messagehtml', param):
            text = oacommon.effify(param['messagetext'])
            part1 = MIMEText(text, "plain")
            message.attach(part1)
        elif oacommon.checkparam('messagehtml', param) and not oacommon.checkparam('messagetext', param):
            html = oacommon.effify(param['messagehtml'])
            part2 = MIMEText(html, "html")
            message.attach(part2)
        elif oacommon.checkparam('messagetext', param) and oacommon.checkparam('messagehtml', param):
            text = oacommon.effify(param['messagetext'])
            part1 = MIMEText(text, "plain")
            html = oacommon.effify(param['messagehtml'])
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
        else:
            raise ValueError("messagetext or messagehtml are required.")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(senderemail, password)
            server.sendmail(senderemail, receiveremail, message.as_string())

        logger.info(f"Email sent successfully to {receiveremail}")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"sendmailbygmail failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
