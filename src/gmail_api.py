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
from flask import Flask

class GmailAPI:

    def __init__(self, app: Flask, conf):
        self.app = app
        self.conf = conf
        creds = None
        token_path = os.path.join("src", "creds", "token.json")
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path,
                                                          conf.gmail["scopes"])
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    conf.gmail["creds"], conf.gmail["scopes"])
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

        self.email_from = conf.email["from"]
        self.email_subject = conf.email["subject"]

    def send_email(self, image_path: str, email_to: str):

        message = MIMEMultipart()
        message.attach(MIMEText(self.conf.email["mess"]))

        message['subject'] = self.conf.email["subject"]

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        image = MIMEImage(image_data)
        image.add_header('Content-Disposition', 'attachment', filename='image.jpg')
        message.attach(image)

        message["to"] = email_to
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}

        try:
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            self.app.logger.info(f'sent message to {message} Message Id: {message["id"]}')
        except HTTPError as error:
            self.app.logger.error(f'An error occurred: {error}')
            message = None
        except TypeError as error:
            self.app.logger.error("Not valid response")
            self.app.logger.error(error)
