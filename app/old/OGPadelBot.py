# -*- coding: utf-8 -*-
import time
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import datetime
from datetime import timedelta
import calendar
import logging
from DiscordBot import send

logging.basicConfig(filename='padelBot.log', level=logging.DEBUG)

#create array for upcoming week
today = datetime.datetime.today()
dates = [today + timedelta(days=i) for i in range(7)]

cookies = {}

def getBaseUrl():
  return "https://www.tennisvlaanderen.be/home?p_p_id=58&p_p_lifecycle=1&p_p_state=maximized&p_p_mode=view&saveLastPath=0&_58_struts_action=/login/login&_58_doActionAfterLogin=true"

# ClubId excelsior:2293
# group id : 3966
# ClubID wimbeledon: 2347
# terrain group id wimbledon : 8685
def getPadelURL(planningDay, terrainGroupId="3966", ownClub="true"):
  return "/reserveer-een-terrein?clubId=2347&planningDay={}&terrainGroupId={}&ownClub={}&clubCourts[0]=I&clubCourts[1]=O".format(planningDay, terrainGroupId, ownClub)

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
  fields = {}
  # indoorFields = ['10818242', '10818241', '10818240']
  # indoor 7 10818242, indoor 6 10818241 , indoor 5 10818240
  #filter out the indoor fields only
  for row in table.find_all("tr"):
    tds =  row.select("td")
    t = row.select("th")[0].text
    for p in tds:
      field = p.text.replace("Reserveren in het verleden is niet toegelaten", "")
      if "vrij" in field.lower() and 'ind' in field.lower():
        timeslot = datetime.datetime.strptime(date + " " + t, '%d-%m-%Y %H:%M')
        fkey = field.replace("Vrij", "").strip()
        #only take slots after 5, or weekend
        if (16 < timeslot.hour < 23)  or  timeslot.weekday() > 4:
          # check wether the padel field is allready in the list
          if fkey not in fields: fields[fkey] = []
          fields[fkey].append(timeslot)
  return fields

def getDailyReport(fields, date):
  message = "Daily Padel report - {}  : {} \n".format(calendar.day_name[date.weekday()],date.strftime("%d-%m-%Y"))
  for k, v in fields.items():
    message += k + " \n"
    for timeSlot in v:
      message += timeSlot.strftime("%H:%M") + "\n"
  return message

# send report for each day
def sendReport(datesDict):
  messages = []
  for k,v in datesDict.items():
    messages.append(getDailyReport(v, k))
  send(messages)

#run function
fields = {x: getAvailableTimeSlots(x) for x in dates}
# fields = fieldsMock()
dailyNoticeSent = False
d = datetime.datetime.today()

#start the loop
while True :
  logging.info("i'm awake !")
  #prevent disturbing during the night
  if 6 < datetime.datetime.now().hour < 20 :
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
          # send([message])
          logging.info("found a change in the calender, sending :")
          logging.info(message)

      # skip the daily report
      if not dailyNoticeSent and 6 < datetime.datetime.now().hour < 8 :
        # send daily notification once
        logging.info("sending daily report")
        sendReport(fields)
        dailyNoticeSent = True
      #small sleep between the loops preventing(?) a ban
      time.sleep(1)
  # check if its a new day, if so program can resend daily
  # setup everything up for the extra day
  newD = datetime.datetime.today()
  if newD.date() > d.date():
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
