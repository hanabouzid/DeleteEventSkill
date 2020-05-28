from __future__ import print_function
import json
import sys
from adapt.intent import IntentBuilder
from adapt.engine import IntentDeterminationEngine
from mycroft.skills.core import MycroftSkill, intent_handler
import pickle
import os.path
from mycroft.util.parse import extract_datetime
from datetime import datetime, timedelta
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
UTC_TZ = u'+00:00'
SCOPES = ['https://www.googleapis.com/auth/calendar']


# TODO: Change "Template" to a unique name for your skill
class DeleteEventSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(DeleteEventSkill, self).__init__(name="DeleteEventSkill")

    @property
    def utc_offset(self):
        return timedelta(seconds=self.location['timezone']['offset'] / 1000)
    @intent_handler(IntentBuilder("delete_event_intent").require("delete").require("Event").require("date").build())
    def deleteEvent(self, message):
        # AUTHORIZE
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
                    '/opt/mycroft/skills/regskill.hanabouzid/client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('calendar', 'v3', credentials=creds)
        #extraire la date et le titre
        utt = message.data.get("utterance", None)
        list1=utt.split(" starts ")
        strtdate=list1[1]
        st = extract_datetime(strtdate)
        st = st[0] - self.utc_offset
        date = st.strftime('%Y-%m-%dT%H:%M:00')
        date += UTC_TZ
        list2=list1[0].split(" event ")
        title=list2[1]
        events = service.events().list(calendarId='primary', timeMin=date, singleEvents=True).execute()
        for event in events['items']:
            if(event['summary']== title and event['start'].get('dateTime') ==date):
                eventid=event['id']
                service.events().delete(calendarId='primary', eventId=eventid, sendUpdates='all').execute()
                self.speak_dialog("eventdeleted",data={"title": title})
            else:
                self.speak_dialog("notevent")






def create_skill():
    return DeleteEventSkill()
