# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
# from datetime import datetime
# from io import BytesIO


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

#############################################################
#        ^ SETUP ENVIRONNEMENT VARIABLE FOR FICUS ^         #
#                START BEYOND THIS LINE                     #
#############################################################



from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

# import json

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from datetime import timedelta, datetime
# from django.utils import timezone
# import pytz

import logging
log = logging.getLogger()


"""
## FICUS ##

course-v1:campus-fraissinet+sbo2018+sbo2018

sudo -H -u edxapp /edx/app/edxapp/venvs/edxapp/bin/python /edx/app/edxapp/edx-microsite/campus-fraissinet/utils/unenroll_course_enrollment.py 'course-v1:campus-fraissinet+sbo2018+sbo2018'
"""


emails_to_send = ['sysadmin@themoocagency.com']

try:
    courses = sys.argv[1].split(';')
except:
    log.info('********************** Pas de cours **********************')
    courses = []


all_users = []

for course_id in courses:
    # Get enrollment
    log.info('------------course_id------------')
    log.info(course_id)
    all_users.append("</br> <li>"+course_id+"</li> </br>")

    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in course_enrollments:
        try:
            user = enrollment.user
        except:
            log.info('user not found, already delete but still enrolled')
            log.info(enrollment)
            # enrollment.delete()
            continue
        log.info('enrollment :')
        log.info(enrollment)

        # if user.email.find('@weuplearning') != -1 or user.email.find('@themoocagency') != -1 :
        #     continue

        log.info(user.email)


        all_users.append("<li>"+user.email+"</li>")
        log.info('unenroll')
        # CourseEnrollment.unenroll_by_email(user.email, course_key)
        # enrollment.delete()


# WRITE AND SEND EMAILS
unenrolled_users = ''.join(all_users)


if len(all_users) > len(courses) :
    html = "<html><head></head><body><p>Bonjour,<br/><br/>  Voici la liste des "+str(len(all_users)-len(courses))+" utilisateurs avec une date d'inscription dépassant le délai autorisé de 3 mois, et qui ont donc été désinscrits " + unenrolled_users + "<br/>Bonne r&eacute;ception<br/>L'&eacute;quipe WeUp Learning</p></body></html>"


    for email in emails_to_send:
        part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')
        fromaddr = "ne-pas-repondre@themoocagency.com"
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = email
        msg['Subject'] = "Rapport du script de suppression"
        server = smtplib.SMTP('mail3.themoocagency.com', 25)
        server.starttls()
        server.login('contact', 'waSwv6Eqer89')
        msg.attach(part2)
        text = msg.as_string()
        server.sendmail(fromaddr, email, text)
        server.quit()


        log.info('Email sent to '+str(email))

