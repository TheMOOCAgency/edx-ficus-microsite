# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#IMPORT FOR SCRIPT TO
##RUN
##WRITE EXCEL FILE
##SEND EMAIL
import os
import importlib
import csv
import time
import os
from xlwt import *
import json
import logging

from io import BytesIO

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.core.management import execute_from_command_line
import django
import smtplib
from courseware.courses import get_course_by_id
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from datetime import datetime, date, timedelta
from xmodule.mongo_utils import connect_to_mongodb
from django.conf import settings
from pprint import pformat
from opaque_keys.edx.keys import CourseKey
log = logging.getLogger()

course_id = sys.argv[1]

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
org = course.org

def _connect_to_forum_mongo_db():
    """
    Create & open the connection, authenticate, and provide pointers to the collection
    """
    db_settings = settings.DOC_STORE_CONFIG
    database = connect_to_mongodb(
    host=db_settings["host"],
    port=db_settings["port"],
    db="cs_comments_service_development",
    user=None,
    password=None,
    connectTimeoutMS=db_settings["connectTimeoutMS"],
    socketTimeoutMS=db_settings["socketTimeoutMS"]
    )
    return database

def get_nb_of_forum_posts(course_id):
    database = _connect_to_forum_mongo_db()
    collection = database["contents"]
    ini_time_for_now = datetime.now()
    number_of_posts = 0

    for doc in collection.find({"course_id" : course_id}):
        created_at = doc['created_at'].replace(tzinfo=None)
        date_1day_ago = ini_time_for_now - timedelta(days = 1) 
        if created_at >= date_1day_ago:
            number_of_posts += 1

    database.connection.close()
    return number_of_posts

posts = get_nb_of_forum_posts(course_id)

if posts >= 1:
    # SEND MAILS
    html = "<html><head></head><body><p>Bonjour,<br />il y a "+str(posts)+" message(s) qui a/ont été posté(s) sur le forum du cours '"+course.display_name_with_default+"' depuis le dernier rapport<br /><br/>https://digital-campus-en3s.fr/courses/"+course_id+"/discussion/forum/</p></body></html>"

    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

    for i in range(len(TO_EMAILS)):
        fromaddr = "EN3S <ne-pas-repondre@themoocagency.com>"
        toaddr = str(TO_EMAILS[i])
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Notification des mails '"+course.display_name_with_default+"' - " + time.strftime("%d.%m.%Y")
        part = MIMEBase('application', 'octet-stream')
        server = smtplib.SMTP('mail3.themoocagency.com', 25)
        server.starttls()
        server.login('contact', 'waSwv6Eqer89')
        msg.attach(part2)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        log.info('Email sent to '+toaddr)