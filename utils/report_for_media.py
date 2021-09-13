# -*- coding: utf-8 -*-
#!/usr/bin/env python
from __future__ import division

import sys

from xlwt.antlr import ifelse
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import csv
import time
import os
import json
import logging
# import string
from collections import OrderedDict


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

# from django.core.management import execute_from_command_line
# import django

##USE EDX FUNCTIONS
from opaque_keys.edx.keys import CourseKey
# from courseware.access import has_access
# from lms.djangoapps.ccx.utils import prep_course_for_grading
# from lms.djangoapps.courseware import courses
# from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory, CourseGrade
# from lms.djangoapps.tma_stat_dashboard.grade_reports import grade_reports
# from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
# from openedx.core.djangoapps.course_groups.models import CohortMembership, CourseUserGroup
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
# from student.roles import CourseStaffRole
from student.models import *
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
from tma_apps.best_grade.helpers import check_best_grade
from lms.djangoapps.grades.context import grading_context_for_course
from courseware.user_state_client import DjangoXBlockUserStateClient



from datetime import datetime
from xlwt import *


from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)
# from tma_apps.files_api.models import mongofiles
# from tma_apps.models import TmaCourseEnrollment

log = logging.getLogger()

try:
    course_ids = sys.argv[1].split(';')
except:
    course_ids = 'course-v1:cfe-cgc+MOOC1+2019'

# WORKBOOK
timesfr = time.strftime("%Y_%m_%d")
timestr = str(timesfr)

wb = Workbook(encoding='utf-8')
sheet = wb.add_sheet('Rapport')
# filename = '/home/edxtma/csv/{}_Egalite_Professionnelle.xls'.format(timestr)
filename = '/edx/var/edxapp/media/microsite/cfe-cgc/reports/{}_Egalite_Professionnelle.xls'.format(timestr)

# Course_ids must be from same platform : getting microsite via first course_id in list
course_key = CourseKey.from_string(course_ids[0])
course = get_course_by_id(course_key)
# Get microsite
org = course.org
query = "SELECT a.id,a.organization,b.key FROM microsite_configuration_micrositeorganizationmapping a,microsite_configuration_microsite b WHERE a.microsite_id = b.id"
microsite_list = MicrositeOrganizationMapping.objects.raw(query)
microsite_name = None
for row in microsite_list:
    if row.organization == org:
        microsite_name = row.key
domain_prefix = None
# register_form = None
certificate_form = None
microsite = Microsite.objects.get(key=microsite_name)
microsite_value = microsite.values
i=0
for val in microsite_value:
    if val == 'domain_prefix':
        domain_prefix = microsite_value.values()[i]
    # if val == 'FORM_EXTRA':
    #     register_form = microsite_value.values()[i]
    if val == 'CERTIFICATE_FORM_EXTRA':
        certificate_form = microsite_value.values()[i]
    i=i+1

# Mongo certificate_form models
_mongo = ensure_form_models()
db = 'ensure_form'
collection = 'certificate_form'
_mongo.connect(db=db,collection=collection)
_mongo.microsite = domain_prefix


all_users_data = {}
header_question = []

first = True


for course_id in course_ids:
    course_key = CourseKey.from_string(course_id)
    course_overview = CourseOverview.get_from_id(course_key)
    course = get_course_by_id(course_key)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    
    # add course headers
    user_repports_summary = course_enrollments[0]
    user_summary=user_repports_summary.user


    for i in range(len(course_enrollments)):
        user = course_enrollments[i].user

        if user.email.find('@yopmail') >0 : 
            continue

        # Create a new user_data
        user_data = {}        

        # Update object with user data without grades
        try:
            user_data["first_name"] = json.loads(user.profile.custom_field)['first_name'].capitalize()
        except:
            user_data["first_name"] = "n.a."

        try:
            user_data["last_name"] = json.loads(user.profile.custom_field)['last_name'].capitalize()
        except:
            user_data["last_name"] = "n.a."

        try:
            user_data["age"] = json.loads(user.profile.custom_field)['age'].capitalize()
        except:
            user_data["age"] = "n.a."

        try:
            user_data["gender"] = json.loads(user.profile.custom_field)['gender'].capitalize()
        except:
            user_data["gender"] = "n.a."
            
        try:
            user_data["salarie"] = json.loads(user.profile.custom_field)['salarie'].capitalize()
        except:
            user_data["salarie"] = "n.a."
            
        try:
            user_data["code"] = json.loads(user.profile.custom_field)['code'].capitalize()
        except:
            user_data["code"] = "n.a."
            

        try:
            user_data["registration_date"] = user.date_joined.strftime('%d/%m/%Y')
            # user_data["registration_date"] = datetime.strptime(user.date_joined.strftime('%d/%m/%Y'), '%d/%m/%Y') 
        except:
            # should not occured
            user_data["registration_date"] = "n.a."    

        try:
            user_data["last_visit"] = user.last_login.strftime('%d/%m/%Y')
        except:
            try:
                user_data["last_visit"] = user.date_joined.strftime('%d/%m/%Y')
            except:
                # should not occured
                user_data["last_visit"] = "n.a."

        user_data["id"] = user.id
        user_data["email_address"] = user.email


   
        course_grade = CourseGradeFactory().create(user, course)


        user_data["final_grade"] = str(course_grade.grade_value['percent']*100) +'%'

        if course_grade.grade_value['grade'] == "Pass":
            user_data["attestation"] = "Oui"
        else:
            user_data["attestation"] = "Non"
    
    
        locations_to_scores = (course_grade.chapter_grades[0]['sections'][0].locations_to_scores)
        
        # Access Section
        scorable_block_titles = OrderedDict()
        grading_context = grading_context_for_course(course_key)



        for assignment_type_name, subsection_infos in grading_context['all_graded_subsections_by_type'].iteritems():
            for subsection_index, subsection_info in enumerate(subsection_infos, start=1):
                for scorable_block in subsection_info['scored_descendants']:
                    header_name = (
                        u"{assignment_type} {subsection_index}: "
                        u"{subsection_name} - {scorable_block_name}"
                    ).format(
                        scorable_block_name=scorable_block.display_name,
                        assignment_type=assignment_type_name,
                        subsection_index=subsection_index,
                        subsection_name=subsection_info['subsection_block'].display_name,
                    )
                    scorable_block_titles[scorable_block.location] = header_name
                    section_name = scorable_block.display_name
                    

        user_grade = check_best_grade(user, course, force_best_grade=True)

        user_state_client = DjangoXBlockUserStateClient()

        questions = []

        # Average calculation
        answered_total = 0
        chapters = [1, 2]

        grades = {}

        for chapter in chapters:
            
            grade_list = []
            for unit in user_grade.chapter_grades[chapter]['sections']:

                for grade in unit.scores:
                    if grade.attempted: 
                        grade = int(grade.earned)
                    else:
                        grade = 'n.a.'
                
                
                    grade_list.append(grade)
            

            grades[chapter] = grade_list

        if first :
            for block_location,block_title in scorable_block_titles.items():

                header_question.append(str(block_title))
                first = False

    
        data = {"grades": grades, "general": user_data}

        all_users_data[str(user.id)]= data
        



# WRITE FILE
headers = ["Identifiant","Email","Prénom", "Nom de famille","Êtes-vous salarié?","Genre","Tranche d'âge","Code postal","Date d'inscription","Dernière connexion"]



j = 0
i = 0
for i, header in enumerate(headers):
    sheet.write(0, i, header)

i=10
for question in header_question:

    sheet.write(0, i, question)

    i += 1

sheet.write(0, 37, "Note finale")
sheet.write(0, 38, "Attestation")


j = 0
for index, user in all_users_data.items():


    sheet.write(j+1, 0, user["general"]["id"])
    sheet.write(j+1, 1, user["general"]["email_address"])
    sheet.write(j+1, 2, user["general"]["first_name"])
    sheet.write(j+1, 3, user["general"]["last_name"])
    sheet.write(j+1, 4, user["general"]["salarie"])
    sheet.write(j+1, 5, user["general"]["gender"])
    sheet.write(j+1, 6, user["general"]["age"])
    sheet.write(j+1, 7, user["general"]["code"])
    try:
        sheet.write(j+1, 8, user["general"]["registration_date"])
        # cell.number_format = 'YYYY MMM DD'
    except:
        sheet.write(j+1, 8, "n.a.")

    try:
        sheet.write(j+1, 9, user["general"]["last_visit"])
        # sheet.write(j+1, 9, user["general"]["last_visit"], style1)
    except:
        sheet.write(j+1, 9, "n.a.")

    sheet.write(j+1, 37, user["general"]["final_grade"])
    sheet.write(j+1, 38, user["general"]["attestation"])
    


    i=10
    for index, chapter in user['grades'].items():
        

        for grade in chapter: 
            sheet.write(j+1, i, grade)
            i += 1

    j += 1


# SAVE FILE
wb.save(filename)
log.info('SCRIPT END')


 
# Last update September 2021, Cyril
 
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/cfe-cgc/utils/test_full_grade.py "course-v1:cfe-cgc+MOOC1+2019" 
