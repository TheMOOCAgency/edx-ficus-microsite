# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import errno
import logging
import importlib



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from opaque_keys.edx.keys import CourseKey

from student.models import *

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


admin_list = []


j=0
for j in range(len(course_ids)):
    # Course info from argument
    course_id = course_ids[j]
    course_key = CourseKey.from_string(course_id)
    enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    email_services = ["@artisanat", "@cm", "@cmai", "@ccism", "@cma", "@ccima", "@crma", "@cmahc", "@cmar", "@cacima", "@crm" ]

    i = 0
    for i in range(len(enrollments)):
        # FOR DEBUG PURPOSES
        # if i > 50:
        #    break
        user = enrollments[i].user

        user_email = str(user.email)
        domain_email = user_email.split('@')[1]

        user_email = "@" + str(domain_email)
        email_contains_service = any(email_service in user_email for email_service in email_services)

        if email_contains_service:
            if user.email not in admin_list:
                admin_list.append(user.email)

# log.info(admin_list)

filename = "//edx/var/edxapp/secret/microsite/cma/admin_mail.txt"
if not os.path.exists(os.path.dirname(filename)):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

with open(filename, "w") as f:
    for admin in admin_list:
        f.write(admin + "\n")










