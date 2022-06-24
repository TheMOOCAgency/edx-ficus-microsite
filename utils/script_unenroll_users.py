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

# THIS SCRIPT WILL UNENROLL EVERY USER 90 DAYS AFTER THEY HAVE BEEN REGISTERED (FOR THE GIVEN COURSES LIST)

courses_list = sys.argv[1].split(";")

admin_list = ['fsegalen@netexplo.org', 'lnyadanu@netexplo.org', 'eruch-ext@netexplo.org', 'learning@netexplo.org']

for course_id in courses_list:

    # Get enrollment
    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in course_enrollments:

        string_data = str(enrollment)
        date_registration = datetime.strptime(string_data.split(' ')[3].replace('(',''), '%Y-%m-%d')
        
        today =  datetime.now()
        test_substract = (today - date_registration).days

        if test_substract > 90 :
            user = enrollment.user

            if user.email not in admin_list and user.email.find("@weuplearning") == -1 and user.email.find("@themoocagency") == -1 : 
                CourseEnrollment.unenroll_by_email(user.email, course_key)
                log.info(user.email)
                log.info('has been deleted from ')
                log.info(course_id)

log.info('End')


# List of command to execute: 
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/complete-data/utils/script_unenroll_users.py 'course-v1:complete-data+FR+v1;course-v1:complete-data+EN+v1;course-v1:faciliter-transformation+FR+2020;course-v1:faciliter-transformation+EN+2021;course-v1:masterclass5g+5G001+2021_T2'

