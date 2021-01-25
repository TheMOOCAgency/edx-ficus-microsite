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

from io import BytesIO

import smtplib
import csv
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from datetime import datetime, date
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
string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
org = sys.argv[2]
path_to_utils = '/edx/app/edxapp/edx-microsite/{}/utils/'.format(org)
old_file = path_to_utils + sys.argv[3]
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')
certificate_extra_form = configuration_helpers.get_value_for_org(org, 'CERTIFICATE_FORM_EXTRA')
form_factory = ensure_form_factory()
db = 'ensure_form'
collection = 'certificate_form'
form_factory.microsite = org
allow_admin_mails = True
admin_mail_list = [u"themoocagency", u"weuplearning", u"yopmail"]

# Get headers
HEADERS_GLOBAL = []
HEADERS_USER = [u"Prénom", u"Nom", u"Matricule", u"Email", u"position", u"department", u"region", u"additional_information", u"Date d'inscription",u"Dernière connexion"]

HEADERS_FORM = []
# if register_form is not None:
#     for row in register_form:
#         if row.get('type') is not None:
#             if 'first_name' not in row.get('name') and 'last_name' not in row.get('name'):
#                 HEADERS_FORM.append(row.get('name'))

# NICE_HEADER = list(HEADERS_FORM)

headerNoGradesLen = len(HEADERS_USER) + len(HEADERS_FORM)

# HEADERS_USER.extend(NICE_HEADER)

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
    
    # missing datas
    matricule = "n/a"
    position = "n/a"
    department = "n/a"
    region = "n/a"
    additional_information = "n/a"
        
    user_row = [first_name, last_name, matricule, email, position, department, region, additional_information, date_inscription, last_login]
    
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
    invalid_values = [[''], '', 'n/a']
    if not isinstance(sections, list) or sections in invalid_values:
        valid = False
    return valid

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
            if allow_admin_mails or not user.email in admin_mail_list:
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
                    if course_name == "journey" or course_name == "expeditions":
                        grade_summary={}
                        passed_exercices=[]
                        for section_grade in course_grade.grade_value['section_breakdown']:
                            grade_summary[section_grade['category']]=section_grade['percent']

                        for section in sorted(grade_summary):
                            grade_value = grade_summary[section]
                            if grade_value > 0.7 :
                                passed_exercices.append(section)
                        course_value = passed_exercices
                    else:
                        tma_enrollment=TmaCourseEnrollment.get_enrollment(course_id=course_id, user=user)
                        if tma_enrollment.best_grade_date == None and (course_grade.percent>0 or tma_enrollment.best_grade>0):
                            tma_enrollment.best_grade_date = datetime.now()
                            tma_enrollment.save()
                        course_value = tma_enrollment.best_grade_date.strftime('%d-%m-%y')
                except:
                    pass

                if course_value != '' and course_value != [] and len(users_data[user.id]) < (headerNoGradesLen + j+1):
                    users_data[user.id].append(course_value)

    #Set default value for unenrolled users
    for user in users_data.keys():
        if len(users_data[user]) < (headerNoGradesLen + j+1) :
            users_data[user].append('n/a')

file = open(old_file, "rb")
old_users_datas_list = csv.DictReader(file, delimiter=';')
for old_user in old_users_datas_list:
    in_new_platform = False
    for key in users_data.keys():
        user = users_data[key]
        if user[3] == old_user['email']:
            in_new_platform = True
            first_name = user[0]
            last_name = user[1]
            matricule = old_user['matricule']
            email = user[3]
            position = old_user['position']
            department = old_user['department']
            region = old_user['region']
            additional_information = old_user['additional information']
            date_inscription = old_user['inscrit le']
            last_login = user[9]
            data_IA = get_best_date(user[10], old_user['data-ia'])
            expeditions = get_sections_number(user[11], old_user['expedition'].split(','))
            journey = get_sections_number(user[12], old_user['journey'].split(','))
            manager = get_best_date(user[13], old_user['manager'])
            passeport = get_best_date(user[14], old_user['passport'])
            social_school = get_best_date(user[15], old_user['social-school'])
            users_data[key] = [first_name, last_name, matricule, email, position, department, region, additional_information, date_inscription, last_login, data_IA, expeditions, journey, manager, passeport, social_school]

    if not in_new_platform:
        users_data[old_user['matricule']] = [
            old_user['firstname'],
            old_user['lastname'],
            old_user['matricule'],
            old_user['email'],
            old_user['position'],
            old_user['department'],
            old_user['region'],
            old_user['additional information'],
            old_user['inscrit le'],
            old_user['derniere connexion'],
            old_user['data-ia'],
            get_sections_number(old_user['expedition'].split(','), 'n/a'),
            get_sections_number(old_user['journey'].split(','), 'n/a'),
            old_user['manager'],
            old_user['passport'],
            old_user['social-school']
        ]
file.close()

# WRITE FILE
# Prepare workbook
wb = Workbook(encoding='utf-8')
# filename = '/home/edxtma/csv/{}_{}.xls'.format(org, time.strftime("%d.%m.%Y"))
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
wb.save('/edx/var/edxapp/media/microsite/bnpp-netexplo/reports/{}.xls'.format(org))

# SEND MAILS
# output = BytesIO()
# wb.save(output)
# _files_values = output.getvalue()

# html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de donn&eacute;es </p></body></html>"

# part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

# for i in range(len(TO_EMAILS)):
#     fromaddr = "{} <ne-pas-repondre@themoocagency.com>".format(org)
#     toaddr = str(TO_EMAILS[i])
#     msg = MIMEMultipart()
#     msg['From'] = fromaddr
#     msg['To'] = toaddr
#     msg['Subject'] = "Rapport {} - {}".format(org, time.strftime("%d.%m.%Y"))
#     attachment = _files_values
#     part = MIMEBase('application', 'octet-stream')
#     part.set_payload(attachment)
#     encoders.encode_base64(part)
#     part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename))
#     msg.attach(part)
#     server = smtplib.SMTP('mail3.themoocagency.com', 25)
#     server.starttls()
#     server.login('contact', 'waSwv6Eqer89')
#     msg.attach(part2)
#     text = msg.as_string()
#     server.sendmail(fromaddr, toaddr, text)
#     server.quit()
#     log.info('Email sent to '+str(toaddr))