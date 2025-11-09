from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import os

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def create_event(summary, start_time, end_time, description=""):
    creds = None
    # Token file stores user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, go through OAuth flow
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save credentials for future runs
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Europe/Helsinki'},
        'end': {'dateTime': end_time, 'timeZone': 'Europe/Helsinki'},
    }
    
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get('htmlLink')

