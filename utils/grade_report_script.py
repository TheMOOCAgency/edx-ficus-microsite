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
from courseware.courses import get_course_by_id
from microsite_configuration.models import Microsite
from courseware.courses import get_courses
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_names
from tma_stat_dashboard.grade_reports import grade_reports
from student.models import CourseEnrollment, UserProfile
import json
from datetime import datetime
import time
from django.utils.timezone import UTC
import logging
log = logging.getLogger()



class GradeReportManager():
    def __init__(self):
        self.split_by_values=["custom_field","cohortes"]
        self.report_base_values=['course_based','microsite_based']
        self.args = self.get_arguments()
        self.microsite_name=None
        self.microsite_info=None
        self.microsite_register_form=None

    def get_arguments(self):
        parser=argparse.ArgumentParser()
        parser.add_argument('--recipients', help='Emails of the recipients of the report ')
        parser.add_argument('--columns', help='Columns of the report to produce')

        parser.add_argument('--report_base', help='On which level should reports be produced for all microsite courses or one course in particular: args = course_based / microsite_based. default = course_based')
        parser.add_argument('--base_course_id', help='Course id of the report to produce')
        parser.add_argument('--base_microsite', help='Microsite on which produce all courses reports if microsite based reports')


        parser.add_argument('--split_by', help='Split global report into subreports according to : args= custom_field / cohortes')

        parser.add_argument('--select_cohortes', help='Cohortes you want to include in the report. args = cohortes names separated by ; default all')
        parser.add_argument('--select_custom_field_key', help='If split by custom_field set here the key of the field to split on. args= custom_field key name')
        parser.add_argument('--select_custom_field_values', help='Values of custom field for key precised in select_custom_field_key you want to include in the report. args = values separated by  default all')
        return parser.parse_args()

    def setCustomFieldsValues(self):
        values=None
        log.info(self.course_key)
        #If values list provided use it
        if self.args.select_custom_field_values:
            values=self.args.select_custom_field_values.split(';')
        #Custom Field key is provided but no values list every value possible
        elif self.args.select_custom_field_key :
            values=[]
            for enrollment in CourseEnrollment.objects.filter(course_id=self.course_key, is_active=1) :
                try :
                    custom_field=json.loads(UserProfile.objects.get(user=enrollment.user).custom_field)
                except:
                    custom_field={}
                custom_field_value = custom_field.get(self.args.select_custom_field_key)
                if custom_field_value and not custom_field_value in values:
                    values.append(custom_field.get(self.args.select_custom_field_key))
        self.select_custom_field_values= values




    def check_arguments(self):
        error=None
        if not self.args.recipients :
            error='Missing recipients email.'
        elif not self.args.columns :
            error='No columns selected, empty report.'
        elif self.args.report_base and not self.args.report_base in self.report_base_values:
            print(self.args.report_base)
            error='Invalid report base provided. Authorized values are :'+' '.join(self.report_base_values)
        elif (not self.args.report_base or self.args.report_base.lower()=="course_based") and not self.args.base_course_id :
            error='Course based report - missing course id argument.'
        elif (not self.args.report_base or self.args.report_base.lower()=="course_based") and not self.is_valid_course_id(self.args.base_course_id):
            error='Course based report - invalid course id provided.'
        elif self.args.report_base and self.args.report_base.lower()=="microsite_based" and not self.args.base_microsite:
            error='Microsite based report - missing microsite argument.'
        elif self.args.report_base and self.args.report_base.lower()=="microsite_based" and not self.is_valid_microsite(self.args.base_microsite):
            error='Microsite based report - invalid microsite provided.'
        elif self.args.split_by and not self.args.split_by in self.split_by_values:
            error='Split by - invalid split by arguments provided. Authorized values are :'+' '.join(self.split_by_values)
        elif self.args.split_by and self.args.split_by.lower()=="custom_field" and not self.args.select_custom_field_key :
            error='Split by custom_field - missing select custom field key argument.'
        elif self.args.select_custom_field_values and not self.args.select_custom_field_key :
            error='Missing select custom field key to select by custom field values.'
        if error:
            sys.exit('Error: '+error)

    def format_arguments(self):
        self.recipients = self.args.recipients.split(';')
        self.columns = self.args.columns.split(';')
        self.report_base = self.args.report_base if self.args.report_base else "course_based"
        self.select_cohortes=self.args.select_cohortes.split(';') if self.args.select_cohortes else None
        self.split_by = self.args.split_by
        self.microsite_register_form = self.microsite_info.get('FORM_EXTRA',[])
        self.microsite_certificate_form = self.microsite_info.get('CERTIFICATE_FORM_EXTRA', [])
        self.select_custom_field_key = self.args.select_custom_field_key
        self.select_custom_field_values = None

    def is_valid_course_id(self, course_id):
        try:
            self.course_id = course_id
            self.course_key=CourseKey.from_string(course_id)
            self.course = get_course_by_id(self.course_key)
            self.microsite_name = self.course.org
            self.microsite_info =  Microsite.objects.get(key=self.microsite_name).values
            self.course_cohortes = [str(cohorte_name) for cohorte_name in get_cohort_names(self.course).values()]
            return True
        except:
            return False

    def is_valid_microsite(self, microsite):
        try:
            self.microsite_name = microsite
            self.microsite_info = Microsite.objects.get(key=microsite).values
            return True
        except:
            return False

    def is_course_open(self, course_id):
        course_id = course_id
        course_key=CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)
        now = datetime.now(UTC())
        if course.start > now:
            return False
        else:
            return True

    def get_task_input(self, additional_args=[], custom_field_values=[]):
        log.info(self.columns)
        log.info(additional_args)
        self.fields = self.columns + additional_args
        log.info(self.fields)
        task_input = {
            "microsite":self.microsite_name,
            "form":self.fields,
            "register_form":self.microsite_register_form,
            "certificate_form":self.microsite_certificate_form,
            "send_to":self.recipients,
            "select_custom_field_key":self.select_custom_field_key,
            "select_custom_field_values":custom_field_values,
            "split_by":self.split_by
        }
        log.info(task_input)
        return task_input

    def launch_grades_report_tasks(self):
        if self.split_by :
            if self.split_by=="cohortes":
                for cohorte_name in get_cohort_names(self.course).values() :
                    if self.select_cohortes is None or cohorte_name in self.select_cohortes :
                        additional_args=['cohort_selection_'+cohorte_name]
                        grade_reports(self.get_task_input(additional_args),course_id=self.course_id).task_generate_xls()

            elif self.split_by=="custom_field":
                if self.select_custom_field_values :
                    for value in self.select_custom_field_values :
                        grade_reports(self.get_task_input(custom_field_values=[value]),course_id=self.course_id).task_generate_xls()

        else:
            #Traditional report - selected cohortes values
            if self.select_cohortes and set(self.select_cohortes).issubset(self.course_cohortes):
                additional_args = ['cohort_selection_'+cohorte_name for cohorte_name in self.select_cohortes]
                grade_reports(self.get_task_input(additional_args),course_id=self.course_id).task_generate_xls()
            #Traditional report - selected custom field values
            elif self.select_custom_field_key and self.select_custom_field_values:
                grade_reports(self.get_task_input(custom_field_values=self.select_custom_field_values),course_id=self.course_id).task_generate_xls()
            #Traditional report - no selection
            elif self.select_cohortes is None and self.select_custom_field_key is None :
                grade_reports(self.get_task_input(),course_id=self.course_id).task_generate_xls()

    def launch_subscribe_report_tasks(self):
        #Removing key relative to course info
        list_to_remove = ["grade_final","exercises_grade","grade_final","certified","grade_detailed"]
        for el in list_to_remove :
            if el in self.columns:
                self.columns.remove(el)

        #Launching grade_reports for only subcribe infos
        grade_reports(self.get_task_input(),course_id=self.course_id,subscribe_report=True).task_generate_xls()


    def get_reports(self):
        self.get_arguments()
        self.check_arguments()
        self.format_arguments()

        if self.report_base=="microsite_based":
            courses = CourseOverview.get_all_courses(org=self.microsite_name)
            for course in courses:
                self.is_valid_course_id(str(course.id))
                if self.is_course_open(str(course.id)):
                    self.setCustomFieldsValues()
                    self.launch_grades_report_tasks()
                else:
                    log.warning('Course closed - Launching subscribe report')
                    self.launch_subscribe_report_tasks()
        elif self.report_base=="course_based":
            self.setCustomFieldsValues()
            self.launch_grades_report_tasks()

if time.time() < 1651052640 :
    print("start of grade report script")
    GradeReportManager().get_reports()
    print("end of grade report script")



"""
from courseware.courses import get_course_by_id
import json
from microsite_configuration.models import Microsite
from opaque_keys.edx.keys import CourseKey
from tma_stat_dashboard.grade_reports import grade_reports


receivers_args = sys.argv[1]
course_id = sys.argv[2]
fields_args = sys.argv[3]
try :
    cohortes_list = sys.argv[4]
except:
    cohortes_list=''


try:
    course_key=CourseKey.from_string(course_id)
    course_org=get_course_by_id(course_key).org
    microsite_information = Microsite.objects.get(key=course_org)
except:
    sys.exit('Course id is not valid!')

#Treated arguments
receivers = receivers_args.split(';')
fields = fields_args.split(';')
if cohortes_list :
    cohortes_list=cohortes_list.split(';')
    cohortes_list=['cohort_selection_'+cohorte for cohorte in cohortes_list]
    fields.extend(cohortes_list)
try:
    microsite_register_form = microsite_information.values['FORM_EXTRA']
except:
    microsite_register_form=''
try :
    microsite_certificate_form = microsite_information.values['CERTIFICATE_FORM_EXTRA']
except:
    microsite_certificate_form=''

task_input = {
    "microsite":course_org,
    "form":fields,
    "register_form":microsite_register_form,
    "certificate_form":microsite_certificate_form,
    "send_to":receivers,
}
print(task_input)
grade_reports(task_input,course_id=course_id).task_generate_xls()
"""


# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/nature-for-city-life/utils/grade_report_script.py --recipient="valerie.montes@univ-amu.fr;mcvallon@maregionsud.fr;esma.inci@weuplearning.com" --columns="user_id;email;first_name;last_name;sexe;age;statut;secteur;niveau-etudes;motivation;area;location;inscription_date;last_connexion;grade_detailed;exercises_grade;exercises_answers;grade_final;certified;cohorte_names" --base_course_id=""