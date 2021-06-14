from __future__ import print_function

import base64
import os
import pathlib
import pickle
from datetime import datetime

import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']


class GmailAPIHelper:
    def __init__(self):
        """Shows basic usage of the Gmail API.
                Lists the user's Gmail labels.
                """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        print(self.service)

    def get_message_ids(self, query):
        messageIds = []
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=500).execute()
        messages = results.get('messages', [])

        for message_id in messages:
            messageIds.append(message_id['id'])
        return messageIds

    def get_messages_df(self, query, attach_type=None):
        messageIds = self.get_message_ids(query)

        message_data = []
        attach_data = []

        for message_id in messageIds:
            message = self.service.users().messages().get(userId='me', id=message_id, format="full").execute()
            subject = ""
            date_val = ""
            for index, header in enumerate(message['payload']['headers']):
                if header['name'] == 'Subject':
                    subject = header['value']
                    print(header['value'])
                if header['name'] == 'Date':
                    date_val = header['value']

            message_data.append({**{
                "messageId": message_id,
                "data_val": date_val,
                "subject": subject,
            }, **{x["name"]: x["value"] for x in message['payload']['headers']}})
            parts = message['payload']['parts']
            for part in parts:
                if part["mimeType"] in ['text/plain']:
                    data = part['body']['data']
                    try:
                        base64_bytes = data.encode('ascii')
                        message_bytes = base64.b64decode(base64_bytes + b'==')
                        message = message_bytes.decode('ascii')
                    except:
                        message = ""
                    attach_data.append({
                        "messageId": message_id,
                        "data": message,
                        "raw": data,
                        "data_val": date_val,
                        "subject": subject
                    })

        message_df = pd.DataFrame(message_data)
        attach_df = pd.DataFrame(attach_data)
        return message_df, attach_df

    def download_attachments(self, attach_df):
        attach_df["status"] = attach_df.apply(lambda df: self._download_attachment(df), axis=1)
        attach_df.to_csv(
            f'{pathlib.Path(__file__).parent.absolute()}/output/final_out_{str(self.get_epoch())}.csv')
        return attach_df

    def _download_attachment(self, df):
        try:
            att = self.service.users().messages().attachments().get(userId='me', messageId=df["messageId"],
                                                                    id=df["attachmentId"]).execute()
            data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            # path = f"/Users/mehul.kumar/Workspace/personal/gmailAlerts/downloads/{df['file_name']}"
            path = f"{pathlib.Path(__file__).parent.absolute()}/output/{df['file_name']}"
            print(path)
            with open(path, 'wb') as f:
                f.write(file_data)
            return "Done"
        except Exception as e:
            print(e)
            return str(e)


    @staticmethod
    def get_epoch():
        """
        Gets the current Epoch time stamp
        :return:
        """
        epoch = datetime.utcfromtimestamp(0)
        dt = datetime.now()
        return int((dt - epoch).total_seconds() * 1000.0)


if __name__ == '__main__':
    gmail_api_helper = GmailAPIHelper()
    a, b = gmail_api_helper.get_messages_df("query", None)
    a.to_csv("x_a.csv")
    b.to_csv("x_b.csv")
    # gmail_api_helper.download_attachments(b)
