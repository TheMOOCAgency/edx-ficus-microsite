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
course_ids=[
    "course-v1:e-formation-artisanat+Pack_Micro+e-formation-2020",
    "course-v1:e-formation-artisanat+commercial+2020_T1",
    "course-v1:e-formation-artisanat+essentiels+2020_T1",
    "course-v1:e-formation-artisanat+gestion+2020_T1",
    "course-v1:e-formation-artisanat+premium+2020_T1",
    "course-v1:e-formation-artisanat+Module_01+SP_01",
    "course-v1:e-formation-artisanat+Module_02+SP_02",
    "course-v1:e-formation-artisanat+Module_03+SP_03",
    "course-v1:e-formation-artisanat+Module_04+SP_04",
    "course-v1:e-formation-artisanat+Module_05+SP_05",
    "course-v1:e-formation-artisanat+Module_06+SP_06",
    "course-v1:e-formation-artisanat+Module_07+SP_07",
    "course-v1:e-formation-artisanat+Module_08+SP_08",
    "course-v1:e-formation-artisanat+Module_09+SP_09",
    "course-v1:e-formation-artisanat+Module_09-+SP_09-",
    "course-v1:e-formation-artisanat+Module_10+SP_10",
    "course-v1:e-formation-artisanat+Module_11+SP_11",
    "course-v1:e-formation-artisanat+Module_12+SP_12"
]

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

def get_forum_posts():
    database = _connect_to_forum_mongo_db()
    collection = database["contents"]
    post_dict_list = []
    number_of_posts = 0
    for course_id in course_ids :
        for doc in collection.find({"course_id" : course_id, "author_username" : "benissanwi_ASSZg"}):
            created_at = doc['created_at'].replace(tzinfo=None).strftime("%d-%m-%Y")
            message = doc['body']

            # Is it a Comment ? If yes lets find the commentthread
            if doc["_type"] == "Comment":
                comment_thead = collection.find_one({"_id" : doc["comment_thread_id"]})

            # Is it a CommentTrhead ? If yes lets find the commentable_id
            if doc["_type"] == "CommentThread":
                comment_thead = doc

            url = "https://www.e-formation.artisanat.fr/courses/{}/discussion/forum/{}/threads/{}".format(course_id,comment_thead["commentable_id"],str(comment_thead["_id"]))

            post_dict = {
                "created_at" : created_at,
                "message" : message,
                "url" : url
            }

            number_of_posts += 1
            post_dict_list.append(post_dict)

    database.connection.close()
    return number_of_posts, post_dict_list

posts,post_dict_list = get_forum_posts()

if posts >= 1:
    # SEND MAILS
    html = "<html><head></head><body><p>Bonjour,<br/><br />il y a {posts} message(s) qui a/ont été posté(s) par benissanwi_ASSZg".format(posts=posts)

    # Add list of links
    html +="<br/><br/>Voici les liens d'accès direct aux fils de discussion et leur contenu.<br/>"
    for post_dict in post_dict_list:
        html += '<br/>- Message envoyé le : '+ post_dict['created_at'] + '<br/>'
        html += '<br/>'+ post_dict['message'] + '<br/>'
        html += '<br/><a href="' + post_dict['url'] + '"> Lien vers le forum </a><br/>'
        html += '<br/>---------------------------------------------------------------<br/>'

    html += "</p></body></html>"

    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

    for i in range(len(TO_EMAILS)):
        fromaddr = "Weuplearning <ne-pas-repondre@weuplearning.com>"
        toaddr = str(TO_EMAILS[i])
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Posts forum sur e-formation.artisanat' - " + time.strftime("%d.%m.%Y")
        part = MIMEBase('application', 'octet-stream')
        server = smtplib.SMTP('mail3.themoocagency.com', 25)
        server.starttls()
        server.login('contact', 'waSwv6Eqer89')
        msg.attach(part2)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        log.info('[WUL] : Email sent to '+toaddr)

# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/e-formation-artisanat/utils/posts_tracker.py