import oacommon 
import inspect
import requests
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

gdict={}

def setgdict(self,gdict):
     self.gdict=gdict

myself = lambda: inspect.stack()[1][3]


@oacommon.trace
def sendtelegramnotify(self,param):
    """
    Assume the bot name is my_bot.

    1- Make /start on your bot

    2- Send a dummy message to the bot.
    You can use this example: /my_id @my_bot
    
    3- Go to following url: https://api.telegram.org/botXXX:YYYY/getUpdates
    replace XXX:YYYY with your bot token
    Or join https://t.me/RawDataBot /start 

    4- Look for "chat":{"id":zzzzzzzzzz, zzzzzzzzzz is your chat id 
    
    - name: send telegram message
      oa-notify.sendtelegramnotify:
        tokenid: "5119550574:AAHoM8C8LDkD71XAJfuKswW-DQvlegEMkEc"
        chatid: 
           - "18278029"
        message: "prova {zzz} test"
        printresponse: True #optional

    """
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('tokenid','chatid','message'),param):
        tokenid=gdict['tokenid']
        chatid=gdict['chatid']
        message=oacommon.effify(gdict['message'])
        for cid in chatid:
            send_text = 'https://api.telegram.org/bot' + tokenid + '/sendMessage?chat_id=' + cid + '&parse_mode=Markdown&text=' + message

        response = requests.get(send_text)
        if oacommon._checkparam('printresponse',param):
            if param['printresponse']:
                print(response.json())

        
        oacommon.logend(myself())
    else:
        exit()
        
        
        
@oacommon.trace
def sendmailbygmail(self,param):
    """
    
    - name: send mail by gmail
      oa-notify.sendmailbygmail:
        senderemail: "meraviglioso.2013@gmail.com"
        receiveremail: "alessandro.pioli@gmail.com,meraviglioso.2013@gmail.com"
        senderpassword: "password.123"
        subject: "nofify"
        messagetext: >
            prova {zzz} test
        messagehtml: >
            <html>
            <body>
                <b>prova</b> {zzz} test
            </body>
            </html>

    """    
    oacommon.logstart(myself())
    if oacommon.checkandloadparam(self,myself(),('senderemail','receiveremail','senderpassword','subject'),param):
        sender_email = gdict['senderemail']
        receiver_email = gdict['receiveremail']
        password = gdict['senderpassword']
        subject = gdict['subject']
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email

        # Create the plain-text and HTML version of your message
        text=""
        html=""
        part1=""
        part2=""
        if oacommon._checkparam('messagetext',param) and not oacommon._checkparam('messagehtml',param):
            text = oacommon.effify(param['messagetext'])
            part1 = MIMEText(text, "plain")
            message.attach(part1)
        elif oacommon._checkparam('messagehtml',param) and not oacommon._checkparam('messagetext',param):
            html = oacommon.effify(param['messagehtml'])
            part2 = MIMEText(html, "html")
            message.attach(part2)
        elif  oacommon._checkparam('messagetext',param) and oacommon._checkparam('messagehtml',param):
            text = oacommon.effify(param['messagetext'])
            part1 = MIMEText(text, "plain")
            html = oacommon.effify(param['messagehtml'])
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
        else:
            print(f"messagetext or messagehtml are required.")
            exit()
        # Turn these into plain/html MIMEText objects
        
        

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first


        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )




        
        oacommon.logend(myself())    
    else:
        exit()