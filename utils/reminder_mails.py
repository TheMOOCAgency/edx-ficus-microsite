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

course_id='course-v1:operation-raffinage+Total01+2018Q1'
course_key=CourseKey.from_string(course_id)
course = get_course_by_id(course_key) 
module_state_key = BlockUsageLocator(CourseLocator(u'operation-raffinage', u'Total01', u'2018Q1', None, None), u'course', u'course')
course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
microsite_base_url = 'https://operation-raffinage.com//'
microsite = 'operation-raffinage'
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
    'reminder_j_plus_1': (
        'reminder_j_plus_1_subject.txt',
        'reminder_j_plus_1_message.txt'
    )
}

email_params={
    'cv_link' : microsite_base_url+'courses/course-v1:operation-raffinage+Total01+2018Q1/courseware/0f9dd2cb9cb249dabddaf0c5b8bb7552/24f594bba21a4704897c752ddf5a142d/1?activate_block_id=block-v1%3Aoperation-raffinage%2BTotal01%2B2018Q1%2Btype%40vertical%2Bblock%407dfed7ed303949b6b86d6f49c894218f'
}

def send_reminder_email(message_type,user):
    subject = 'Operation-raffinage'
    message = ''
    from_email = 'Operation Raffinage <ne-pas-repondre@themoocagency.com>'
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

def is_cv_done(custom_field):
    if 'cv_done' in custom_field:
        return custom_field['cv_done']
    else:
        return False

def is_reminder_already_sent(custom_field, user_profile):
    if 'reminder_already_sent' in custom_field:
        return True
    else:
        custom_field['reminder_already_sent'] = True
        user_profile.custom_field = json.dumps(custom_field)
        user_profile.save()
        return False

for _ce in course_enrollments:
    user = _ce.user
    user_id = user.id

    if has_opted_out(user) or '@weuplearning.com' in user.email or '@themoocagency.com' in user.email:
        continue

    try:
        user_profile = UserProfile.objects.get(user=user)
        custom_field = json.loads(user_profile.custom_field)
    except:
        custom_field = {}

    if is_cv_done(custom_field) != 'oui':
        course_grade = CourseGradeFactory().create(user, course)
        if course_grade.passed:
            reminder_already_sent = is_reminder_already_sent(custom_field, user_profile)
            if not reminder_already_sent:
                send_reminder_email('reminder_j_plus_1',user)
            else:
                log.info(('[WUL] : mail already sent for user {}').format(user.email))
        else:
            log.info(('[WUL] : course not passed for user {}').format(user.email))
    else:
        log.info(('[WUL] : cv already uploaded for user {}').format(user.email))

log.info('******************************************************************')
log.info('[WUL] : End of sending emails. SUCCESS !')
log.info('******************************************************************')