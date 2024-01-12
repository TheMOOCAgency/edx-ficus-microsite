
# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib

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

import json
import logging
log = logging.getLogger()

courses = sys.argv[1].split(';')

with open('/edx/app/edxapp/edx-microsite/handimooc/utils/user_list.json', 'r') as file:
    json_data = file.read()
    users_to_unenroll = json.loads(json_data)

print(users_to_unenroll[0])

for course_id in courses:
    print(course_id)
    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    print(len(course_enrollments))
    
    for enrollment in course_enrollments:
        if getattr(enrollment.user, "email", None) in users_to_unenroll:
            print("ok")
    # for enrollment in course_enrollments:
    #     try:
    #         print(dir(enrollment.user))
    #         user = enrollment.user

    #         # print(user)
    #     except:
    #         pass
