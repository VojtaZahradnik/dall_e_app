import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import HTTPError
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

class GmailAPI:

    def __init__(self, conf):
        creds = None
        token_path = os.path.join("src", "creds","token.json")
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path,
                                                          conf["gmail_scopes"])
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    conf["gmail_creds"], conf["gmail_scopes"])
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

        self.email_from = conf["email_from"]
        self.email_subject = conf["email_subject"]

        self.message = MIMEMultipart()
        self.message.attach(MIMEText(conf["email_mess"]))

        self.message['subject'] = conf["email_subject"]


    def send_email(self, image_path: str, email_to: str):

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        image = MIMEImage(image_data)
        image.add_header('Content-Disposition', 'attachment', filename='image.jpg')
        self.message.attach(image)

        self.message["to"] = email_to
        raw_message = base64.urlsafe_b64encode(self.message.as_bytes()).decode()
        create_message = {'raw': raw_message}

        try:
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            print(f'sent message to {message} Message Id: {message["id"]}')
        except HTTPError as error:
            print(f'An error occurred: {error}')
            self.message = None
        except TypeError as error:
            print("Not valid response")
            print(error)

