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
from datetime import datetime



from io import BytesIO


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()
#IMPORT TO
##RUN OUTSITE EDX
from django.core.management import execute_from_command_line
import django
##USE EDX FUNCTIONS
from opaque_keys.edx.keys import CourseKey
# from courseware.courses import get_course_by_id
from student.models import CourseEnrollment



import logging
log = logging.getLogger()


courses_list = ['course-v1:complete-data+FR+v1']

for course_id in courses_list:

    # Get enrollment
    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in course_enrollments:
        string_data = str(enrollment)
        # log.info(string_data)
        # log.info(string_data.split(' ')[3].replace('(',''))

        date_registration = datetime.strptime(string_data.split(' ')[3].replace('(',''), '%Y-%m-%d')
        
        today =  datetime.now()

        test_substract = (today - date_registration).days

        if test_substract > 90 :
            log.info('HERE')
            # CourseEnrollment.unenroll_by_email(user.email, course_key)

log.info('End')



# List of command to execute: 

# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/complete-data/utils/script_unenroll_users.py

