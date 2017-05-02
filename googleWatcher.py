#!/usr/bin/python3.5

# False Ads links - Google Search
# Developed by Raphael Denipotti

import requests
import re
import smtplib
import time
import pickle
import os
import json
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup


try:
  configFile = open("config.json", "r")
  configF = json.load(configFile)
  configFile.close()
except:
  sys.stderr.write("Error loading config.json file.\n")
  exit(1)
if not 'header' in configF:
  sys.stderr.write("'Header' parameter wasn't set in the config.json file\n")
  exit(1)
if not 'site' in configF:
  sys.stderr.write("'Site' parameter not found in the config.json file\n")
  exit(1)
if not 'paramList' in configF:
  sys.stderr.write("'List with parameters to search' parameter not found in the config.json file\n")
  exit(1)
if not 'receiver' in configF:
  sys.stderr.write("'Receiver' parameter not found in the config.json file\n")
  exit(1)
if not 'sender' in configF:
  sys.stderr.write("'Sender' parameter not found in the config.json file\n")
  exit(1)


# Methods

def getContent(par):
   url = "https://www.google.com.br/search?q="+par
   header = configF["header"]
   try:
     r = requests.get(url, headers=header)
   except HTTPError as e:
     return None
   try:
     bsObj = BeautifulSoup(r.text, "html.parser")
   except AttributeError as e:
     return None
   return bsObj

def getSite(obj):
   siteList = obj.findAll("cite", {"class":"_WGk"})
   return siteList

def getTitle(obj):
   titleList = obj.findAll("div", {"class":"ellip ads-creative"})
   return titleList

def getDesc(obj):
   descList = obj.findAll("div", {"class":"ellip"})
   return descList

def regExp(site):
   wsite = configF["site"]
   url = site.get_text()
   pattern = re.compile(r"(\b%s\b)"%wsite)
   match = pattern.search(url)
   if match:
      status = 0
   else:
      status = 1
   return status

def createDic(siteList, titleList, descList, param):
   x = 0
   dicObj = dict()
   while  x < len(siteList):
    dicObj["ID." + str(x+1) ] = dict(url=siteList[x], title=titleList[x], desc=descList[x])
    x += 1
   return str(dicObj)

def smtpSender(x):
   sender = configF["sender"]
   receiver = configF["receiver"]

   if len(receiver)>1:
      receivers = ",".join(receiver)
   else:
      receivers = receiver
   try:
      msg = MIMEMultipart('alternative')
      msg['Subject'] = "Alert - High Importance"
      msg['From'] = sender
      msg['To'] = receivers
      sites = '\n'.join(x)
      if sites:
       text = "These domains aren't yours. Please review them!\n\n\n%s" %sites
      else:
       text = "There were no domains found that do not belong to your organization"
      s = smtplib.SMTP('localhost')
      part1 = MIMEText(text, 'plain')
      msg.attach(part1)
      s.sendmail(sender, receiver, msg.as_string())
   except SMTPException:
      print ("Error: unable to send email")

def verifyDomain(siteList):
    for site in siteList:
      stat = regExp(site)
      if stat == 0:
        print("")
        print("Domain %s belong to the organization." %format(site.get_text()))
      else:
        print("")
        print("Domain %s was identified as unknown. An alert was generated for manual review." %format(site.get_text()))
        badList.append(format(site.get_text()))
    return badList

def recSave(record):

   ttime = time.asctime()
   timList = ttime.split()
   year = timList[4]
   mond = timList[1]
   day = timList[2]
   etime = timList[3]

   directory_r = "./"+format(year)+"/"


   if not os.path.exists(directory_r):
     os.makedirs(directory_r)

   directory = directory_r+format(mond)+"/"

   if not os.path.exists(directory):
      os.makedirs(directory)

   compName = os.path.join(directory, format(day+"-"+etime)+".pkl")
   recfile = open(compName,'wb')

   pickle.dump(record, recfile)

   recfile.close()


if __name__ == "__main__":

  badList = []
  dicObj = {}
  paramList = configF["paramList"]

  for param in paramList:

      bsObj = getContent(param)
      siteList = getSite(bsObj)
      titleList = getTitle(bsObj)
      descList = getDesc(bsObj)

      blist = verifyDomain(siteList)
      dicObj[param] = createDic(siteList, titleList, descList, param)

  recSave(dicObj)

  smtpSender(blist)
  print(dicObj)

  print("")
  print("Done! The script was executed!")
  print("")
