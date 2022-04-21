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

users_list=["aurelien.garreau@live.fr",
"tovihessis@gmail.com",
"lauremvuh@gmail.com",
"gethroaltema@yahoo.com",
"dame.diallo@ucad.edu.sn",
"melaniebawourim@yahoo.fr",
"tenkodogoisi@gmail.com",
"sekesero95@gmail.com",
"ssekeyerima@gmail.com",
"adjayemaixent2@gmail.com",
"magbediakite@gmail.com",
"elkhatrinabil0@gmail.com",
"jclaudofoun@yahoo.fr",
"alsabrinaniriniaina@gmail.com",
"moustaphadie@gmail.com",
"mounkenezacharie@gmail.com",
"nath.kilima@gmail.com",
"Francisco.URENA-LARA@eeas.europa.eu",
"djatelenguek@gmail.com",
"cedricingridbiankeu@gmail.com",
"agrofemmesh@gmail.com",
"richabpro3507@gmail.com",
"cedricingridbiankeu@gmail.com",
"sayba58keita@gmail.com",
"ngoliclaver@gmail.com",
"izouon92@gmail.com",
"youkouguiedmond@yahoo.fr",
"skossivi@yahoo.fr",
"valeryaristide@yahoo.fr",
"rachadsanoussi@gmail.com",
"desirevictor91@gmail.com",
"louise.percevault@yahoo.fr",
"tsihoarana.mandranto@gmail.com",
"sinnancamara@gmail.com",
"sayba58keita@gmail.com",
"houngnonraoul@gmail.com",
"donatienmudimba@gmail.com",
"guylandryb3@gmail.com",
"thierry2024@yahoo.fr",
"soilihialimansouri@gmail.com",
"tieribernadette@gmail.com"]

user_already_seen = []

microsite_base_url = 'https://mooc-conservation.org/'
for course_id in course_id_list:
    primary_list = course_id.split(":")
    course_id_elements = primary_list[1].split("+")
    course_key=CourseKey.from_string(course_id)
    course=get_course_by_id(course_key)
    print course.display_name_with_default
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

    for _ce in course_enrollments:
        user = _ce.user
        if user.email in users_list:
            user_already_seen.append(user.email)
            print user.email
            print user.profile.name
            

log.info('******************************************************************')

# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/mooc-conservation/utils/find_names.py
