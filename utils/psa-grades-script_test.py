#!/usr/bin/env python

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

import csv
import sys
import json
from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from courseware.courses import get_course_by_id
from tma_apps.models import TmaCourseEnrollment
from student.models import CourseEnrollment

import logging
log = logging.getLogger()


json_settings = json.load(open("/edx/var/edxapp/media/microsite/psa-netexplo/config/platform_stats_settings.json"))
courses_ids=json_settings['courses_ids']

user_file = open("/edx/var/edxapp/secret/microsite/psa-netexplo/culture_digitale_export_test.csv", "rb")
psa_users = csv.DictReader(user_file, delimiter=';')
psa_users_list=[]
for psa_user in psa_users:
    psa_users_list.append(psa_user)
user_file.close()
structure_fields=['struct_org1','struct_org2','struct_org3','struct_org4','struct_org5','struct_org6','struct_org7','struct_org8','struct_org9']


users_data=[]
group_average={"percent":0,"participants":0}
group_skill_average={}
filiere_average={}
filiere_skill_average={}

fake_group_average=0.5
fake_filiere_average=0.55

users_treated=[]



for course_id in courses_ids:
    log.info("Psa grade script for course_id ----------------------------- {}".format(course_id))
    course_key=CourseKey.from_string(course_id)
    course=get_course_by_id(course_key)

    #Grading Policy
    graders=course._grading_policy.get('RAW_GRADER')
    skill_weight={}
    for grader in graders:
      skill_weight[grader.get('type').lower()]=grader.get('weight')

    for psa_user in psa_users_list:
        user_object={}
        if not psa_user['email'] in users_treated:
            log.info("Treating user {} ----------------------------------------------------".format(psa_user['email']))
            if User.objects.filter(email=psa_user['email']).exists() :
                log.info("user exists in db")
                current_user=User.objects.get(email=psa_user['email'])
                log.info("current_user {} -----------------------------".format(current_user))
                if CourseEnrollment.is_enrolled(current_user, course_key) :
                    courseEnrollment = TmaCourseEnrollment.get_enrollment(course_id=course_id, user=current_user)
                    if courseEnrollment :
                        if courseEnrollment.has_finished_course is True:
                            status='finished'
                        elif courseEnrollment.has_started_course is True:
                            status='ongoing'
                        else :
                            status="not_started"
                    else:
                        status='not_started'
                    #log.info("status {}".format(status))

                    user_filiere=psa_user['job_family']
                    grade_info = CourseGradeFactory().create(current_user, course)
                    chapter_grades = grade_info.chapter_grades

                    skill_points={}
                    user_skill_averages=[]
                    if chapter_grades:
                      for chapter in chapter_grades:
                        for section in chapter['sections']:
                            if section.format is not None and len(section.scores) > 0:
                                skill_name=section.format.lower()
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

                        if status=="finished":
                            filiere_skill_average.setdefault(user_filiere,{})
                            filiere_skill_average[user_filiere].setdefault(skill, {'percent':0,'participants':0})
                            filiere_skill_average[user_filiere][skill]['percent']+=skill_percent
                            filiere_skill_average[user_filiere][skill]['participants']+=1

                            group_skill_average.setdefault(skill, {'percent':0,'participants':0})
                            group_skill_average[skill]['percent']+=skill_percent
                            group_skill_average[skill]['participants']+=1

                    #Get global grade
                    user_global_grade=0
                    for skill in user_skill_averages:
                        user_global_grade+=(skill['grade']*skill_weight[skill['name']])
                    #log.info("user_global_grade {}".format(user_global_grade))

                    if status=="finished":
                        group_average['percent']+=user_global_grade
                        group_average['participants']+=1

                        filiere_average.setdefault(user_filiere, {'percent':0,'participants':0})
                        filiere_average[user_filiere]['percent']+=user_global_grade
                        filiere_average[user_filiere]['participants']+=1

                    user_object={
                    "fields":{
                        "id":psa_user['Uid'],
                        "first_name":psa_user['first_name'].lower(),
                        "last_name":psa_user['last_name'].lower(),
                        "localisation":[psa_user['country'],psa_user['location']],
                        "position":[psa_user['job_family'],psa_user['profession']],
                        "structure":[psa_user[structure] for structure in structure_fields],
                        "email":psa_user['email'],
                        "has_finished":courseEnrollment.has_finished_course if courseEnrollment else False,
                        "has_started":courseEnrollment.has_started_course if courseEnrollment else False,
                        "finished_date":courseEnrollment.finished_course_date.strftime("%m/%d/%Y") if (courseEnrollment and courseEnrollment.finished_course_date ) else "undefined",
                        "tmaId":current_user.id,
                        "course_id":course_id,
                        "status":status,
                        "progressLink":"/tma_apps/"+str(course_id)+"/skill-radar?user="+str(current_user.id)
                    },
                    "grades":{
                        "global":round(user_global_grade,2),
                        "skills":user_skill_averages
                    }
                    }

                    log.info("user_object {}".format(user_object))
                    users_data.append(user_object)
                    users_treated.append(psa_user['email'])
                    log.info("Appended user {} ----------------------------------------------------".format(psa_user['email']))
            else :
                log.info("user doesn't exist in db")
                user_skill_averages=[]
                for skill_name, skill_percent in skill_weight.items():
                    user_skill_averages.append({"name":skill_name,"grade":0})

                user_object={
                "fields":{
                    "id":psa_user['Uid'],
                    "first_name":psa_user['first_name'].lower(),
                    "last_name":psa_user['last_name'].lower(),
                    "localisation":[psa_user['country'],psa_user['location']],
                    "position":[psa_user['job_family'],psa_user['profession']],
                    "structure":[psa_user[structure] for structure in structure_fields],
                    "email":psa_user['email'],
                    "has_finished":False,
                    "has_started":False,
                    "finished_date":"undefined",
                    "tmaId":"undefined",
                    "course_id":course_id,
                    "status":"not_started",
                    "progressLink":"#"
                },
                "grades":{
                    "global":0,
                    "skills":user_skill_averages
                }
                }

                log.info("user_object {}".format(user_object))
                users_data.append(user_object)
                users_treated.append(psa_user['email'])
                log.info("Appended user {} ----------------------------------------------------".format(psa_user['email']))



#Filiere Average
for filiere_name, filiere_values in filiere_average.items():
    if filiere_values['participants']>=3:
        filiere_average[filiere_name]=round(filiere_values['percent']/filiere_values['participants'],2)
    else :
        filiere_average[filiere_name]=fake_filiere_average

#Filiere Skill Averages
for filiere_name, filiere_values in filiere_skill_average.items():
    for filiere_skill_name, filiere_skill_value in filiere_values.items():
        if filiere_skill_value['participants']>=3:
            filiere_skill_average[filiere_name][filiere_skill_name]=round(filiere_skill_value['percent']/filiere_skill_value['participants'],2)
        else :
            filiere_skill_average[filiere_name][filiere_skill_name]=fake_filiere_average

#Group Average
if group_average['participants']>=3:
    group_average=round(group_average['percent']/group_average['participants'], 2)
else :
    group_average=fake_group_average

#Group Skill Averages
for skill_name, skill_values in group_skill_average.items():
    if skill_values['participants']>=3:
        group_skill_average[skill_name]=round(skill_values['percent']/skill_values['participants'],2)
    else :
        group_skill_average[skill_name]=fake_group_average

json_data={
    "userData":users_data,
    "group_average":group_average,
    "group_skill_average":group_skill_average,
    "filiere_average":filiere_average,
    "filiere_skill_average":filiere_skill_average
}

with open("/edx/var/edxapp/secret/microsite/psa-netexplo/grades_test.json", 'w') as outfile:
    json.dump(json_data, outfile)

with open("/edx/var/edxapp/secret/microsite/psa-netexplo/emails_test.json", 'w') as f:
    for e in users_treated:
        f.write("%s\n" % e)