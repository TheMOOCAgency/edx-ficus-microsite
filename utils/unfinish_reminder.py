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
from django.conf import settings
from pprint import pformat
from opaque_keys.edx.keys import CourseKey
from student.views import password_reset_confirm_wrapper
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment, UserProfile
log = logging.getLogger()

org = sys.argv[1]

users_infos = []

today = date.today()

#get course overviews
course_overviews=CourseOverview.objects.filter(org=org)
courses_dict=course_overviews.values('id', 'display_name')

for course_dict in courses_dict:
    course_name=course_dict['display_name']
    course_id=course_dict['id']
    course_key=CourseKey.from_string(course_id)
    course=get_course_by_id(course_key)
    days_allowed = configuration_helpers.get_value_for_org(org, 'COURSES_REGISTRATION_PERIOD')
    try: 
        days_allowed_for_course = days_allowed[course_id]
    except:
        days_allowed_for_course = None

    #get course enrolls
    course_enrollments=CourseEnrollment.objects.filter(course_id=course_key)

    #get users that has never been connected
    log.info('[WUL] : {} users in {}'.format(len(course_enrollments),course_enrollments[0].course_id))
    if days_allowed_for_course is not None:
        for course_enrollment in course_enrollments:
            user=course_enrollment.user
            user_profile = UserProfile.objects.get(user=user)
            custom_field = json.loads(user_profile.custom_field)
            start_course_ts=int(custom_field.get(course_id, False))/1000

            if start_course_ts > 0:
                start_course_dt=datetime.fromtimestamp(start_course_ts).date()
                days_passed = today - start_course_dt
                days_passed_int = int(days_passed.days)
                remaining_days = days_allowed_for_course - days_passed_int

                if remaining_days == 15 or remaining_days == 5:
                    course_grade = CourseGradeFactory().create(user, course)
                    if not course_grade.passed:
                        log.info(user)
                        user_info={'user':user,'course_id':course_id,'course_name':course_name, 'remaining_days':remaining_days}
                        users_infos.append(user_info)


if len(users_infos) >= 1:
    # SEND MAILS
    for i in range(len(users_infos)):
        user=users_infos[i]['user']
        course_id=users_infos[i]['course_id']
        course_name=users_infos[i]['course_name']
        remaining_days=users_infos[i]['remaining_days']
        uid=int_to_base36(user.id)
        token = default_token_generator.make_token(user)
        reset_password_link = str(reverse(password_reset_confirm_wrapper, args=(uid, token)))

        html = "<html><head></head><body><p>Bonjour,<br /><br />Il ne vous reste plus que {remaining_days} jours pour finaliser la formation {course_name}.<br />Vous pouvez reprendre dès maintenant votre progression pour finaliser le cours et débloquer l'attestation de réussite :<br /><a href=https://academie-digitale.the-mooc-agency.com/dashboard/{course_id}>https://academie-digitale.the-mooc-agency.com/dashboard/{course_id}</a><br /><br />N’hésitez pas à nous écrire à l’adresse supportdigital@cma-france.fr si vous rencontrez des difficultés pour suivre votre formation.<br /><br />Le réseau des Chambres de Métiers et de l’Artisanat vous souhaite une excellente formation !<br /><br />Sincèrement,<br />L’équipe d’accompagnement des formations digitales du réseau des CMA</p></body></html>".format(remaining_days=remaining_days,course_name=course_name,course_id=course_id)
        part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

        fromaddr = "academie-digitale <ne-pas-repondre@themoocagency.com>"
        toaddr = str(user.email)
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "[academie-digitale] Ne vous arrêtez pas en si bon chemin !"
        part = MIMEBase('application', 'octet-stream')
        server = smtplib.SMTP('mail3.themoocagency.com', 25)
        server.starttls()
        server.login('contact', 'waSwv6Eqer89')
        msg.attach(part2)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        log.info("[WUL] Email sent to : {}  (id : {})".format(user.email, str(user.id)))