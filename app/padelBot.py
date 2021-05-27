# -*- coding: utf-8 -*-
import requests
import time
import json
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import nest_asyncio
import fbchat
import datetime
import pprint
from datetime import date, timedelta
from fbchat import Client, Message, ThreadType
import calendar
import logging
from mocks import datesMock, fieldsMock, newFieldsMock
logging.basicConfig(filename='padelBot.log', level=logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)

nest_asyncio.apply()

#create array for upcoming week
today = datetime.datetime.today()
dates = [today + timedelta(days=i) for i in range(7)]

cookies = {}
try:
    # Load the session cookies
    with open('cookie.json', 'r') as f:
        cookies = json.load(f)
except Exception() as e:
    # If it fails, never mind, we'll just login again
    print(e)
    pass

email = "padelbot2@gmail.com"
password = "padel1234"

client = Client(email, password, max_tries=1)

# Save the session again
with open('cookie.json', 'w') as f:
    json.dump(client.getSession(), f)

def getBaseUrl():
  return "https://www.tennisvlaanderen.be/home?p_p_id=58&p_p_lifecycle=1&p_p_state=maximized&p_p_mode=view&saveLastPath=0&_58_struts_action=/login/login&_58_doActionAfterLogin=true"

def getPadelURL(planningDay, terrainGroupId="3966", ownClub="true"):
  return "/reserveer-een-terrein?clubId=2293&planningDay={}&terrainGroupId={}&ownClub={}&clubCourts[0]=I&clubCourts[1]=O".format(planningDay, terrainGroupId, ownClub)


def getLoginParams(padelURL):
  return {
    "_58_login" : "0594943",
    "_58_password" : "BAVO KNAEPS",
    "_58_redirect" : padelURL
}

session = HTMLSession()
c = session.get(getBaseUrl())

def getAvailableTimeSlots(d, cookies = c.cookies):
  date = d.strftime("%d-%m-%Y")
  padelURL = getPadelURL(date)
  loginParams = getLoginParams(padelURL) 
  response = session.post(getBaseUrl(), data=loginParams, cookies = cookies)
  soup = BeautifulSoup(response.content.decode('utf-8'), features="lxml")
  table = soup.html.find_all("div", {"class": "reservation-table"})[0].find("table").find("tbody")
  fields = {"Padel 1" : [], "Padel 2" : [], "Padel 3" : []}
  for row in table.find_all("tr"):
    p =  row.select("td")
    t = row.select("th")[0].text
    if len(p) > 0:
      field = p[0].text.replace("Reserveren in het verleden is niet toegelaten", "")
      if "vrij" in field.lower():
        timeslot = datetime.datetime.strptime(date + " " + t, '%d-%m-%Y %H:%M')
        #only take slots after 5, or weekend
        if (16 < timeslot.hour < 23)  or  timeslot.weekday() > 4:
          fields[field.replace("Vrij", "").strip()].append(timeslot)
  return fields

def getDailyReport(fields, date):
  message = "Daily Padel report : {} \n".format(date.strftime("%d-%m-%Y"))
  for k, v in fields.items():
    message += k + " \n"
    for timeSlot in v:
      message += timeSlot.strftime("%H:%M") + "\n"
  return message

# send report for each day
def sendReport(datesDict, clientSend):
  for k,v in datesDict.items():
      message_id = clientSend.send(Message(text=getDailyReport(v, k)), thread_id="2087266384717178", thread_type=ThreadType.GROUP)
      time.sleep(1)

#run function
fields = {x: getAvailableTimeSlots(x) for x in dates}
# fields = fieldsMock()
dailyNoticeSent = False
d = datetime.datetime.today()

while True :
  logging.info("i'm awake !")
  #prevent disturbing during the night
  if 8 < datetime.datetime.now().hour < 22 :
    #loop over each day
    #check if logged in
    for day in dates:
      newFields = getAvailableTimeSlots(day)
      # newFields = newFieldsMock()[day]
      #check if extra field is available
      for (k, field) ,(k2, newField) in zip(fields[day].items(), newFields.items()):
        changes = list(set(newField) - set(field))
        if len(changes) > 0:
          fields[day] = newFields
          message = "{}, {} is available : {} ".format(calendar.day_name[changes[0].weekday()], k, changes[0].strftime("%H:%M"))
          if not client.isLoggedIn(): client.login(email, password)
          message_id = client.send(Message(text=message), thread_id="2087266384717178", thread_type=ThreadType.GROUP)
          logging.info("found a change in the calender, sending :")
          logging.info(message)
          #log back out
        # send notification something changed

      if not dailyNoticeSent and 9 < datetime.datetime.now().hour < 11 :
        # send daily notification once
        logging.info("sending daily report")
        if not client.isLoggedIn(): client.login(email, password)
        sendReport(fields, client)
        dailyNoticeSent = True
      #small sleep between the loops preventing(?) a ban
      time.sleep(1)
  # check if its a new day, if so program can resend daily
  # setup everything up for the extra day
  newD = datetime.datetime.today()
  if not newD > d:
    logging.info("new Day !")
    logging.info("resetting values")
    d = newD
    dailyNoticeSent = False
    dates = [d + timedelta(days=i) for i in range(7)]
    fields = {x:getAvailableTimeSlots(x) for x in dates}
    newFields = fields

  #time.sleep(5)
  logging.info("completed loop, sleeping now zzzzzzzzzz")
  time.sleep(20*60)
