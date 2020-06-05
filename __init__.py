from __future__ import print_function
import json
import sys
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.util.parse import extract_datetime
from datetime import datetime, timedelta
import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools



UTC_TZ = u'+00:00'
FLOW = OAuth2WebServerFlow(
    client_id='73558912455-smu6u0uha6c2t56n2sigrp76imm2p35j.apps.googleusercontent.com',
    client_secret='0X_IKOiJbLIU_E5gN3NefNns',
    scope=['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/contacts.readonly'],
    user_agent='Smart assistant box')


# TODO: Change "Template" to a unique name for your skill
class DeleteEventSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(DeleteEventSkill, self).__init__(name="DeleteEventSkill")

    @property
    def utc_offset(self):
        return timedelta(seconds=self.location['timezone']['offset'] / 1000)
    @intent_handler(IntentBuilder("delete_event_intent").require('delete').require('Event').optionally('date').optionally('Location').build())
    def deleteEvent(self, message):
        storage1 = Storage('/opt/mycroft/skills/deleteeventskill.hanabouzid/info3.dat')
        credentials = storage1.get()
        if credentials is None or credentials.invalid == True:
            credentials = tools.run_flow(FLOW, storage1)
        print(credentials)
        # Create an httplib2.Http object to handle our HTTP requests and
        # authorize it with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('calendar', 'v3', http=http)
        people_service = build(serviceName='people', version='v1', http=http)
        print("authorized")
        # To get a list of people in the user's contacts,
        results = people_service.people().connections().list(resourceName='people/me', pageSize=100,
                                                             personFields='names,emailAddresses',
                                                             fields='connections,totalItems,nextSyncToken').execute()
        connections = results.get('connections', [])

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