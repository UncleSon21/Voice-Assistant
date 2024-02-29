import os
import time
import playsound
import speech_recognition as sr
from gtts import gTTS
import datetime
import os.path
import pytz
import subprocess

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENSIONS = ["nd", "rd", "th", "st"]

def speak(text):
	tts = gTTS(text = text, lang = "en")
	filename = "voice.mp3"
	tts.save(filename)
	playsound.playsound(filename)

def get_audio():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""	

		try:
			said = r.recognize_google(audio)
			print(said)
		except Exception as e:
			print("Exception: "+ str(e))
	return said.lower()

def authenticate_google():
	creds = None
	if os.path.exists("token.json"):
		creds = Credentials.from_authorized_user_file("token.json", SCOPES)

	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				"credentials.json", SCOPES
				)
			creds = flow.run_local_server(port=0)
	with open("token.json", "w") as token:
		token.write(creds.to_json())

	service = build("calendar", "v3", credentials=creds)
	return service

def get_events(day, service):
	#call the calendar api
	date = datetime.datetime.combine(day, datetime.datetime.min.time())
	end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
	utc = pytz.UTC
	date = date.astimezone(utc)
	end_date = end_date.astimezone(utc)


	events_result = (
		service.events()
		.list(
			calendarId="primary",
			timeMin=date.isoformat(),
			timeMax=end_date.isoformat(),
			singleEvents=True,
			orderBy="startTime",
		)
		.execute()
	)
	events = events_result.get("items", [])

	if not events:
		speak("No upcoming events found.")
	else:
		speak(f"You have {len(events)} events on this day")
		for event in events:
			start = event["start"].get("dateTime", event["start"].get("date"))
			print(start, event["summary"])
			start_time = str(start.split("T")[1].split("-")[0])
			if int(start_time.split(":")[0]) < 12:
				start_time = start_time + "am"
			else:
				start_time = str(int(start_time.split(":")[0]) - 12) + start_time.split(":")[1]
				start_time = start_time + "pm"
			speak(event["summary"] + " at "+ start_time)
def get_date(text):
	text = text.lower()
	today = datetime.date.today()
	print("Text: ",text)
	if text.count("today") > 0:
		return today

	day = -1
	day_of_week = -1
	month = -1
	year = today.year

	for word in text.split():
		if word in MONTHS:
			month = MONTHS.index(word) + 1
		elif word in DAYS:
			day_of_week = DAYS.index(word)
		elif word.isdigit():
			day = int(word)
		else:
			for ext in DAY_EXTENSIONS:
				found = word.find(ext)
				if found > 0:
					try:
						day = int(word[:found])
					except:
						pass
	if month < today.month and month != -1:
		year = year + 1

	if day < today.day and month == -1 and day !=-1:
		month = month + 1

	if month == -1 and day == -1 and day_of_week != -1:
		current_day_of_the_week = today.weekday()
		dif = day_of_week - current_day_of_the_week

		if dif < 0:
			dif += 7
			if text.count("next") >=1:
				dif +=7

		return today + datetime.timedelta(dif)

	print("Month", month)
	print("Year:", year)
	print("Day:", day)
	return datetime.date(year=year, month=month, day=day)

def note(text):
	date = datetime.datetime.now()
	file_name = str(date).replace(":","-")+"-note.txt"
	with open(file_name, "w") as f:
		f.write(text)
	#if in window change the first parameter to "notepad.exe" or other app
	subprocess.Popen(["open","-e", file_name])
wake_call = ["Hello Mi","Hey Mi","Hi Mi"]
ending_call = "Goodbye Mi"
service = authenticate_google()
speak("Hello, i am Mi")
#Get the command from the user via get_audio()
#text = "Make a note for me"
#text.lower()
while True:
	print("Listening")
	text = get_audio()
	for greeting in wake_call:
		if greeting in text:
			speak("How can i help")
			text = get_audio()
	if text.count(ending_call) > 0:
		speak("Have a great day")
		break

	calendar_trigger = ["what do i have", "do i have plans", "am i busy"]
	for phrase in calendar_trigger:
		if phrase in text:
			date = get_date(text)
			if date:
				get_events(date, service)
			else:
				speak("I don't understand")

	note_trigger = ["make a note", "write this down", "take note", "remember this"]
	for phrase in note_trigger:
		if phrase in text:
			speak("Sure thing. What do you want me to note")
			note("She's gorgeous")
			speak("Here it is")