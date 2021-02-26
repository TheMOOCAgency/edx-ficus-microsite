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
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
log = logging.getLogger()

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
course_id = sys.argv[2]
frequence = int(sys.argv[3])

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
org = course.org
site_name=configuration_helpers.get_value_for_org(org, "SITE_NAME", None)

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

def get_forum_posts(course_id):
    database = _connect_to_forum_mongo_db()
    collection = database["contents"]
    ini_time_for_now = datetime.now()
    number_of_posts = 0
    urls = {}
    for doc in collection.find({"course_id" : course_id}):
        created_at = doc['created_at'].replace(tzinfo=None)
        date_since_last = ini_time_for_now - timedelta(days = frequence) 
        if created_at >= date_since_last:
            new_url = ""

            # Is it a Comment ? If yes lets find the commentthread
            if doc["_type"] == "Comment":
                comment_thead = collection.find_one({"_id" : doc["comment_thread_id"]})

            # Is it a CommentTrhead ? If yes lets find the commentable_id
            if doc["_type"] == "CommentThread":
                comment_thead = doc

            new_url = "https://{}/courses/{}/discussion/forum/{}/threads/{}".format(site_name,course_id,comment_thead["commentable_id"],str(comment_thead["_id"]))

            if new_url and (not new_url in urls):
                urls[new_url] = comment_thead["title"]

            number_of_posts += 1

    database.connection.close()
    return number_of_posts, urls

posts,urls = get_forum_posts(course_id)
forum_link = "https://{}/courses/{}/discussion/forum/".format(site_name,course_id)

if posts >= 1:
    # SEND MAILS
    html = "<html><head></head><body><p>Bonjour,<br/><br />il y a {posts} message(s) qui a/ont été posté(s) sur le forum du cours '{course_name}' depuis le dernier rapport.<br /><br/>Voici le <a href={forum_link}>lien du forum</a> concerné.".format(posts=str(posts),course_name=course.display_name_with_default,forum_link=forum_link)

    # Add list of links
    html +="<br/><br/>Voici les liens d'accès direct aux fils de discussion. Il peut y avoir plusieurs nouveaux messages par fil.<br/>"
    for key in urls.keys():
        html += '<br/>- '+ urls[key] + '<br/><a href="' + key + '">' + key + '</a><br/>'

    html += "</p></body></html>"


    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

    for i in range(len(TO_EMAILS)):
        fromaddr = "{} <ne-pas-repondre@themoocagency.com>".format(org)
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
        log.info('[WUL] : Email sent to '+toaddr)
