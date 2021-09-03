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

try:
    course_ids = sys.argv[1].split(';')
except:
    pass
    course_ids = ""

try:
    register_users = sys.argv[2]
    if register_users == "true":
        register_users = True
    else:
        register_users = False
except:
    register_users = None

try:
    certificate_users = sys.argv[3]
    if certificate_users == "true":
        certificate_users = True
    else:
        certificate_users = False
except:
    certificate_users = None

try:
    persistent = sys.argv[4]
    if persistent == "true":
        persistent = True
    else:
        persistent = False
except:
    persistent = None

try:
    graded = sys.argv[5]
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
    cohort_names = sys.argv[6]
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
timesfr = time.strftime("%Y_%m_%d")
timestr = str(timesfr)

wb = Workbook(encoding='utf-8')
sheet = wb.add_sheet('Rapport')
filename = '/edx/var/edxapp/media/microsite/cfe-cgc/reports/{}_Egalite_Professionnelle.xls'.format(timestr)

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
# _mongo = ensure_form_models()
# db = 'ensure_form'
# collection = 'certificate_form'
# _mongo.connect(db=db,collection=collection)
# _mongo.microsite = domain_prefix

headers = ["Identifiant","Email","Prénom", "Last Name","Êtes vous salarié?","Genre", "Tranche d'âge", "Code Postal","Date d'inscription","Dernière visite"]
# headers = ["ID","First Name", "Last Name","Email Address","Registration Date","Last Visit","Number of Visits", "Total time spent on SPOC (min)"]

courses_length = {}

all_users_data = {}
for course_id in course_ids:
    course_key = CourseKey.from_string(course_id)
    course_overview = CourseOverview.get_from_id(course_key)
    course = get_course_by_id(course_key)

    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    # add course headers
    user_repports_summary = course_enrollments[0]
    user_summary=user_repports_summary.user
    if graded:
        header_summary_base=CourseGradeFactory().create(user_summary, course).grade_value['grade_breakdown'].keys()


        # headers.append("Time spent on "+name+" "+version + " (min)")
        for i, header in enumerate(header_summary_base):
            headers.append(header)
            i += 1
        courses_length[course_id] = i + 1
        headers.append(header)


    for i in range(len(course_enrollments)):
        user = course_enrollments[i].user
        tma_enrollment,is_exist=TmaCourseEnrollment.objects.get_or_create(course_enrollment_edx=course_enrollments[i])

        # Create a new user_data
        user_data = {}

        # user is not yet saved
        if str(user.id) not in all_users_data.keys():


            # Update object with user data without grades
            try:
                user_data["first_name"] = json.loads(user.profile.custom_field)['first_name'].capitalize()
            except:
                user_data["first_name"] = "n/a"

            try:
                user_data["last_name"] = json.loads(user.profile.custom_field)['last_name'].capitalize()
            except:
                user_data["last_name"] = "n/a"

            try:
                user_data["age"] = json.loads(user.profile.custom_field)['age'].capitalize()
            except:
                user_data["age"] = "n/a"

            try:
                user_data["gender"] = json.loads(user.profile.custom_field)['gender'].capitalize()
            except:
                user_data["gender"] = "n/a"
                
            try:
                user_data["salarie"] = json.loads(user.profile.custom_field)['salarie'].capitalize()
            except:
                user_data["salarie"] = "n/a"
                
            try:
                user_data["code"] = json.loads(user.profile.custom_field)['code'].capitalize()
            except:
                user_data["code"] = "n/a"
                

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

            # Time tracking
            # try:
            #     seconds = tma_enrollment.global_time_tracking
            #     minute = seconds // 60
            #     user_data["time_tracking_"+ course_id] = int(minute)
            # except:
            #     user_data["time_tracking_"+ course_id] = int(0)

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
            # try:
            #     seconds = tma_enrollment.global_time_tracking
            #     minute = seconds // 60
            # except:
            #     minute = 0

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
            # all_users_data[str(user.id)]["time_tracking_"+ course_id]=int(minute)

# log.info(all_users_data)



# WRITE FILE
for i, header in enumerate(headers):
    # log.info("header")
    # log.info(header)
    sheet.write(0, i, header)

j = 1
for index, user in all_users_data.items():

    # headers = ["Identifiant","Email","Prénom", "Last Name","Êtes vous salarié?","Genre", "Tranche d'âge", "Code Postal","Date d'inscription","Dernière visite"]

    sheet.write(j, 0, user["id"])
    sheet.write(j, 1, user["email_address"])
    sheet.write(j, 2, user["first_name"])
    sheet.write(j, 3, user["last_name"])
    sheet.write(j, 4, user["salarie"])
    sheet.write(j, 5, user["gender"])
    sheet.write(j, 6, user["age"])
    sheet.write(j, 7, user["code"])
    sheet.write(j, 8, user["registration_date"], style1)
    sheet.write(j, 9, user["last_visit"], style1)
    i=10

    for course in course_ids:

        if course in user :
            # sheet.write(j, i, user["time_tracking_"+course])
            # total_time += int(user["time_tracking_"+course])
            for k, grade in enumerate(user[course]):
                sheet.write(j, (i+k), grade)
                # sheet.write(j, (i+k+1), grade)
        else:
            sheet.write(j, i, int(0))
            # for each grade in this course
            for k, elem in enumerate(range(courses_length[course])):
                sheet.write(j, (i+k) , int(0))
                # sheet.write(j, (i+k+1) , int(0))
        i = i + courses_length[course]
        # i = i + courses_length[course]+1
    # sheet.write(j, 7, total_time)
    j = j+ 1

    

wb.save(filename)

# output = BytesIO(filename)
# wb.save(output)






# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/cfe-cgc/utils/report_for_media.py "course-v1:cfe-cgc+MOOC1+2019" false false true true false
