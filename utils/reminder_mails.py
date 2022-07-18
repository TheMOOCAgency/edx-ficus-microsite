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
from tma_apps.best_grade.helpers import check_best_grade
import urllib
from tma_apps.models import TmaCourseEnrollment

log = logging.getLogger()

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

email_params={}

def send_email(message_type,user,course_id, course):
    subject = 'Mooc Conservation'
    message = ''
    from_email = 'Mooc Conservation <mooc-conservation@themoocagency.com>'
    recipient_list = [user.email]
    #recipient_list = ["yoann.mroz@weuplearning.com"]
    subject_template = None
    message_template = None

    email_params['message'] = message_type
    email_params['email_address'] = user.email
    email_params['full_name'] = user.profile.name
    email_params['course_name'] = course.display_name_with_default
    email_params['facebook_link'] = 'https://www.facebook.com/IUCNpapaco'
    email_params['twitter_link'] = 'https://twitter.com/Papaco_IUCN'
    email_params['linkedin_link'] = 'https://www.linkedin.com/company/papaco'
    email_params['instagram_link'] = 'https://www.instagram.com/moocconservation/'
    email_params['application_link'] = 'https://mooc-conservation.org/about'
    if course.end:
        email_params['course_end'] = course.end.strftime('%d-%m-%y')
    elif "_EN" in course_id:
        email_params['course_end'] = "(No course end date)"
    else:
        email_params['course_end'] = "(pas de date de fin de cours)"
    email_params['opted_out_link'] = microsite_base_url+'dashboard?optOut='+urllib.quote(course_id)
    email_params['ambassadors'] = 'https://sites.google.com/view/moocconservation/ambassadors'

    subject = message_type
    message = message_type

    if "_EN" in course_id:
        subject = subject+'_en'
        message = message+'_en'
    else: 
        subject = subject+'_fr'
        message = message+'_fr'
    subject = subject+'_subject.txt'
    message = message+'_message.txt'

    if subject is not None and message is not None:
        subject_template = mylookup.get_template(subject).render()
        subject_template = transpilation(subject_template, email_params)
        message_template = mylookup.get_template(message).render()
        message_template = transpilation(message_template, email_params)
        log.info('[WUL] : mail sent to '+user.email+' wich content is '+message_type)
        send_mail(subject_template, message_template, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
    else:
        log.info('[WUL] : mail aborted subject or message is empty')

def has_opted_out(user, course_id):
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

def is_quiz_validated(user):
    for student_module in db_query:
        if student_module.student_id == user.id:
            return True
    return False

def firstCourseSubmit(custom_field, course_id, user_profile):
    if user_profile != {}:
        if "papaco_first_exam_submission" not in custom_field:
            custom_field["papaco_first_exam_submission"] = []
        if course_id not in custom_field["papaco_first_exam_submission"]:
            custom_field["papaco_first_exam_submission"].append(course_id)
            user_profile.custom_field = json.dumps(custom_field)
            user_profile.save()
            log.info(custom_field["papaco_first_exam_submission"])
            return True
    return False

def check_previous_session(custom_field, course_id, user_profile, passed):
    if user_profile != {} and passed:
        if course_id not in custom_field:
            custom_field[course_id]=True
            user_profile.custom_field = json.dumps(custom_field)
            user_profile.save()
        return True
    return False

def check_grade(user, course, course_id):
    courseGrade = check_best_grade(user, course)
    metadata = course.course_extra['certificate']

    passed = False
    forum_posts_validated = False
    total = 0
    add = 0
    finished = 0
    values = []
    from_vue = []
    grade = courseGrade.percent_tma
    regular = False
    course_grades =[]
    course_grade = CourseGradeFactory().create(user, course)
    final_grade = course_grade.percent * 100
    for user_summary in course_grade.grade_value['grade_breakdown'].keys():
        name_section=course_grade.grade_value['grade_breakdown'].get(user_summary)['category']
        for course_part in course_grade.grade_value['section_breakdown']:
            if course_part['category'] == name_section:
                if course_part['percent'] > 0:
                    add += 1
                if course_part['percent'] > 0.75:
                    finished += 1
    if add == len(course_grade.grade_value['section_breakdown']):
        regular = True
    if regular and finished == len(course_grade.grade_value['section_breakdown']):
        passed = True

    partial = True
    for grade_category_result in courseGrade.grade_value['grade_breakdown'].keys():
        # If any grade is zero then it means there is a course category that was not tried or outrageously failed
        # But a grade can be zero if its weight is zero
        if courseGrade.grade_value['grade_breakdown'].get(grade_category_result).get('percent') == 0 and not ("of a possible 0.00%" in courseGrade.grade_value['grade_breakdown'].get(grade_category_result).get('detail')):
            partial = False
            break
    
    try:
        tma_enrollment=TmaCourseEnrollment.get_enrollment(course_id=course_id, user=user)
        if tma_enrollment.best_grade_date == None and regular:
            tma_enrollment.best_grade_date = datetime.now()
            tma_enrollment.save()
        best_grade_date = tma_enrollment.best_grade_date
    except:
        best_grade_date = False
        pass

    context = {
        "partial":partial,
        "passed":passed,
        "finished":finished,
        "regular":regular,
        "add":add,
        "total":total,
        "grade":grade,
        "values":values,
        "from_vue":from_vue,
        "best_grade_date":best_grade_date
    }

    return context

course_id_list = [
    'course-v1:mooc-conservation+eco-monitoring+2021_T1_EN',
    'course-v1:mooc-conservation+law-enforcement+2021_T1_EN',
    'course-v1:mooc-conservation+marine-areas+2021_T1_EN',
    'course-v1:mooc-conservation+new-techs+2021_T1_EN',
    'course-v1:mooc-conservation+protected-areas+2021_T1_EN',
    'course-v1:mooc-conservation+areas-valorisation+2021_T1_EN',
    'course-v1:mooc-conservation+species-conservation+2021_T1_EN',
    'course-v1:mooc-conservation+aires-marines+2021_T1',
    'course-v1:mooc-conservation+application-loi+2021_T1',
    'course-v1:mooc-conservation+conservation-especes+2021_T1',
    'course-v1:mooc-conservation+aires-protegees+2021_T1',
    'course-v1:mooc-conservation+aires-protegees+2020_T2',
    'course-v1:mooc-conservation+nouvelles-technologies+2021_T1',
    'course-v1:mooc-conservation+suivi-eco+2021_T1',
    'course-v1:mooc-conservation+valorisation-aires+2021_T1'
]

microsite_base_url = 'https://mooc-conservation.org/'

for course_id in course_id_list:
    primary_list = course_id.split(":")
    course_id_elements = primary_list[1].split("+")
    course_key=CourseKey.from_string(course_id)
    course=get_course_by_id(course_key)
    microsite = course_id_elements[0]
    course_number = course_id_elements[1]
    course_session = course_id_elements[2]
    module_state_key = BlockUsageLocator(CourseLocator(microsite, course_number, course_session, None, None), u'course', u'course')
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    microsite_info =  Microsite.objects.get(key=microsite).values
    db_query = models.StudentModule.objects.filter(
        course_id__exact=course_key,
        module_state_key=module_state_key,
    )
    log.info(course_id)
    for _ce in course_enrollments:
        user = _ce.user
        user_id = user.id
        user_enroll_date = _ce.created
        try:
            grade_summary = check_grade(user, course, course_id)
        except:
            continue
        user_enroll_date = user_enroll_date.replace(hour=0, minute=0, second=0, microsecond=0)
        user_enroll_date = user_enroll_date.date()
        user_last_login = user.last_login
        if user_last_login:
            user_last_login = user.last_login.replace(hour=0, minute=0, second=0, microsecond=0)
            user_last_login = user_last_login.date()
        course_enrollment_end = course.enrollment_end
        if course_enrollment_end:
            course_enrollment_end = course.enrollment_end.replace(hour=0, minute=0, second=0, microsecond=0)
            course_enrollment_end = course_enrollment_end.date()
        if "best_grade_date" in grade_summary and grade_summary["best_grade_date"] and grade_summary["passed"]:
            best_grade_date = grade_summary["best_grade_date"].replace(hour=0, minute=0, second=0, microsecond=0)
            best_grade_date = best_grade_date.date()
        else:
            best_grade_date = None
        regular = grade_summary["regular"]
        passed = grade_summary["passed"]
        finished = grade_summary["finished"]

        #if has_opted_out(user) or '@weuplearning.com' in user.email or '@themoocagency.com' in user.email:
        if has_opted_out(user, course_id):
            continue

        try:
            user_profile = UserProfile.objects.get(user=user)
            custom_field = json.loads(user_profile.custom_field)
        except:
            user_profile = None
            custom_field = {}

        # check previous session is passed
        previous_session = False
        previous_session = check_previous_session(custom_field, course_id, user_profile, grade_summary["passed"])

        # Enrolled yesterday
        if user_enroll_date == (script_reference_date - timedelta(days=1)):
            send_email('welcome',user, course_id, course)

        # Success first exam
        if finished == 1 and firstCourseSubmit(custom_field, course_id, user_profile):
            send_email('congratulations_first_exam',user, course_id, course)
        
        # Failed certification
        if regular and not passed:
            if best_grade_date == (script_reference_date - timedelta(days=1)):
                send_email('reminder_exam',user, course_id, course)
        
        # All exams passed
        if best_grade_date and passed:
            if best_grade_date == (script_reference_date - timedelta(days=1)):
                send_email('congratulations_all_exams',user, course_id, course)

        # No connection for 2 weeks AND not all exams done
        if not previous_session and not passed and not regular and (course_enrollment_end is None or course_enrollment_end >= script_reference_date):
            if user_last_login == (script_reference_date - timedelta(days=14)):
                send_email('encouragement',user, course_id, course)

log.info('******************************************************************')
log.info('[WUL] : End of sending emails. SUCCESS !')
log.info('******************************************************************')

# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/mooc-conservation/utils/reminder_mails.py
