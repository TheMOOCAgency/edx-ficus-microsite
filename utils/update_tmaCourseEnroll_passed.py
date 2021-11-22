# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import time
import logging
from unidecode import unidecode
from xlwt import *
import re

from io import BytesIO

import smtplib
import csv
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from datetime import datetime, date, timedelta
from dateutil.parser import parse
import copy

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey
from cms.djangoapps.models.settings.course_grading import CourseGradingModel

from student.models import *

from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from lms.djangoapps.grades.context import grading_context_for_course, grading_context
from lms.djangoapps.tma_ensure_form.utils import ensure_form_factory
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from tma_apps.models import TmaCourseEnrollment

from pprint import pformat

# Auxiliary functions
def is_course_open(course):
    now = datetime.now(UTC())
    if course.start > now:
        return False
    else:
        return True

# SET MAIN VARIABLES
org = sys.argv[1]
path_to_utils = '/edx/app/edxapp/edx-microsite/{}/utils/'.format(org)
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')
certificate_extra_form = configuration_helpers.get_value_for_org(org, 'CERTIFICATE_FORM_EXTRA')
form_factory = ensure_form_factory()
db = 'ensure_form'
collection = 'certificate_form'
form_factory.microsite = org
allow_admin_mails = False
admin_mail_list = [u"themoocagency.com", u"weuplearning.com", u"yopmail.com", u"mpsa.com"]


course_ids=[
    { "data-IA":
        [
            "course-v1:netexplo+FR+V1",
            "course-v1:netexplo+EN+V1",
            "course-v1:netexplo+12+ES",
            "course-v1:netexplo+13+DE"
        ]
    },
    { "expeditions":
        [
            "course-v1:netexplo+Netexplo_expedition+2018_T2_expedition",
            "course-v1:netexplo+Netexplo_expeditions_en+2018_T2_expeditions_en",
            "course-v1:netexplo+expeditions+2020_es",
            "course-v1:netexplo+expeditions+2020_de"
        ]
    },
    
    { "journey":
        [
            "course-v1:netexplo+Netexplo_voyages+2018_T2_voyages",
            "course-v1:netexplo+Netexplo_travel+2018_T2_travel",
            "course-v1:netexplo+travel+2020_es",
            "course-v1:netexplo+travel+2020_de"
        ]
    },
    { "manager":
        [
            "course-v1:netexplo+parcours-manager-fr+parcours-manager-fr",
            "course-v1:netexplo+manager+manager-en",
            "course-v1:netexplo+manager+manager-es",
            "course-v1:netexplo+manager+manager-de"
        ]
    },
    {"passeport":
        [
            "course-v1:netexplo+Netexplo_passeport+2018_T2_passeport",
            "course-v1:netexplo+Netexplo_passeport_EN+2018_T2_passeport_EN",
            "course-v1:netexplo+data_ia+2020_ES",
            "course-v1:netexplo+data_ia+2020_DE"
        ]
    },
    { "social-school":
        [
            "course-v1:netexplo+socialschoolfr+SSFR",
            "course-v1:netexplo+socialschoolen+SSEN",
            "course-v1:netexplo+socialschooles+SSES",
            "course-v1:netexplo+socialschoolde+SSDE"
        ]
    }
]

def update_tmaCourseEnrollment(user, course_id):
    tma_enrollment=TmaCourseEnrollment.get_enrollment(course_id=course_id, user=user)
    if tma_enrollment.has_finished_course == False:
        course_grade = CourseGradeFactory().create(user, course)
        print('**********')
        print(course_grade.passed)
        if course_grade.passed:
            tma_enrollment.has_finished_course = True
            tma_enrollment.save()

#### TRUE SCRIPT

users_data = {}

# Now get info for all users enrolled in courses
j=0
for j in range(len(course_ids)):
    course_name = course_ids[j].keys()[0]
    for course_id in course_ids[j][course_name]:
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key) 
        enrollments = CourseEnrollment.objects.filter(course_id=course_key)
        #Get grade for enrolled users
        i = 0
        for i in range(len(enrollments)):
            user = enrollments[i].user
            update_tmaCourseEnrollment(user, course_id)