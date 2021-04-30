# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import csv
import time
import os
import json
import logging

from io import BytesIO

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

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
from courseware.access import has_access
from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
#from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.djangoapps.course_groups.models import CohortMembership, CourseUserGroup
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.roles import CourseStaffRole
from student.models import *
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
from datetime import datetime
from xlwt import *

from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)
from tma_apps.files_api.models import mongofiles
from tma_apps.models import TmaCourseEnrollment

log = logging.getLogger()

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
try:
    course_ids = sys.argv[2].split(';')
except:
    pass
    course_ids = ""

try:
    register_users = sys.argv[3]
    if register_users == "true":
        register_users = True
    else:
        register_users = False
except:
    register_users = None

try:
    certificate_users = sys.argv[4]
    if certificate_users == "true":
        certificate_users = True
    else:
        certificate_users = False
except:
    certificate_users = None

try:
    persistent = sys.argv[5]
    if persistent == "true":
        persistent = True
    else:
        persistent = False
except:
    persistent = None

try:
    graded = sys.argv[6]
    if graded == "true":
        graded = True
    else:
        graded = False
except:
    graded = None

# Cohorts
sort_by_cohort = False
no_cohort = False
cohort_ids = []
try:
    cohort_names = sys.argv[8]
    # If cohort names in argument
    if cohort_names != "":
        cohort_names = cohort_names.split(';')
        sort_by_cohort = True
    else:
        cohort_names = []
        no_cohort = True
except:
    cohort_names = []
    no_cohort = True


# WORKBOOK
timestr = time.strftime("%Y_%m_%d")
timesfr = time.strftime("%d.%m.%Y")
timesfr = str(timesfr)
wb = Workbook(encoding='utf-8')
filename = '/home/edxtma/csv/{}_TIAMA.xls'.format(timestr)

# format date
style1 = XFStyle()
style1.num_format_str = 'DD/MM/YYYY'

# Course_ids must be from same platform : getting microsite via first course_id in list
course_key = CourseKey.from_string(course_ids[0])
course = get_course_by_id(course_key)

#get microsite
org = course.org
query = "SELECT a.id,a.organization,b.key FROM microsite_configuration_micrositeorganizationmapping a,microsite_configuration_microsite b WHERE a.microsite_id = b.id"
microsite_list = MicrositeOrganizationMapping.objects.raw(query)
microsite_name = None
for row in microsite_list:
    if row.organization == org:
        microsite_name = row.key

domain_prefix = None
register_form = None
certificate_form = None

microsite = Microsite.objects.get(key=microsite_name)
microsite_value = microsite.values
i=0
for val in microsite_value:
    if val == 'domain_prefix':
        domain_prefix = microsite_value.values()[i]
    if val == 'FORM_EXTRA':
        register_form = microsite_value.values()[i]
    if val == 'CERTIFICATE_FORM_EXTRA':
        certificate_form = microsite_value.values()[i]
    i=i+1

#mongo certificate_form models
_mongo = ensure_form_models()
db = 'ensure_form'
collection = 'certificate_form'
_mongo.connect(db=db,collection=collection)
_mongo.microsite = domain_prefix

headers = ["ID","First Name", "Last Name","Email Address","Registration Date","Last Visit","Number of Visits", "Total time spent on SPOC (min)"]

courses_length = {}
all_users_data = {}

for course_id in course_ids:
    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    course = get_course_by_id(course_key)
    user_repports_summary = course_enrollments[0]
    user_summary=user_repports_summary.user


    for i in range(len(course_enrollments)):
        user = course_enrollments[i].user
        tma_enrollment,is_exist=TmaCourseEnrollment.objects.get_or_create(course_enrollment_edx=course_enrollments[i])

        # Create a new user_data
        user_data = {}

        # user is not yet saved
        if str(user.id) not in all_users_data.keys():

            # number of connections        
            connections = 1
            try:
                user_ip = UserIpTracking.objects.filter(user=user,microsite=domain_prefix)
                for ip in user_ip:
                    connections = connections + 1
            except:
                pass

            # Update object with user data without grades
            try:
                user_data["first_name"] = json.loads(user.profile.custom_field)['first_name'].capitalize()
                user_data["last_name"] = json.loads(user.profile.custom_field)['last_name'].capitalize()
            except:
                user_data["first_name"] = "n/a"
                user_data["last_name"] = "n/a"

            try:
                user_data["registration_date"] = datetime.strptime(user.date_joined.strftime('%d/%m/%Y'), '%d/%m/%Y') 
            except:
                # should not occured
                user_data["registration_date"] = "n/a"    

            try:
                user_data["last_visit"] = datetime.strptime(user.last_login.strftime('%d/%m/%Y'), '%d/%m/%Y')
            except:
                try:
                    user_data["last_visit"] = datetime.strptime(user.date_joined.strftime('%d/%m/%Y'), '%d/%m/%Y')
                except:
                    # should not occured
                    user_data["last_visit"] = "n/a"

            user_data["id"] = user.id
            user_data["email_address"] = user.email
            user_data["connections"] = connections

            # Time tracking
            try:
                seconds = tma_enrollment.global_time_tracking
                minute = seconds // 60
                user_data["time_tracking_"+ course_id] = int(minute)
            except:
                user_data["time_tracking_"+ course_id] = int(0)

            # ADD GRADES
            course_grades =[]
            
            course_grade = CourseGradeFactory().create(user, course)
            final_grade = course_grade.percent * 100
            for user_summary in course_grade.grade_value['grade_breakdown'].keys():
                summary_percent = course_grade.grade_value['grade_breakdown'].get(user_summary)['percent']
                try:
                    summary_coef = float(course_grade.grade_value['grade_breakdown'].get(user_summary)['detail'].split(' of a possible ')[1].replace('%','')) / 100

                    #Bonus courses with 0 Coef
                    if summary_coef==0:
                        number_sections=0
                        student_score=[]
                        name_section=course_grade.grade_value['grade_breakdown'].get(user_summary)['category']
                        for course_part in course_grade.grade_value['section_breakdown']:
                            if course_part['category'] == name_section:
                                number_sections=number_sections+1
                                student_score.append(course_part['percent'])
                                if number_sections>1:
                                    summary_grade= student_score[number_sections-1]*100
                                else :
                                    summary_grade=student_score[0]*100
                    else:
                        summary_grade = (course_grade.grade_value['grade_breakdown'].get(user_summary)['percent'] / summary_coef) * 100

                    summary_grade = float(int(summary_grade * 100)) / 100
                except:
                    summary_grade = 0.00

                course_grades.append(summary_grade)
            
            course_grades.append(final_grade)

            user_data[str(course_id)] = course_grades
            all_users_data[str(user.id)]=user_data

        # user already saved for another course
        else:
        
            # Time tracking
            try:
                seconds = tma_enrollment.global_time_tracking
                minute = seconds // 60
            except:
                minute = 0

            course_grades =[]
            course_grade = CourseGradeFactory().create(user, course)
            final_grade = course_grade.percent * 100
            for user_summary in course_grade.grade_value['grade_breakdown'].keys():
                summary_percent = course_grade.grade_value['grade_breakdown'].get(user_summary)['percent']
                try:
                    summary_coef = float(course_grade.grade_value['grade_breakdown'].get(user_summary)['detail'].split(' of a possible ')[1].replace('%','')) / 100

                    #Bonus courses with 0 Coef
                    if summary_coef==0:
                        number_sections=0
                        student_score=[]
                        name_section=course_grade.grade_value['grade_breakdown'].get(user_summary)['category']
                        for course_part in course_grade.grade_value['section_breakdown']:
                            if course_part['category'] == name_section:
                                number_sections=number_sections+1
                                student_score.append(course_part['percent'])
                                if number_sections>1:
                                    summary_grade= student_score[number_sections-1]*100
                                else :
                                    summary_grade=student_score[0]*100
                    else:
                        summary_grade = (course_grade.grade_value['grade_breakdown'].get(user_summary)['percent'] / summary_coef) * 100
                    summary_grade = float(int(summary_grade * 100)) / 100

                except:
                    summary_grade = 0.00
                course_grades.append(summary_grade)
            course_grades.append(final_grade)

            all_users_data[str(user.id)][course_id]=course_grades
            all_users_data[str(user.id)]["time_tracking_"+ course_id]=int(minute)

# log.info(all_users_data)

# WRITE FILE
for h, course in enumerate(course_ids):

    course_key = CourseKey.from_string(course)
    course_overview = CourseOverview.get_from_id(course_key)
    # ADD SHEET
    sheet = wb.add_sheet(course_overview.display_name[:30])
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    user_repports_summary = course_enrollments[0]
    user_summary=user_repports_summary.user
    course_name = get_course_by_id(course_key)
    header_summary_base=CourseGradeFactory().create(user_summary, course_name).grade_value['grade_breakdown'].keys()
    
    split = course_name.display_name.split(" - ")
    name = split[1]        
    version = split[0].split(" ")[-1][1:]

    for i, header in enumerate(headers):
        sheet.write(0, i, header)

    section = 0
    for i, header in enumerate(header_summary_base):
        sheet.write(0, (8+i), name + " " + version + " Q"+str(i+1)+" (in %)")
        section += i
    courses_length[course] = section + 1
    sheet.write(0, courses_length[course]+5, name + " " + version + " Final Grade (in %)")
    j = 1

    for index, user in all_users_data.items():
        sheet.write(j, 0, user["id"])
        sheet.write(j, 1, user["first_name"])
        sheet.write(j, 2, user["last_name"])
        sheet.write(j, 3, user["email_address"])
        sheet.write(j, 4, user["registration_date"], style1)
        sheet.write(j, 5, user["last_visit"], style1)
        sheet.write(j, 6, user["connections"])
        try:
            sheet.write(j, 7, user["time_tracking_"+ course])
        except:
            sheet.write(j, 7, int(0))
        i=8

        if course in user :
            for k, grade in enumerate(user[course]):
                sheet.write(j, (i+k), grade)
        else:
            # for each grade in this course
            for k, elem in enumerate(range(courses_length[course]-2)):
                sheet.write(j, (i+k) , int(0))
        i += courses_length[course]+1
        j += 1

# SEND MAILS
output = BytesIO()
wb.save(output)
_files_values = output.getvalue()

course_names = []
course_names_html = []
for course_id in course_ids: 
    course = get_course_by_id(CourseKey.from_string(course_id)) 
    course_names.append(course.display_name_with_default.encode('ascii', errors='xmlcharrefreplace'))
    course_names_html.append("<li>"+ course.display_name_with_default.encode('ascii', errors='xmlcharrefreplace')+"</li>")

course_names_html = ''.join(course_names_html)

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en pièce jointe le rapport de donn&eacute;es des SPOCs : "+ course_names_html +"<br/><br/>Bonne r&eacute;ception<br><br></p><p>---------------------------<br><br>Hello,<br/><br/>You will find attached the data report of the SPOCs : "+ course_names_html +"<br/><br/>Good reception<br><br></p><p>---------------------------<br><br>Buenos dias,<br/><br/>Se adjunta el informe de datos de los SPOC : "+ course_names_html +"<br/><br/>Buena recepción<br><br></p></body></html>"

part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "ne-pas-repondre@themoocagency.com"
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "Tiama - " + ' + '.join(course_names)
   attachment = _files_values
   part = MIMEBase('application', 'octet-stream')
   part.set_payload(attachment)
   encoders.encode_base64(part)
   part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename))
   msg.attach(part)
   server = smtplib.SMTP('mail3.themoocagency.com', 25)
   server.starttls()
   server.login('contact', 'waSwv6Eqer89')
   msg.attach(part2)
   text = msg.as_string()
   server.sendmail(fromaddr, toaddr, text)
   server.quit()
   log.info('Email sent to '+str(TO_EMAILS[i]))


# List of command to execute: 

# 29 March 2021
# sudo -H -u edxapp /edx/bin/python.edxapp /home/edxtma/dev_generic_reports_script/script-tiama-pages.py "thomas.gomes@themoocagency.com;p.raison@tiama.com;R.LECHIFFLART@tiama.com;S.FREIXE.ext@tiama.com;G.GAYTE.ext@tiama.com;T.JEANBLANC@tiama.com" "course-v1:tiama+essais2020+essais2020;course-v1:tiama+prueba2020+prueba2020;course-v1:tiama+trial2020+trial2020" false false true true


#TEST
# sudo -H -u edxapp /edx/bin/python.edxapp /home/edxtma/dev_generic_reports_script/script-tiama-pages.py "cyril.adolf@weuplearning.com" "course-v1:tiama+essais2020+essais2020;course-v1:tiama+prueba2020+prueba2020;course-v1:tiama+trial2020+trial2020" false false true true



