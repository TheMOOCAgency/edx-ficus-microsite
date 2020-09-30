#!/usr/bin/env python

import os
import importlib
import sys
reload(sys)
sys.setdefaultencoding('utf8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.core.management import execute_from_command_line
import django

#Script imports
import argparse, sys
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, BlockUsageLocator
from opaque_keys.edx.locator import CourseLocator
from courseware.courses import get_course_by_id
from microsite_configuration.models import Microsite
from courseware.courses import get_courses
from django.core.mail import send_mail
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_names
from bulk_email.models import Optout, BulkEmailFlag  # pylint: disable=import-error
from courseware import models
from courseware.models import StudentModule
from mako.lookup import TemplateLookup
from mako.template import Template
from student.models import CourseEnrollment, UserProfile
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
import json
from datetime import date, datetime, timedelta
import logging
import inspect
import track.views
log = logging.getLogger()

course_id='course-v1:inveest+invest2019+invest2019'
course_key=CourseKey.from_string(course_id)
module_state_key = BlockUsageLocator(CourseLocator(u'inveest', u'invest2019', u'invest2019', None, None), u'course', u'course')
course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
microsite_base_url = 'https://elearning.inveest.org/'
microsite = 'inveest'
microsite_info =  Microsite.objects.get(key=microsite).values
db_query = models.StudentModule.objects.filter(
    course_id__exact=course_key,
    module_state_key=module_state_key,
)

SETTINGS_PATH = os.path.normpath(os.path.dirname(__file__))

TEMPLATE_DIRS = (
    os.path.join(SETTINGS_PATH, 'emails'),
)

script_reference_date = date.today()

mylookup = TemplateLookup(directories=[TEMPLATE_DIRS[0]],
        input_encoding='utf-8',
        output_encoding='utf-8',
        default_filters=['decode.utf8'],
        encoding_errors='replace')

email_template_dict = {
    'not_expert_j_plus_1': (
        'not_expert_j_plus_1_subject.txt',
        'not_expert_j_plus_1_message.txt'
    ),
    'not_expert_j_plus_4': (
        'not_expert_j_plus_4_subject.txt',
        'not_expert_j_plus_4_message.txt'
    ),
    'not_expert_quiz_1_validated_j_plus_6': (
        'not_expert_quiz_1_validated_j_plus_6_subject.txt',
        'not_expert_quiz_1_validated_j_plus_6_message.txt'
    ),
    'not_expert_quiz_1_not_validated_j_plus_6': (
        'not_expert_quiz_1_not_validated_j_plus_6_subject.txt',
        'not_expert_quiz_1_not_validated_j_plus_6_message.txt'
    ),
    'not_expert_j_plus_10': (
        'not_expert_j_plus_10_subject.txt',
        'not_expert_j_plus_10_message.txt'
    ),
    'not_expert_quiz_1_validated_j_plus_14': (
        'not_expert_quiz_1_validated_j_plus_14_subject.txt',
        'not_expert_quiz_1_validated_j_plus_14_message.txt'
    ),
    'not_expert_quiz_1_not_validated_j_plus_14': (
        'not_expert_quiz_1_not_validated_j_plus_14_subject.txt',
        'not_expert_quiz_1_not_validated_j_plus_14_message.txt'
    ),
    'not_expert_quiz_1_validated_j_plus_20': (
        'not_expert_quiz_1_validated_j_plus_20_subject.txt',
        'not_expert_quiz_1_validated_j_plus_20_message.txt'
    ),
    'not_expert_quiz_1_not_validated_j_plus_20': (
        'not_expert_quiz_1_not_validated_j_plus_20_subject.txt',
        'not_expert_quiz_1_not_validated_j_plus_20_message.txt'
    ),
    'not_expert_quiz_1_validated_j_plus_30': (
        'not_expert_quiz_1_validated_j_plus_30_subject.txt',
        'not_expert_quiz_1_validated_j_plus_30_message.txt'
    ),
    'not_expert_quiz_1_not_validated_j_plus_30': (
        'not_expert_quiz_1_not_validated_j_plus_30_subject.txt',
        'not_expert_quiz_1_not_validated_j_plus_30_message.txt'
    ),
    'not_expert_quiz_1_validated_j_plus_45': (
        'not_expert_quiz_1_validated_j_plus_45_subject.txt',
        'not_expert_quiz_1_validated_j_plus_45_message.txt'
    ),
    'not_expert_quiz_1_not_validated_j_plus_45': (
        'not_expert_quiz_1_not_validated_j_plus_45_subject.txt',
        'not_expert_quiz_1_not_validated_j_plus_45_message.txt'
    ),
    'expert_no_siren_siret_j_plus_2': (
        'expert_no_siren_siret_j_plus_2_subject.txt',
        'expert_no_siren_siret_j_plus_2_message.txt'
    ),
    'expert_no_siren_siret_j_plus_6': (
        'expert_no_siren_siret_j_plus_6_subject.txt',
        'expert_no_siren_siret_j_plus_6_message.txt'
    ),
    'expert_siren_siret_j_plus_4': (
        'expert_siren_siret_j_plus_4_subject.txt',
        'expert_siren_siret_j_plus_4_message.txt'
    ),
    'expert_siren_siret_j_plus_10': (
        'expert_siren_siret_j_plus_10_subject.txt',
        'expert_siren_siret_j_plus_10_message.txt'
    ),
    'expert_siren_siret_j_plus_30': (
        'expert_siren_siret_j_plus_30_subject.txt',
        'expert_siren_siret_j_plus_30_message.txt'
    )
}

email_params={
    'message' : '',
    'email_address' : '',
    'full_name' : '',
    'dashboard_link' : microsite_base_url+'dashboard',
    'opted_out_link' : microsite_base_url+'dashboard?optOut=course-v1%3Ainveest%2Binvest2019%2Binvest2019',
    'map_link' : microsite_base_url+'about',
    'expert_link' : microsite_base_url+'courses/'+course_id+'/courseware/d80f528b85e4484c9555dd07b1428942/678409528a7849ed877f53bbfcf0d771/',
    'cost_link' : microsite_base_url+'courses/course-v1%3Ainveest%2Bexpert%2B2020/courseware/d0e4d2b906d14d1b873fc5604f5677bb/',
    'skill_link' : microsite_base_url+'courses/'+course_id+'/courseware/3eba27b96a744bbc80b66541fdaaaa54/f687c6d4357942d4927b017bd55000af/',
    'start_module_link' : microsite_base_url+'dashboard/'+course_id+'/',
    'questionnaire_link' : 'https://apollineabauzit.typeform.com/to/UtEw12',
    'siret_siren_link' : microsite_base_url+'courses/course-v1:inveest+expert+2020/courseware/d0e4d2b906d14d1b873fc5604f5677bb/'
}

def send_greenflex_email(message_type,user):
    subject = 'GreenFlex'
    message = ''
    from_email = 'Inveest <inveest@themoocagency.com>'
    recipient_list = [user.email]
    subject_template = None
    message_template = None

    email_params['message'] = message_type
    email_params['email_address'] = user.email
    email_params['full_name'] = user.profile.name

    subject, message = email_template_dict.get(message_type, (None, None))
    if subject is not None and message is not None:
        subject_template = mylookup.get_template(subject).render()
        message_template = mylookup.get_template(message).render()
        message_template = transpilation(message_template, email_params)
        log.info('[WUL] : mail sent to '+user.email+' wich content is '+message_type)
        send_mail(subject_template, message_template, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
    else:
        log.info('[WUL] : mail aborted subject or message is empty')

def has_opted_out(user):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    optout_object = Optout.objects.filter(user=user, course_id=course_key)
    if len(optout_object)>0:
        return True
    else:
        return False

def transpilation(message, email_params):
    for word, new_word in email_params.items():
        message = message.replace('{'+word+'}', new_word)
    return message

def is_expert(custom_field):
    if 'expert' in custom_field:
        return custom_field['expert']
    else:
        return False

def get_siren_siret_date(user_id):
    if 'siren_siret_date' in custom_field:
        ss_date = custom_field['siren_siret_date']
        ss_date = datetime. strptime(ss_date, '%Y-%m-%d')
        ss_date = ss_date.replace(hour=0, minute=0, second=0, microsecond=0)
        ss_date = ss_date.date()
        return ss_date
    else:
        return False

def is_quiz_validated(user):
    for student_module in db_query:
        if student_module.student_id == user.id:
            return True
    return False

def get_presentiel(_ce):
    is_in_presentiel = False
    for field in microsite_info['FORM_EXTRA']:
        if 'name' in field and field['name'] == 'organisme':
            for field_option in field['options']:
                if 'course' in field_option:
                    presentiel_course_id = CourseKey.from_string(field_option['course'])
                    for enrollment in CourseEnrollment.objects.filter(course_id=presentiel_course_id):
                        if _ce.user == enrollment.user:
                            log.info('[WUL] : User is registered to a presentiel course : '+str(presentiel_course_id))
                            is_in_presentiel = True
                            break
    return is_in_presentiel

for _ce in course_enrollments:
    user = _ce.user
    user_id = user.id
    user_enroll_date = _ce.created
    user_enroll_date = user_enroll_date.replace(hour=0, minute=0, second=0, microsecond=0)
    user_enroll_date = user_enroll_date.date()
    log.info('[WUL] : created date '+str(_ce.created))

    #if has_opted_out(user) or '@weuplearning.com' in user.email or '@themoocagency.com' in user.email:
    if has_opted_out(user):
        continue

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except:
        custom_field = {}

    log.info('[WUL] : Treating user '+user.email+' ; ID : '+str(user_id))

    if is_expert(custom_field) != 'oui':
        quizvalidated = is_quiz_validated(user)
        log.info(('[WUL] : not expert, days : {} ; has validated quiz : {}').format(script_reference_date - user_enroll_date,quizvalidated))
        if user_enroll_date == (script_reference_date - timedelta(days=1)):
            send_greenflex_email('not_expert_j_plus_1',user)

        if user_enroll_date == (script_reference_date - timedelta(days=4)):
            send_greenflex_email('not_expert_j_plus_4',user)
        
        if user_enroll_date == (script_reference_date - timedelta(days=6)):
            if quizvalidated:
                send_greenflex_email('not_expert_quiz_1_validated_j_plus_6',user)
            else:
                send_greenflex_email('not_expert_quiz_1_not_validated_j_plus_6',user)
        
        if user_enroll_date == (script_reference_date - timedelta(days=10)):
            send_greenflex_email('not_expert_j_plus_10',user)

        if user_enroll_date == (script_reference_date - timedelta(days=14)):
            if quizvalidated:
                send_greenflex_email('not_expert_quiz_1_validated_j_plus_14',user)
            else:
                send_greenflex_email('not_expert_quiz_1_not_validated_j_plus_14',user)
        
        if user_enroll_date == (script_reference_date - timedelta(days=20)):
            if quizvalidated:
                send_greenflex_email('not_expert_quiz_1_validated_j_plus_20',user)
            else:
                send_greenflex_email('not_expert_quiz_1_not_validated_j_plus_20',user)
    
        if user_enroll_date == (script_reference_date - timedelta(days=30)):
            if quizvalidated:
                send_greenflex_email('not_expert_quiz_1_validated_j_plus_30',user)
            else:
                send_greenflex_email('not_expert_quiz_1_not_validated_j_plus_30',user)

        if user_enroll_date == (script_reference_date - timedelta(days=45)):
            if quizvalidated:
                send_greenflex_email('not_expert_quiz_1_validated_j_plus_45',user)
            else:
                send_greenflex_email('not_expert_quiz_1_not_validated_j_plus_45',user)
    
    else:
        siren_siret_date = get_siren_siret_date(user_id)
        presentiel_registered = get_presentiel(_ce)
        ss_register_date = None
        if siren_siret_date:
            ss_register_date = script_reference_date - siren_siret_date
        log.info(('[WUL] : expert, days : {}, is presentiel registered : {}, siren siret register date : {}').format(script_reference_date - user_enroll_date,presentiel_registered,ss_register_date))
        if not siren_siret_date:
            if user_enroll_date == (script_reference_date - timedelta(days=2)):
                send_greenflex_email('expert_no_siren_siret_j_plus_2',user)
            
            if user_enroll_date == (script_reference_date - timedelta(days=6)):
                send_greenflex_email('expert_no_siren_siret_j_plus_6',user)
        
        elif not presentiel_registered:
            if siren_siret_date == (script_reference_date - timedelta(days=4)):
                send_greenflex_email('expert_siren_siret_j_plus_4',user)
            
            if siren_siret_date == (script_reference_date - timedelta(days=10)):
                send_greenflex_email('expert_siren_siret_j_plus_10',user)

            if siren_siret_date == (script_reference_date - timedelta(days=30)):
                send_greenflex_email('expert_siren_siret_j_plus_30',user)

log.info('******************************************************************')
log.info('[WUL] : End of sending emails. SUCCESS !')
log.info('******************************************************************')