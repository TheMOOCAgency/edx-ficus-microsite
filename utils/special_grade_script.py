# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#IMPORT FOR SCRIPT TO
##RUN
##WRITE EXCEL FILE
##SEND EMAIL
import os
import importlib
import csv
import time
import os
from xlwt import *
import json
import logging

from io import BytesIO

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

log = logging.getLogger()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()
#IMPORT TO
##RUN OUTSITE EDX
from django.core.management import execute_from_command_line
import django
##USE EDX FUNCTIONS
from opaque_keys.edx.keys import CourseKey,UsageKey
from courseware.access import has_access
from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
#from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from student.roles import CourseStaffRole
from student.models import *
from courseware.models import StudentModule
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)
from tma_apps.files_api.models import mongofiles

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
try:
    course_id = sys.argv[2]
except:
    pass
    course_id = ""
try:
    register_users = sys.argv[3]
    if register_users == "true":
        register_users = True
    else:
        register_users = False
except:
    register_users = None
try:
    certificate_users = sys.argv[4]
    if certificate_users == "true":
        certificate_users = True
    else:
        certificate_users = False
except:
    certificate_users = None
try:
    persistent = sys.argv[5]
    if persistent == "true":
        persistent = True
    else:
        persistent = False
except:
    persistent = None
try:
    graded = sys.argv[6]
    if graded == "true":
        graded = True
    else:
        graded = False
except:
    graded = None

#Types de fichiers à récupérer
try :
    string_fichiers = sys.argv[7]
    ajout_fichiers = string_fichiers.split(';')
except:
    ajout_fichiers = []

#If application form field
try :
    application_field = sys.argv[8]
    if application_field == "true":
        application_field = True
    else:
        application_field = False
except:
    application_field = None

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)

#get microsite
org = course.org
query = "SELECT a.id,a.organization,b.key FROM microsite_configuration_micrositeorganizationmapping a,microsite_configuration_microsite b WHERE a.microsite_id = b.id"
microsite_list = MicrositeOrganizationMapping.objects.raw(query)
microsite_name = None

for row in microsite_list:
    if row.organization == org:
        microsite_name = row.key

domain_prefix = None
register_form = None
certificate_form = None
microsite = Microsite.objects.get(key=microsite_name)
microsite_value = microsite.values
i=0

for val in microsite_value:
    if val == 'domain_prefix':
        domain_prefix = microsite_value.values()[i]
    if val == 'FORM_EXTRA':
        register_form = microsite_value.values()[i]
    if val == 'CERTIFICATE_FORM_EXTRA':
        certificate_form = microsite_value.values()[i]
    if val == 'APPLICATION_EXTRA':
        application_form = microsite_value.values()[i]
    i=i+1

#mongo certificate_form models
_mongo = ensure_form_models()
db = 'ensure_form'
collection = 'certificate_form'
_mongo.connect(db=db,collection=collection)
_mongo.microsite = domain_prefix
timestr = time.strftime("%Y_%m_%d")
timesfr = time.strftime("%d.%m.%Y")
timesfr = str(timesfr)

#headers
HEADERS = [
    "ID","Nom","Prénom","Téléphone","Code Postal","Username","Email","Diplôme","Spécialité","Année de naissance","Sexe","Agent SNCF","Dossier de candidature déposé","Note","Date d'inscritpion"
]

#get course enrolls
course_enrollement=CourseEnrollment.objects.filter(course_id=course_key)

#grades reports summary
user_repports_summary=course_enrollement[0]
user_summary=user_repports_summary.user

#prepare workbook
wb = Workbook(encoding='utf-8')
filename = '/home/edxtma/csv/{}_{}.xls'.format(timestr,course.display_name_with_default)
sheet = wb.add_sheet('Stats')
for i, header in enumerate(HEADERS):
   sheet.write(0, i, header)

if persistent:
    #PREPARE JSON LOG FILE
    file_path = '/home/edxtma/dev/log{}.json'.format(course.display_name_with_default)
    try:
        _log_file = open(file_path,"r")
        _log_content = json.load(_log_file)
        _log_file.close()
    except:
        _log_content = {}

#NOW LOOK AT GRADES
def get_cf_value(user_profile, cf_str):
    value = ''
    if cf_str == "folder_already_completed" or cf_str == "is_already_agent":
        if cf_str in user_profile and user_profile[cf_str] == u'true' :
            value = u'Oui'
        else:
            value = u'Non'
    else:
        if cf_str in user_profile:
            value = user_profile[cf_str]
        else:
            value = ''
    return value


usage_id = "block-v1:aiguilleur-du-rail+SNCFR2017+2017_T1+type@problem+block@510e3e2f5ec14077825eb7eecefc0d84"
course_id = "course-v1:aiguilleur-du-rail+SNCFR2017+2017_T1"
course_key = CourseKey.from_string(course_id)
module_state_key =  UsageKey.from_string(usage_id).map_into_course(course_key)

list_of_student_modules_for_last_problem_block = StudentModule.objects.filter(module_state_key__exact = module_state_key).order_by().values('student_id').distinct()

from pprint import pformat

j=0
for i in range(len(course_enrollement)):
    user=course_enrollement[i].user

    did_finish = False
    for courseware_student_module in list_of_student_modules_for_last_problem_block:
        log.info(pformat(courseware_student_module))
        if(user.id == courseware_student_module["student_id"]):
            did_finish = True
            break

    if not did_finish:
        continue

    if user.id >= 536458:
        j=j+1
        #userprofile
        user_profile = {}

        #ip
        list_ip_str = ""
        try:
            user_ip = UserIpTracking.objects.filter(user=self.user,microsite=domain_prefix)
            for _ip in user_ip:
                list_ip.append(_ip.ip)
            if len(list_ip) > 10:
                list_ip = list_ip[-10:]
            list_ip_str = "; ".join(list_ip)
        except:
            user_ip = []
        username=user.username
        email=user.email
        try:
            date_inscription=user.date_joined.strftime('%d %b %y')
        except:
            date_inscription="Null"
        try:
            last_login=user.last_login.strftime('%d %b %y')
        except:
            last_login="Null"
        list_ip = ""
        for _ip in user_ip:
            list_ip = list_ip+" "+str(_ip.ip)
        
        try:
            user_profile = json.loads(UserProfile.objects.get(user=user).custom_field)
        except:
            user_profile = {}

        try:
            course_grade = CourseGradeFactory().create(user, course)
            grade_note = str(course_grade.percent * 100)+'%'
        except:
            pass

        #insert rows
        user_rows = [
            user.id,
            get_cf_value(user_profile,"last_name"),
            get_cf_value(user_profile,"first_name"),
            get_cf_value(user_profile,"telephone"),
            get_cf_value(user_profile,"postal_code"),
            username,
            email,
            get_cf_value(user_profile,"diplome"),
            get_cf_value(user_profile,"filiere"),
            get_cf_value(user_profile,"year_of_birth"),
            get_cf_value(user_profile,"gender"),
            get_cf_value(user_profile,"is_already_agent"),
            get_cf_value(user_profile,"folder_already_completed"),
            grade_note,
            date_inscription
        ]
        l=0

        for row in user_rows:
            sheet.write(j, l, row)
            l=l+1

output = BytesIO()

wb.save(output)

_files_values = output.getvalue()
# envoyer un mail test

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de données du MOOC {}<br/><br/>Bonne réception<br>The MOOC Agency<br></p></body></html>".format(course.display_name)
part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "{} <ne-pas-repondre@themoocagency.com>".format(org)
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "Rapport de donnees"
   attachment = _files_values
   part = MIMEBase('application', 'octet-stream')
   part.set_payload(attachment)
   encoders.encode_base64(part)
   part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename))
   msg.attach(part)
   server = smtplib.SMTP('mail3.themoocagency.com', 25)
   server.starttls()
   server.login('contact', 'waSwv6Eqer89')
   msg.attach(part2)
   text = msg.as_string()
   server.sendmail(fromaddr, toaddr, text)
   server.quit()
   print 'mail send to '+str(TO_EMAILS[i])
