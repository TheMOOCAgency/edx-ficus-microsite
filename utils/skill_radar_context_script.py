#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import importlib
from django.core.urlresolvers import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.core.management import execute_from_command_line
import django


from courseware.courses import get_course_by_id
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from edxmako.shortcuts import render_to_response
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from opaque_keys.edx.keys import CourseKey
from tma_apps.models import TmaCourseEnrollment
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.contrib.auth.models import User

import json
import logging
log = logging.getLogger()


#current_user = current_user
current_user=User.objects.get(email="lucie.ory@themoocagency.com")
course_id="course-v1:nautisme-durable+skillquiz+PSA2019"


context={}
course_enrollment = TmaCourseEnrollment.get_enrollment(course_id=course_id, user=current_user)
microsite = configuration_helpers.get_value('domain_prefix')
json_grades= json.load(open("/edx/var/edxapp/secret/microsite/psa-netexplo/grades.json"))

#User info
context['info']={}
try :
    custom_field=json.loads(current_user.profile.custom_field)
except :
    custom_field={}
if custom_field is not None:
    for key,value in custom_field.items() :
        context['info'][key]=value
first_name = current_user.first_name if current_user.first_name !="" else custom_field.get('first_name','unknown')
last_name = current_user.last_name if current_user.last_name !="" else custom_field.get('last_name','unknown')

#User info from grade file
user_filiere="unknown"
for psa_user in json_grades['userData'] :
    if psa_user['fields']['email']==current_user.email :
        user_filiere=psa_user['fields']['position'][0]

context['info']={
    'first_name':first_name,
    'last_name':last_name,
    'filiere':user_filiere
}



current_user=current_user
course_key=CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
courseEnrollment = TmaCourseEnrollment.get_enrollment(course_id=course_id, user=current_user)
grade_info = CourseGradeFactory().create(current_user, course)
chapter_grades = grade_info.chapter_grades

#Grading Policy
graders=course._grading_policy.get('RAW_GRADER')
skill_weight={}
for grader in graders:
  skill_weight[grader.get('type').lower()]=grader.get('weight')

skill_points={}
user_skill_averages=[]
if chapter_grades:
  for chapter in chapter_grades:
    for section in chapter['sections']:
        skill_name=section.format.lower()
        if skill_name is not None and len(section.scores) > 0:
            points_earned=0
            for score in section.scores:
                #Only get score with 100% success
                if score.earned==score.possible:
                    points_earned+=score.earned
            skill_points.setdefault(skill_name, {'total_earned':0,'total_possible':0})
            skill_points[skill_name]['total_earned']+=points_earned
            skill_points[skill_name]['total_possible']+=section.all_total.possible

#Get average grade for each skill
for skill in skill_points :
    skill_percent = round(skill_points[skill].get('total_earned')/skill_points[skill].get('total_possible'),2)
    user_skill_averages.append({"name":skill,"grade":skill_percent})

#Get global grade
user_global_grade=0
for skill in user_skill_averages:
    user_global_grade+=(skill['grade']*skill_weight[skill['name']])

if(course_enrollment and course_enrollment.finished_course_date):
    context['date']={"date_evaluation": course_enrollment.finished_course_date.strftime("%d/%m/%Y")}
else :
    context['date']={"date_evaluation": "unknown"}


context['global_scores']=[
    {"Mon_score_global": user_global_grade},
    {"Moyenne_Groupe": json_grades.get("group_average",0)},
    {"Moyenne_Métier": json_grades.get("filiere_average",{}).get(user_filiere,0)}
]

context['skillGrades']=[]
for skill_info in user_skill_averages:
    if skill_info['grade']>0.7:
        stars=3
    elif skill_info['grade']>=0.4:
        stars =2
    else :
        stars=1

    skill_details={}
    skill_details['name']=skill_info['name']
    skill_details['userGrades']={
        "score":skill_info['grade'],
        "stars":stars,
    }
    skill_details['compare2']=json_grades.get('filiere_skill_average',{}).get(user_filiere,{}).get(skill_info['name'].lower(), 0.5)
    skill_details['compare1']=json_grades.get('group_skill_average',{}).get(skill_info['name'].lower(), 0.55)
    skill_details['user']=skill_info['grade']
    context['skillGrades'].append(skill_details)

context['globalGrades']=[
    {"value": user_global_grade, "name":"user"},
    {"value": json_grades.get("filiere_average",{}).get(user_filiere,0), "name":"compare2"},
    {"value": json_grades.get("group_average",0), "name":"compare1"},
]
if user_global_grade>0.7:
    user_global_level=3
elif user_global_grade>=0.4:
    user_global_level =2
else :
    user_global_level=1

context['user_global_level']=user_global_level

context["buttons"]= [
    {"name":"view_answers", "icon":"fas fa-book-open","link":reverse('courseware', args=[str(course_id)]), "disabled":"false"},
    {"name":"download_page","icon":"fas fa-search", "link": "", "disabled":"false"},
    {"name":"see_last_score","icon":"fas fa-download", "link": reverse('progress', args=[str(course_id)]), "disabled":"true"}
]

#TRANSLATIONS
context['current_language']=course.language
translations= json.load(open("/edx/var/edxapp/media/microsite/psa-netexplo/config/skill_radar_trads.json"))
context['translations']=translations[course.language]




with open("/edx/var/edxapp/secret/microsite/psa-netexplo/context_skill_radar.json", 'w') as outfile:
    json.dump(context, outfile)
