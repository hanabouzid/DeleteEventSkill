from __future__ import print_function
import json
import sys
from adapt.intent import IntentBuilder
from adapt.engine import IntentDeterminationEngine
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.util.parse import extract_datetime
from datetime import datetime, timedelta
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
from googleapiclient.discovery import build



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
    @intent_handler(IntentBuilder("delete_event_intent").require('update').require('Event').optionally('time').optionally('Location').build())
    def deleteEvent(self, message):
        #AUTHORIZE
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

        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
        #extraire la date et le titre
        utt = message.data.get("utterance", None)

        # extract the location
        # location = message.data.get("Location", None)
        print(utt)
        # listname1=utt.split(" named ")
        # listname2=listname1[1].split(" with ")
        # title =listname2[0]
        lister = utt.split(" starts ")
        lister2 = lister[1].split(" in ")
        location = lister2[1]
        print(location)
        strtdate = lister2[0]
        st = extract_datetime(strtdate)
        st = st[0] - self.utc_offset
        datestart = st.strftime('%Y-%m-%dT%H:%M:00')
        datestart += UTC_TZ
        print(datestart)
        lister3 = lister[0].split(" the event ")
        title = lister3[1]
        print(title)
        events_result = service.events().list(calendarId='primary', timeMin=datestart,
                                              maxResults=1, singleEvents=True,
                                              orderBy='startTime', q=location).execute()
        events = events_result.get('items', [])
        if not events:
            self.speak_dialog("notEvent")

        for event in events:
            eventid = event['id']
            service.events().delete(calendarId='primary', eventId=eventid, sendUpdates='all').execute()
            self.speak_dialog("eventdeleted", data={"title": title})


def create_skill():
    return DeleteEventSkill()