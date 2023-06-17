from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import smtplib
import PIL.Image

class SendEmail():

    def __init__(self, email_from: str, email_to: str, date: str, subject: str, image: PIL.Image, server: str):
        self.email_from = email_from
        self.email_to = email_to
        self.date = date
        self.subject = subject
        self.server = server

    def send_mail(self, text, image):
            assert isinstance(send_to, list)
            msg = MIMEMultipart()
            msg['From'] = send_from
            msg['To'] = COMMASPACE.join(send_to)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = subject

            msg.attach(MIMEText(text))

            for f in files or []:
                with open(f, "rb") as fil:
                    part = MIMEApplication(
                        fil.read(),
                        Name=basename(f)
                    )
                # After the file is closed
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
                msg.attach(part)

            smtp = smtplib.SMTP(server)
            smtp.sendmail(send_from, send_to, msg.as_string())
            smtp.close()
