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

# Get headers
HEADERS_GLOBAL = []
HEADERS_USER = [u"Prénom", u"Nom", u"Email", u"position", u"Date d'inscription",u"Dernière connexion"]

HEADERS_FORM = []

headerNoGradesLen = len(HEADERS_USER) + len(HEADERS_FORM)

HEADER = HEADERS_USER

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

def get_user_info(user):
    user_profile = {}
    email = user.email
    custom_field = {}
    certificate_field = {}

    user_id = str(user.id)
    user_profile = UserProfile.objects.get(user_id=user_id)

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except:
        pass

    form_factory.user_id = long(user_id)
    
    if user.first_name:
        first_name = user.first_name
    elif custom_field :
        first_name = custom_field.get('first_name', 'n/a')
    else:
        first_name = "n/a"

    if user.last_name:
        last_name = user.last_name
    elif custom_field :
        last_name = custom_field.get('last_name', 'n/a')
    else:
        last_name = "n/a"

    try:
        date_inscription = user.date_joined.strftime('%d %b %y')
    except:
        date_inscription = "n/a"

    try:
        last_login = user.last_login.strftime('%d %b %y')
    except:
        last_login = "n/a"

    try:
        position = custom_field.get('bnpp_entity', 'n/a')
    except:
        position = "n/a"
        
    user_row = [first_name, last_name, email, position, date_inscription, last_login]
    
    # CUSTOM FIELDS INFO
    for field in HEADERS_FORM:
        try:
            user_row.append(custom_field[field])
        except:
            user_row.append('n/a')

    return user_row

def get_best_date(dateA, dateB):
    earliest_date = ''
    dateA_valid = False
    dateB_valid = False

    if dateA and dateA != '':
        dateA_valid = True
    if dateB and dateB != '':
        dateB_valid = True

    if dateA_valid and not dateB_valid:
        earliest_date = dateA
    else:
        earliest_date = dateB

    return earliest_date

def is_sections_valid(sections):
    valid = True
    invalid_values = ['', 'n/a', [''], ['n/a']]
    if not isinstance(sections, list) or sections in invalid_values:
        valid = False
    return valid

def is_date(value):
    is_date = False
    p = re.compile('\d+[-]\d+[-]\d+')
    if p.match(value):
        is_date = True
    return is_date

def get_best_grade_date_or_sections_number(sectionsA, sectionsB):
    if len(sectionsA)==1 and isinstance(sectionsA[0], str) and is_date(sectionsA[0]):
        return sectionsA[0]
    
    elif len(sectionsB)==1 and isinstance(sectionsB[0], str) and is_date(sectionsB[0]):
        return sectionsB[0]
    
    else:
        return get_sections_number(sectionsA, sectionsB)

def get_sections_number(sectionsA, sectionsB):
    total_sections = 'n/a'

    if is_sections_valid(sectionsA) and not is_sections_valid(sectionsB):
        total_sections = sectionsA

    if not is_sections_valid(sectionsA) and is_sections_valid(sectionsB):
        total_sections = sectionsB
    
    if is_sections_valid(sectionsA) and is_sections_valid(sectionsB):
        sectionsA.extend(x for x in sectionsB if x not in sectionsA)
        total_sections = sectionsA

    if total_sections != 'n/a':
        total_sections = str(len(total_sections))
    else:
        total_sections = ''
    return total_sections

def get_best_grade_date(user, course_id, course_grade):
    tma_enrollment=TmaCourseEnrollment.get_enrollment(course_id=course_id, user=user)
    if tma_enrollment.best_grade_date == None and (course_grade.percent>0 or tma_enrollment.best_grade>0):
        tma_enrollment.best_grade_date = datetime.now()
        tma_enrollment.save()
    grade_date = tma_enrollment.best_grade_date.strftime('%d-%m-%y')
    return grade_date

#### TRUE SCRIPT

users_data = {}

j=0
for j in range(len(course_ids)):
    course_name = course_ids[j].keys()[0]
    HEADER.append(course_name)
    for course_id in course_ids[j][course_name]:
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key) 

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
            
            if allow_admin_mails or len([ele for ele in admin_mail_list if(ele in user.email)]) == 0:
                # If the user has never been seen before get its basic info
                if user.id not in users_data.keys():
                    # USER INFO
                    users_data[user.id] = get_user_info(user)
                    for k in range(j):
                        users_data[user.id].append('n/a')
                # get list of sections in "journey" and "expeditions"
                # GET GRADES
                course_value = ''
                try:
                    course_grade = CourseGradeFactory().create(user, course)
                    if course_name == "journey" or course_name == "expeditions" and not course_grade.passed:
                        grade_summary={}
                        passed_exercices=[]
                        for section_grade in course_grade.grade_value['section_breakdown']:
                            grade_summary[section_grade['category']]=section_grade['percent']

                        for section in sorted(grade_summary):
                            grade_value = grade_summary[section]
                            if grade_value > 0.7 :
                                passed_exercices.append(section)
                        course_value = len(passed_exercices)
                    else:
                        course_value = get_best_grade_date(user, course_id, course_grade)
                except:
                    pass

                if course_value != '' and course_value != [] and len(users_data[user.id]) < (headerNoGradesLen + j+1):
                    users_data[user.id].append(course_value)

    #Set default value for unenrolled users
    for user in users_data.keys():
        if len(users_data[user]) < (headerNoGradesLen + j+1) :
            users_data[user].append('n/a')

# WRITE GLOBAL FILE
# Prepare workbook
wb = Workbook(encoding='utf-8')
sheet = wb.add_sheet('Rapport')
style_title = easyxf('font: bold 1')
for i in range(len(HEADER)):
    sheet.write(0, i, HEADER[i],style_title)

j = 1
for user in users_data:
    user_data = users_data[user]
    for i in range(len(user_data)):
        try:
            sheet.write(j, i, user_data[i])
        except:
            pass
    j = j + 1
wb.save('/edx/var/edxapp/media/microsite/netexplo/reports/{}_NETEXPLO_ACA.xls'.format(time.strftime("%d.%m.%Y")))
log.info('[WUL] : Global report file written')

# delete old files
two_days_ago = datetime.today() - timedelta(days=1)
try:
    os.remove('/edx/var/edxapp/media/microsite/netexplo/reports/{}_NETEXPLO_ACA.xls'.format(two_days_ago.strftime("%d.%m.%Y")))
except:
    pass