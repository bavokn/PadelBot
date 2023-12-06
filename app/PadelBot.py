import calendar
import datetime
import logging
from queue import Queue
from dotenv import load_dotenv
from requests_html import HTMLSession
from bs4 import BeautifulSoup

logging.basicConfig(filename=f'padelBot-{datetime.datetime.today().strftime("%d-%m-%Y")}.log', level=logging.INFO)

class PadelBot:
    def __init__(self, clubId) -> None:
        load_dotenv()
        self.clubId = clubId
        self.messageQueue = Queue()
        self.dates = [datetime.datetime.today() + datetime.timedelta(days=i) for i in range(7)]
        self.fieldKeys = self.getFieldKeys()
        # TODO parse to more readable object
        self.fields = {x:{y : [] for y in self.fieldKeys} for x in self.dates}
        self.currentDay = datetime.datetime.today()
        
    # ClubId excelsior:2293
    # group id : 3966
    # ClubID wimbeledon: 2347
    # terrain group id wimbledon : 8685
    def getPadelURL(self, planningDay, terrainGroupId="2293", ownClub="true"):
        return "https://www.tennisenpadelvlaanderen.be/clubdashboard/reserveer-een-terrein?clubId={}&planningDay={}&terrainGroupId={}&ownClub={}&clubCourts[0]=I&clubCourts[1]=O".format(self.clubId, planningDay, terrainGroupId, ownClub)

    def getFieldKeys(self):
        session = HTMLSession()
        #used for cookies later on
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        response = session.get(self.getPadelURL(date))
        soup = BeautifulSoup(response.content.decode('utf-8'), features="lxml")
        table = soup.html.find_all("div", {"class": "reservation-table"})[0].find("table").find("tbody")
        keys = []
        for row in table.find_all("tr"):
            tds =  row.select("td")
            t = row.select("th")[0].text
            for p in tds:
                field = p.text.replace("Reserveren in het verleden is niet toegelaten", "")
                if "vrij" in field.lower() and 'ind' in field.lower():
                    fkey = field.replace("Vrij", "").strip()
                    keys.append(fkey)
        return keys


    def getAvailableTimeSlots(self, d: str):
        session = HTMLSession()
        #used for cookies later on
        date = d.strftime("%d-%m-%Y")
        response = session.get(self.getPadelURL(date))
        soup = BeautifulSoup(response.content.decode('utf-8'), features="lxml")
        table = soup.html.find_all("div", {"class": "reservation-table"})[0].find("table").find("tbody")
        fields = {}
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

    def formatMessage(self, s: datetime, field: str ) -> str:
        return "{} | {}, {} is available : {} ".format(
                        s.strftime("%d/%m"),
                        calendar.day_name[s.weekday()], 
                        field, 
                        s.strftime("%H:%M"))

    def refresh(self): 
        logging.info('refreshing')
        # prevent disturbing during the night
        # if 6 < datetime.datetime.now().hour < 22 :
        #loop over each day
        for day in self.dates:
            newFields = self.getAvailableTimeSlots(day)
            #check if extra field is available and not in list
            for (k, field) ,(k2, newField) in zip(self.fields[day].items(), newFields.items()):
                print((k, field), (k2, newField))
                changes = list(set(newField) - set(field))
                if len(changes) > 0:
                    self.fields[day] = newFields
                    message = self.formatMessage(changes[0], k)
                    self.messageQueue.put(message)
        # setup everything up for the next day
        newD = datetime.datetime.today()
        if newD.date() > self.currentDay.date():
            logging.info('new day, resetting values')
            self.currentDay = newD
            self.dates.append(newD)
            self.fields[newD] = {x : [] for x in self.fieldKeys}
