from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']

# label:rollbar before:2019/06/01


def getMessagesToDelete(service):
    messageIds = []
    results = service.users().messages().list(
        userId='me', q='in:spam', maxResults=500).execute()
    messages = results.get('messages', [])

    # metadataHeaders= ['From', 'To','Date','Subject' ]
    for message in messages:
        # messageData = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders= metadataHeaders).execute()
        # for header in messageData['payload']['headers']:
        #     if(header['name']=='From'):
        #         print(header['value'])
        messageIds.append(message['id'])

    return messageIds


def deleteMessages(service, messageIds):
    start_time = time.time()
    print("Deleting " + str(len(messageIds)) + " messages")
    result = service.users().messages().batchDelete(
        userId='me', body={"ids": messageIds}).execute()
    print(result, "--- %s seconds ---" % (time.time() - start_time))


def getAndDeleteOldMessages(service):
    while True:
        messageIds = getMessagesToDelete(service)
        if (len(messageIds) == 0):
            break
        deleteMessages(service, messageIds)


def main():
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

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    getAndDeleteOldMessages(service)
    # getMessagesToDelete(service)

if __name__ == '__main__':
    main()
