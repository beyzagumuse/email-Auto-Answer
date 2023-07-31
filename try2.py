import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os


# Gmail API'ye erişim için gereken izinler
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.modify']


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file('C:\\Users\\z004r4dj\\Desktop\\E-mail\\email-select\\token.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return creds




def process_mails(service):
    try:
        query = 'is:unread "dikkat"'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        if not messages:
            print("Cevaplanacak yeni mail yok")
        else:
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                msg_subject = [header for header in msg['payload']['headers'] if header['name'] == 'Subject'][0]['value']
                msg_from = [header for header in msg['payload']['headers'] if header['name'] == 'From'][0]['value']

                print(f'Processing message: {msg_subject} from {msg_from}')

                send_reply(service, msg)
                mark_as_read(service, message['id'])
                
    except HttpError as error:
        print(f'An error occurred: {error}')

"""
def send_reply(service, original_msg):
    msg_subject = [header for header in original_msg['payload']['headers'] if header['name'] == 'Subject'][0]['value']
    msg_from = [header for header in original_msg['payload']['headers'] if header['name'] == 'From'][0]['value']

    reply = {
        'message': {
            'threadId': original_msg['threadId'],
            'subject': f'Re: {msg_subject}',
            'body': 'Anlaşıldı.',
        },
        'to': msg_from,
    }

    send_message(service, 'me', reply)
"""

import re

def clean_email_address(email_address):
    cleaned_email = re.search(r'<(.*)>', email_address)
    if cleaned_email:
        return cleaned_email.group(1)
    else:
        return email_address

def send_reply(service, original_msg):
    msg_subject = [header for header in original_msg['payload']['headers'] if header['name'] == 'Subject'][0]['value']
    msg_from = [header for header in original_msg['payload']['headers'] if header['name'] == 'From'][0]['value']

    cleaned_email_from = clean_email_address(msg_from)

    reply = {
        'message': {
            'threadId': original_msg['threadId'],
            'subject': f'Re: {msg_subject}',
            'body': 'Anlaşıldı.',
        },
        'to': cleaned_email_from,
    }

    send_message(service, 'me', reply)

def mark_as_read(service, msg_id):
    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()


import base64
from email.mime.text import MIMEText

def send_message(service, user_id, message):
    try:
        message_body = message['message']['body']
        message_subject = message['message']['subject']
        to = message['to']

        mime_message = MIMEText(message_body)
        mime_message['to'] = to
        mime_message['subject'] = message_subject

        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')

        message = (service.users().messages().send(userId=user_id, body={'raw': raw_message}).execute())
        print(f'sent message to {to}: {message_subject}')
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gmail Otomatik Yanıtlama Uygulaması")
        self.setGeometry(300, 300, 800, 600)

        # Gmail API'ye bağlanma
        creds = get_credentials()
        self.service = build('gmail', 'v1', credentials=creds)

        # Check Emails düğmesi
        check_emails_button = QPushButton("Check Emails", self)
        check_emails_button.move(350, 280)
        check_emails_button.clicked.connect(self.check_emails)

        # QTimer kullanarak arka planda e-postaları kontrol etme
        self.email_check_timer = QTimer(self)
        self.email_check_timer.timeout.connect(self.check_emails)
        self.email_check_timer.start(60000)  # 60000 ms (1 dakika) aralıklarla e-postaları kontrol eder

    def check_emails(self):
        process_mails(self.service)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
