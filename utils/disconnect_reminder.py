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
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
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
from student.views import password_reset_confirm_wrapper
from student.models import *
log = logging.getLogger()

course_id = sys.argv[1]

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
org = course.org
TO_EMAILS = []

#get course enrolls
course_enrollment=CourseEnrollment.objects.filter(course_id=course_key)

#get users that has never been connected
for i in range(len(course_enrollment)):
    user=course_enrollment[i].user
    if user.last_login is None:
        TO_EMAILS.append(user)

if len(TO_EMAILS) >= 1:
    # SEND MAILS
    for i in range(len(TO_EMAILS)):
        user=TO_EMAILS[i]
        uid=int_to_base36(user.id)
        token = default_token_generator.make_token(user)
        reset_password_link = str(reverse(password_reset_confirm_wrapper, args=(uid, token)))

        html = "<html><head></head><body><p>Bonjour,<br /><br />Vous êtes inscrit au cours « Comprendre les enjeux de la sécurité sociale ».<br /><br />Nous avons constaté que vous n’avez pas encore pris le temps de découvrir les contenus.<br /><br />De nombreuses vidéos, textes, activités et quiz sont à votre disposition, 24h/24, n’hésitez pas à les consulter !<br /><br />Et si vous rencontrez des difficultés de connexion, vous pouvez réinitialiser votre mot de passe en cliquant ici :<br /><a href=https://digital-campus-en3s.fr"+reset_password_link+">https://digital-campus-en3s.fr"+reset_password_link+"</a><br /><br />L’équipe pédagogique</p></body></html>"
        part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

        fromaddr = "EN3S <ne-pas-repondre@themoocagency.com>"
        toaddr = str(user.email)
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Venez découvrir les enjeux de la sécurité sociale"
        part = MIMEBase('application', 'octet-stream')
        server = smtplib.SMTP('mail3.themoocagency.com', 25)
        server.starttls()
        server.login('contact', 'waSwv6Eqer89')
        msg.attach(part2)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        log.info("[WUL] Email sent to : {}  (id : {})".format(user.email, str(user.id)))