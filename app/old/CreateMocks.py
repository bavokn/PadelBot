# -*- coding: utf-8 -*-
import requests
import time
import json
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import nest_asyncio
import datetime
from datetime import date, timedelta
import calendar

#create array for upcoming week
today = datetime.datetime.today()
dates = [today + timedelta(days=i) for i in range(7)]


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
  fields = {}
  for row in table.find_all("tr"):
    p =  row.select("td")
    t = row.select("th")[0].text
    if len(p) > 0:
      field = p[0].text.replace("Reserveren in het verleden is niet toegelaten", "")
      if "vrij" in field.lower():
        timeslot = datetime.datetime.strptime(date + " " + t, '%d-%m-%Y %H:%M')
        fkey = field.replace("Vrij", "").strip()
        #only take slots after 5, or weekend
        if (16 < timeslot.hour < 23)  or  timeslot.weekday() > 4:
          # check wether the padel field is allready in the list
          if fkey not in fields: fields[fkey]= []
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
def sendReport(datesDict, clientSend):
  for k,v in datesDict.items():
      time.sleep(1)

#run function
fields = {str(x): getAvailableTimeSlots(x) for x in dates}
with open("mock.json", "w") as fp:
    json.dump(fields, fp, indent=4, sort_keys=True, default=str)
