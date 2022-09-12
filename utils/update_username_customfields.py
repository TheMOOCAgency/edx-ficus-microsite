# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import logging
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment, UserProfile


#for pprod
# course_ids=[
#     "course-v1:academie-digitale+FC_B20+FC_B20",
#     "course-v1:academie-digitale+FC_01+FC_01",
#     "course-v1:academie-digitale+FC_B01+FC_B01",
#     "course-v1:academie-digitale+FC_02+FC_02"
#     ]

#for prod
course_ids=[
    "course-v1:academie-digitale+FC_B50+2022",
    "course-v1:academie-digitale+FC_20+2022",
    "course-v1:academie-digitale+FC_B20+2022",
    "course-v1:academie-digitale+FC_B40+2022",
    "course-v1:academie-digitale+FC_B30+2022"
    ]


def get_cf_and_update(user, name, custom_fields, nametype):
    if name == "":
        if custom_fields:
            name = custom_fields.get(nametype)
            if name == "":
                log.info(' -------------- user : '+str(user) + 'has no ' + nametype + ' -----------------')
            else:
                if nametype == 'last_name':
                    user.last_name = name
                else:
                    user.first_name = name
                user.save()
                log.info(' -------------- update ' + nametype + ' for user : '+str(user) + '-----------------')

def udpate_user_data(user):
    try:
        user_profile = UserProfile.objects.get(user_id=user)
        custom_fields = json.loads(user_profile.custom_field)
    except:
        log.info(" ---------------- error when trying to load cutsom field --------------- ")
        pass

    get_cf_and_update(user, user.last_name, custom_fields, 'last_name')
    get_cf_and_update(user, user.first_name, custom_fields, 'first_name')


for course in course_ids:
    course_key = CourseKey.from_string(course)
    enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in enrollments:
        udpate_user_data(enrollment.user)

    
