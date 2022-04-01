# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import logging
import importlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from enrollment.api import get_enrollments
from student.models import CourseEnrollment
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger()

users_list_to_unsubscribe = [
    "dhayes@allied-glass.com",
    "jbottoms@allied-glass.com",
    "lpearson@allied-glass.com",
    "dkeenan@allied-glass.com"
]

course_ids = [
    "course-v1:tiama+MX403+2018"
]

yopmail_list = User.objects.filter(email__endswith="yopmail.com")

log.info(yopmail_list)

for user_email in users_list_to_unsubscribe:
    log.info(user_email)
    user = User.objects.get(email=user_email)
    # enrollments = get_enrollments(user.username)

    for course_id in course_ids :
        # course_id = enrollment.get('course_details').get('course_id')
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        log.info('[WUL] : {} has been unenrolled from : {}'.format(user_email, course_id))
        CourseEnrollment.unenroll(user, course_id)
    
    # if (len(enrollments) == 0) :
    #     user_id = user.id
    #     User.objects.get(id=user_id).delete()
    #     log.info('[WUL] : Successfully deleted user : {}'.format(user_email))
    # else:
    #     log.error('[WUL] : NOT ALL ENROLLMENTS DELETED FOR USER {}'.format(user_email))


# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/tiama/utils/unsubscribe.py