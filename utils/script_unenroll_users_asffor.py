# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
from datetime import datetime
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
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

import logging
log = logging.getLogger()

# THIS SCRIPT WILL UNENROLL EVERY USER FROM THE STUDENT IMPORT MODULE
# THIS WILL ALLOW THE CLIENT TO REGISTER A SAME USER DIFFERENT TIMES. JUST IN CASE
courses_list = ['course-v1:asffor+01+2022']
admin_list = ['j.bontemps@asf-france.com', 'jsoulie@asf-france.com', 'a.matsakis@asf-france.com', 'm.malivert@asf-france.com']

for course_id in courses_list:
    # Get enrollment
    log.info('Treat course: "%s"', course_id)
    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in course_enrollments:
        # string_data = str(enrollment)
        # date_registration = datetime.strptime(string_data.split(' ')[3].replace('(',''), '%Y-%m-%d')
        # today =  datetime.now()
        # test_substract = (today - date_registration).days
        # if test_substract > 90 :
        #     log.info('Older')
        #     log.info(test_substract)

        user = enrollment.user
        if user.email not in admin_list and user.email.find("@weuplearning") == -1 and user.email.find("@themoocagency") == -1 : 
            CourseEnrollment.unenroll_by_email(user.email, course_key)
            log.info(u"user: '%s' has been deleted from '%s' ", user.email, course_id)

# List of command to execute: 
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/asffor/utils/script_unenroll_users_asffor.py

# Setup everyday at 10pm in crontab
# * 22 * * * sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/asffor/utils/