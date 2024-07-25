# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
# from datetime import datetime
# from io import BytesIO


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

#############################################################
#        ^ SETUP ENVIRONNEMENT VARIABLE FOR FICUS ^         #
#                START BEYOND THIS LINE                     #
#############################################################

import json
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment, UserProfile
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from courseware.courses import get_course_by_id


import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import json
from xlwt import *
import time
#import logging
from util.json_request import JsonResponse
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment, UserProfile
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from courseware.courses import get_course_by_id


    #if request.LANGUAGE_CODE == 'fr':
    #    countries_codes_files = '/edx/var/edxapp/media/microsite-utils/countries_code_fr.json'
    #else:
    #    countries_codes_files = '/edx/var/edxapp/media/microsite-utils/countries_code.json'
countries_codes_files = '/edx/var/edxapp/media/microsite-utils/countries_code.json'
with open(countries_codes_files) as json_file:
    country_codes = json.load(json_file)

def get_custom_field_value(custom_field, value):
    if value in custom_field:
        if value == 'country':
            code = custom_field[value]
            country_name = code
            for key in country_codes:
                if code == key['code']:
                    country_name = key['name']
            return country_name
        else:
            return custom_field[value]
    else:
        return 'n/a'



def main():
    #log = logging.getLogger()

    #alumni_courses_list = ['course-v1:champagne-mooc+004+004']
    #alumni_courses_list = ['course-v1:champagne-mooc+003+003']
    alumni_courses_list = ['course-v1:champagne-mooc+003+003','course-v1:champagne-mooc+004+004']
    
    course_enrollments, first_name, last_name, email, username, city, country, tell_us_more, profile_image_url, mention, linkedin = [], [], [], [], [], [], [], [], [], [], []
    json_alumni_users = ''
    user_is_alumni_registered = False
    country_codes = {}
    test_list = []
    hidden_list = ['theo.gicquel@weuplearning.com']
    print("begin")
    for course_id in alumni_courses_list :
        course_key=CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)
        print("(1)")
        print(course_key)
        current_course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
        print("-------------------------------------------------")
        course_len = len(current_course_enrollments)
        for index,course_enrolls in enumerate(current_course_enrollments):
            user = course_enrolls.user
            
            # if user.email not in hidden_list:

            if user.email in hidden_list:
                pass
            
            custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
            if 'alumni_registered' in custom_field and (custom_field['alumni_registered'] == 'true' or custom_field['alumni_registered'] == 'True' or custom_field['alumni_registered'] == True):
                course_enrollments.append(course_enrolls)
                print("[OK] (" + str(index) + "/" + str(course_len) + ") Got valid profile : " + user.email)
    print("begin last loop")
    total_len = len(course_enrollments)
    for index,course_enrolls in enumerate(course_enrollments):
        user = course_enrolls.user

        #try:
        if(True == True):
            custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
            if 'alumni_registered' in custom_field and (custom_field['alumni_registered'] == 'true' or custom_field['alumni_registered'] == 'True' or custom_field['alumni_registered'] == True):
                test_list.append(get_custom_field_value(custom_field, 'first_name').replace("'","’"))
                email.append(user.email)
                username.append(user.username.replace("'","’"))
                first_name.append(get_custom_field_value(custom_field, 'first_name').replace("'","’"))
                last_name.append(get_custom_field_value(custom_field, 'last_name').replace("'","’"))
                city.append(get_custom_field_value(custom_field, 'city').replace("'","’"))
                country.append(get_custom_field_value(custom_field, 'country').replace("'","’"))
                tell_us_more.append(get_custom_field_value(custom_field, 'tell_us_more').replace("'","’"))
                profile_image_url.append(get_profile_image_urls_for_user(user)['large'])
                if get_custom_field_value(custom_field, 'linkedin') != 'n/a':
                    linkedin.append(get_custom_field_value(custom_field, 'linkedin').replace("\\","/"))
                else:
                    linkedin.append('')                    
        #except:
        #    print("error fetching user data (skipped)")
        #    pass
        percent = 0
        try:
            course_key=CourseKey.from_string(str(course_enrolls.course))
            course = get_course_by_id(course_key)
            course_grade = CourseGradeFactory().create(user, course)
            percent = course_grade.percent
        except AttributeError:
            print("couldnt obrain grade percent")
            pass
        mention.append(percent)
        print("")
        print("[OK] (" + str(index) + "/" + str(total_len) + ") Got valid grade : " + str(percent) + " for " + user.email)
        print("")

    if len(email) > 0:
        alumni_users = [{'first_name': f, 'last_name': la, 'email': e, 'username': u, 'city': ci, 'country': co, 'tell_us_more': t, 'profile_image_url' : p, 'mention' : m, 'linkedin': li} for f, la, e, u, ci, co, t, p, m, li in zip(first_name, last_name, email, username, city, country, tell_us_more, profile_image_url, mention, linkedin)]
        json_alumni_users = json.dumps(alumni_users)
        json_alumni_dict_user = json.dumps(alumni_users)
        with open('/edx/var/edxapp/media/microsite/champagne-mooc/json/alumni_list_daily.json', 'w') as f:
            f.write(json_alumni_dict_user)
            msg = " ** json alumni files is successfully created ** "
            print(msg)

main()



# sudo /edx/app/edxapp/venvs/edxapp/bin/python /glustered_data/edx-microsite/champagne-mooc/templates/static_templates/update_alumni.py 