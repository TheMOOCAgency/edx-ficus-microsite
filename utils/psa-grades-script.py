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
from microsite_configuration.models import Microsite
from itertools import repeat
from student.views import get_course_enrollments
from tma_apps.skill_grade.helpers import SkillGrades
from social.apps.django_app.default.models import UserSocialAuth

#dev Aurelien
from datetime import datetime, timedelta
import pytz

import logging
log = logging.getLogger()

microsite_name = sys.argv[1]
users_file_name = sys.argv[2]
invited_users_file_name = sys.argv[3]
structure_fields=['struct_org1','struct_org2','struct_org3','struct_org4','struct_org5','struct_org6','struct_org7','struct_org8','struct_org9']



class GroupGradesGenerator():
    def __init__(self, microsite_name, users_file_name, invited_users_file_name):
        self.microsite_name = microsite_name
        self.levels = Microsite.objects.get(key=self.microsite_name).values.get('TMA_ASSOCIATED_COURSES').get('parcours')
        self.levels_list = self.getParcoursList()
        self.users_file_name = users_file_name
        self.invited_users_file_name = invited_users_file_name
        self.users_list = self.getUsersList()
    
    def getListOfList(self):
        n=len(max(self.levels,key=len))
        listOfList=[[] for i in repeat(None, n)]
        return listOfList
    
    def initializeAverages(self):
        self.filiere_global={}
        self.filiere_skill={}
        self.group_global={"totalParticipants":0,"totalScore":0}
        self.group_skill={}
        self.userData=[]
        self.levelData={}

    def getParcoursList(self):
        levels_list = self.getListOfList()
        for parcours in self.levels :
            i=0
            for course in parcours:
                try:
                    levels_list[i].append(str(course))
                except:
                    levels_list[i]=[course]
                i+=1
        return levels_list
    
    def getUsersList(self):
        user_file = open("/edx/var/edxapp/secret/microsite/"+microsite_name+"/"+self.users_file_name, "rb")
        users = csv.DictReader(user_file, delimiter=';')
        users_list=[]
        
        invited_users_list=[]
        invited_users_file = open("/edx/var/edxapp/secret/microsite/"+microsite_name+"/"+self.invited_users_file_name, "rb")
        invited_users = csv.DictReader(invited_users_file, delimiter=';')
        for row in invited_users:
            invited_users_list.append(row["Uid"])
        
        for user in users:
            if user["Uid"] in invited_users_list:
                users_list.append(user)
        user_file.close()
        return users_list

    def getCourseRegisteredTo(self, level, user):
        course_id=None
        enrollments = list(get_course_enrollments(user, self.microsite_name, []))
        for enrollment in enrollments :
            if(str(enrollment.course_id) in level) :
                course_id=str(enrollment.course_id)
                break
        return course_id

    def buildGradesFile(self):
        gradesFile = []
        for index,level in enumerate(self.levels_list) :
            log.info("Starting treatment of level {} ----------------------------- ".format(str(index+1)))
            self.initializeAverages()
            self.getEmptySkillGrades(level[0])
            for user in self.users_list :
                log.info("Treating user ----------------------------- {}".format(user['email']))
                if UserSocialAuth.objects.filter(uid=str("psanetxploSAML:"+user['Uid'])).exists():
                #if User.objects.filter(email=user['email']).exists() :
                    user_id = UserSocialAuth.objects.get(uid=str("psanetxploSAML:"+user['Uid'])).user_id
                    tmaUser = User.objects.get(id=user_id)
                    courseRegisteredTo = self.getCourseRegisteredTo(level, tmaUser)
                    log.info("user {} is registered to ----------------------------- {}".format(user['email'], courseRegisteredTo))
                    userResults = self.buildResults(user=user, course_id=courseRegisteredTo, tmaUser=tmaUser) if courseRegisteredTo else self.buildResults(user=user, course_id=level[0], tmaUser=None)
                else:
                    userResults = self.buildResults(user=user, course_id=level[0], tmaUser=None)
                self.userData.append(userResults)
            self.levelData={
                "level":"Level "+str(index+1),
                "userData":self.userData,
                "filiere_skill_average":self.getFiliereSkillAverage(),
                "filiere_average":{index:round(value['totalScore']/value['totalParticipants'],2) if value['totalParticipants']>=3 else 0.55 for (index, value) in self.filiere_global.items()},
                "group_average":round(self.group_global['totalScore']/self.group_global['totalParticipants'],2) if self.group_global['totalParticipants']>=3 else 0.50,
                "group_skill_average":{index:round(value['totalScore']/value['totalParticipants'],2) if value['totalParticipants']>=3 else 0.50 for (index, value) in self.group_skill.items()}
            }
            gradesFile.append(self.levelData)
            log.info("Ending treatment of level {} ----------------------------- ".format(str(index+1)))
        return gradesFile

    def getEmptySkillGrades(self, course_id):
        course = get_course_by_id(CourseKey.from_string(course_id))
        emptySkillGrades = []
        for grader in course._grading_policy.get('RAW_GRADER'):
            emptySkillGrades.append({'name':grader.get('type').lower(),'grade':0})
        self.emptySkillGrades = emptySkillGrades

    def getFiliereSkillAverage(self):
        for key, value in self.filiere_skill.items():
            for index,skill in value.items():
                value[index] = round(skill['totalScore']/skill['totalParticipants'],2) if skill['totalParticipants']>=3 else 0.55
        return self.filiere_skill

    def produceGradesJson(self):
        data = self.buildGradesFile()
        with open("/edx/var/edxapp/secret/microsite/"+microsite_name+"/grades.json", 'w') as outfile:
            json.dump(data, outfile)

    def getCourseStatus(self, tmaEnrollment):
        status="not_started"
        if tmaEnrollment is not None:
            if tmaEnrollment.has_finished_course :
                status="finished"
            elif tmaEnrollment.has_started_course:
                status="ongoing"
        return status

    def buildResults(self, user, course_id, tmaUser=None):
        tmaEnrollment= TmaCourseEnrollment.get_enrollment(user=tmaUser, course_id=course_id) if tmaUser else None
        status = self.getCourseStatus(tmaEnrollment)
        skillGrades = None

        #devAurelien
        if tmaUser:
            #skillGrades = SkillGrades(course_id, tmaUser) if tmaUser else None
            tz_info = tmaUser.last_login.tzinfo
            if tmaUser.last_login < datetime.now(tz_info) - timedelta(10):
                log.info("user did not login since 10 days: "+str(tmaUser.email))
                #user did not login since a long time so if we have his/her skillgrade lets use it
                extra_data = {}
                try:
                    extra_data = json.loads(tmaEnrollment.extra_data)
                except:
                    log.info("ERROR : could not load extra_data for user: "+str(tmaUser.email))
                    pass
                if "skillGrades" in extra_data:
                    skillGrades = extra_data["skillGrades"]
                else:
                    # user did not login since a long time but we have no clue about his results so lets
                    # compute them and also memorize
                    log.info("user did not login since 10 days and we dont know his/her results from extra_data: "+str(tmaUser.email))
                    skillGrades = SkillGrades(course_id, tmaUser)
                    try:
                        extra_data["skillGrades"] = {"global_grade":skillGrades.global_grade,"skill_grades":skillGrades.skill_grades}
                        tmaEnrollment.extra_data = json.dumps(extra_data)
                        tmaEnrollment.save()
                        log.info("user did not login since 10 days and we dont know his/her results from extra_data but we computed it and saved it: "+str(tmaUser.email))
                    except:
                        log.info("ERROR : could not save for old user: "+str(tmaUser.email))
                        pass
                    skillGrades = {"global_grade":skillGrades.global_grade,"skill_grades":skillGrades.skill_grades}
            else:
                #user did login rather "recently" so lets compute his/her skillgrade and memorize it
                skillGrades = SkillGrades(course_id, tmaUser)
                try:
                    extra_data = json.loads(tmaEnrollment.extra_data)
                    extra_data["skillGrades"] = {"global_grade":skillGrades.global_grade,"skill_grades":skillGrades.skill_grades}
                    tmaEnrollment.extra_data = json.dumps(extra_data)
                    tmaEnrollment.save()
                    log.info("user logged in recently so we had to compute and store: "+str(tmaUser.email))
                except:
                    log.info("ERROR : could not load or save data for recent user "+str(tmaUser.email))
                skillGrades = {"global_grade":skillGrades.global_grade,"skill_grades":skillGrades.skill_grades}

        user_object={
            "fields":{
                "id":user['Uid'],
                "first_name":user['first_name'].lower(),
                "last_name":user['last_name'].lower(),
                "localisation":[user['country'],user['location']],
                "position":[user['job_family'],user['profession']],
                "structure":[user[structure] for structure in structure_fields],
                "email":user['email'],
                "has_finished":tmaEnrollment.has_finished_course if tmaEnrollment else False,
                "has_started":tmaEnrollment.has_started_course if tmaEnrollment else False,
                "finished_date":tmaEnrollment.finished_course_date.strftime("%m/%d/%Y") if (tmaEnrollment and tmaEnrollment.finished_course_date ) else "undefined",
                "status":status,
                "progressLink":"/tma_apps/"+course_id+"/skill-radar?user="+str(tmaUser.id) if tmaEnrollment else "no_link"
            },
            "grades":{
                "global":round(skillGrades["global_grade"],2) if tmaUser else 0,
                "skills":skillGrades["skill_grades"] if tmaUser else self.emptySkillGrades
            }
        }
        
        #Group and Filiere Averages
        if status=="finished":
            self.group_global['totalParticipants']+=1
            self.group_global['totalScore']+=user_object['grades']['global']

            for skill in user_object['grades']['skills']:
                self.group_skill.setdefault(skill['name'], {'totalParticipants':0,'totalScore':0})
                self.group_skill[skill['name']]['totalParticipants']+=1
                self.group_skill[skill['name']]['totalScore']+=skill['grade']
            
            self.filiere_global.setdefault(user['job_family'],{'totalParticipants':0,'totalScore':0})
            self.filiere_global[user['job_family']]['totalParticipants']+=1
            self.filiere_global[user['job_family']]['totalScore']+=user_object['grades']['global']

            self.filiere_skill.setdefault(user['job_family'], {})
            for skill in user_object['grades']['skills']:
                self.filiere_skill[user['job_family']].setdefault(skill['name'], {'totalParticipants':0,'totalScore':0})
                self.filiere_skill[user['job_family']][skill['name']]['totalParticipants']+=1    
                self.filiere_skill[user['job_family']][skill['name']]['totalScore']+=skill['grade']

        return user_object  
        
        


       




GroupGradesGenerator(microsite_name, users_file_name,invited_users_file_name).produceGradesJson()

