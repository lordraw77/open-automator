import oacommon 
import inspect
import requests
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-notify')

gdict={}

def setgdict(self,gdict):
     self.gdict=gdict

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
    oacommon.logstart(func_name)

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(self, myself(), ('tokenid', 'chatid', 'message'), param):
            raise ValueError(f"Missing required parameters for {func_name}")

        tokenid = gdict['tokenid']
        chatid = gdict['chatid']
        message = oacommon.effify(gdict['message'])

        for cid in chatid:
            send_text = (
                'https://api.telegram.org/bot' + tokenid +
                '/sendMessage?chat_id=' + cid +
                '&parse_mode=Markdown&text=' + message
            )
            response = requests.get(send_text)

            # opzionale: puoi considerare status != 200 come failure
            if response.status_code != 200:
                task_success = False
                error_msg = f"Telegram API error for chat {cid}: {response.status_code} {response.reason}"

            if oacommon._checkparam('printresponse', param):
                if param['printresponse']:
                    print(response.json())

        oacommon.logend(func_name)

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
    oacommon.logstart(func_name)

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(
            self, myself(),
            ('senderemail', 'receiveremail', 'senderpassword', 'subject'),
            param
        ):
            raise ValueError(f"Missing required parameters for {func_name}")

        sender_email = gdict['senderemail']
        receiver_email = gdict['receiveremail']
        password = gdict['senderpassword']
        subject = gdict['subject']

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email

        text = ""
        html = ""

        if oacommon._checkparam('messagetext', param) and not oacommon._checkparam('messagehtml', param):
            text = oacommon.effify(param['messagetext'])
            part1 = MIMEText(text, "plain")
            message.attach(part1)
        elif oacommon._checkparam('messagehtml', param) and not oacommon._checkparam('messagetext', param):
            html = oacommon.effify(param['messagehtml'])
            part2 = MIMEText(html, "html")
            message.attach(part2)
        elif oacommon._checkparam('messagetext', param) and oacommon._checkparam('messagehtml', param):
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
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        oacommon.logend(func_name)

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"sendmailbygmail failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
