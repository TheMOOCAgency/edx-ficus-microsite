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

from io import BytesIO

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders


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
from opaque_keys.edx.keys import CourseKey
from courseware.access import has_access
from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
#from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from student.roles import CourseStaffRole
from student.models import *
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
from tma_apps.models import TmaCourseEnrollment


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
enable_time_tracking = None

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
    if val == 'TMA_ENABLE_TIME_TRACKING':
        enable_time_tracking = microsite_value.values()[i]
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
if domain_prefix == "moduleblanchiment":
    HEADERS = [
            "id","Matricule","Adresse mail",
            "Client","Date d'inscription","Date dernière connexion"
            ]
else:
    HEADERS = [
            "id","Username","Adresse mail",
            "Client","Date d'inscription","Date dernière connexion"
            ]

#register_form
if register_users and register_form is not None:
    for row in register_form:
        if row.get('type') is not None:
            HEADERS.append(row.get('label'))
#certificate_form
if certificate_users and certificate_form is not None:
    for row in certificate_form:
        if row.get('type') is not None:
            HEADERS.append(row.get('label'))

#get course enrolls
course_enrollment=CourseEnrollment.objects.filter(course_id=course_key)

#grades reports summary
user_repports_summary=course_enrollment[0]
user_summary=user_repports_summary.user

if enable_time_tracking:
    HEADERS.append('Temps passé')

if graded:
    header_summary_base=CourseGradeFactory().create(user_summary, course).grade_value['grade_breakdown'].keys()

    for h in header_summary_base:
        HEADERS.append(h)

    HEADERS.append('Note finale')


#certificate_form
#if ajout_fichiers :
for fichier_name in ajout_fichiers:
    HEADERS.append(fichier_name)

#If application form field
if application_field:
    for value in application_form:
        HEADERS.append(value['label'])
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

#NOW LOOK AT GRADES & TIME TRACKING
j=0

for i in range(len(course_enrollment)):
    j=j+1
    user=course_enrollment[i].user
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
    client = email.split('@')[1]
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
    #course_grade

    #insert rows
    """
    primary_rows = [
        user.id,username,email,
        client,last_login,list_ip_str
    ]
    """
    primary_rows = [
        user.id,username,email,
        client,date_inscription, last_login
    ]

    l=0

    for prim_row in primary_rows:
        sheet.write(j, l, prim_row)
        l=l+1

    #add all values into for_lines
    for_lines = []
    user_lines = {}
    if register_users and register_form is not None:
        for reg_row in register_form:
            for_lines.append(reg_row)
        try:
            user_profile = json.loads(UserProfile.objects.get(user=user).custom_field)
        except:
            user_profile = {}
        for key,value in user_profile.items():
            user_lines[key] = value

    if certificate_users and certificate_form is not None:
        for reg_row in certificate_form:
            for_lines.append(reg_row)
        _mongo.user_id = user.id
        try:
          certificate = _mongo.getForm(microsite=True,user_id=True).get('form')
        except:
          certificate = {}
        for key,value in certificate.items():
            user_lines[key] = value

    # add form
    for _row in for_lines:
        for _key in user_lines.keys():
            if _row.get('name') == _key:
                if _row.get('type') == "select":
                    if _row.get('name') == "year_of_birth" or _row.get('name') == "month_of_birth" or _row.get('name') == "day_of_birth" or _row.get('name') == "age" or _row.get('name') == "country" or _row.get('name') == "nationalite":
                        sheet.write(j, l, user_lines[_row.get('name')])
                    else:
                        reg_op = _row.get('options')
                        for option in reg_op:
                            if user_lines[_row.get('name')] == option.get('value'):
                                sheet.write(j, l, option.get('name'))
                else:
                    sheet.write(j, l, user_lines[_row.get('name')])
        l=l+1

    #time tracking
    if enable_time_tracking:
        tma_enrollment,is_exist=TmaCourseEnrollment.objects.get_or_create(course_enrollment_edx=course_enrollment[i])
        seconds = tma_enrollment.global_time_tracking
        hour = seconds // 3600
        seconds %= 3600
        minute = seconds // 60
        global_time = str(hour)+"h"+str(minute)+"min"
        time_tracking = global_time
        sheet.write(j, l, time_tracking)
        l=l+1

    if graded:
        course_grade = CourseGradeFactory().create(user, course)
        percent = str(course_grade.percent * 100)+'%'
        for user_summary in course_grade.grade_value['grade_breakdown'].keys():
            summary_percent = course_grade.grade_value['grade_breakdown'].get(user_summary)['percent']
            try:
                summary_coef = float(course_grade.grade_value['grade_breakdown'].get(user_summary)['detail'].split(' of a possible ')[1].replace('%','')) / 100

                #Bonus courses with 0 Coef
                if summary_coef==0:
                    number_sections=0
                    student_score=[]
                    name_section=course_grade.grade_value['grade_breakdown'].get(user_summary)['category']
                    for course_part in course_grade.grade_value['section_breakdown']:
                        if course_part['category'] == name_section:
                            number_sections=number_sections+1
                            student_score.append(course_part['percent'])
                            if number_sections>1:
                                summary_grade= student_score[number_sections-1]*100
                            else :
                                summary_grade=student_score[0]*100
                else:
                    summary_grade = (course_grade.grade_value['grade_breakdown'].get(user_summary)['percent'] / summary_coef) * 100
                summary_grade = float(int(summary_grade * 100)) / 100

            except:
                summary_grade = 0.00
            summary_grade = str(summary_grade).replace('.',',')+"%"
            sheet.write(j, l, summary_grade)
            l=l+1
        sheet.write(j, l, percent.replace('.',','))
        l=l+1
    #check if cv link available
    if ajout_fichiers :
        for user_fichier in ajout_fichiers:
            file_check=mongofiles().is_file('file_api',user_fichier,user.id, domain_prefix)
            if file_check.get('status'):
                sheet.write(j, l, 'https://{}/tma_apps/files_api/v1/{}/{}/{}'.format(str(microsite.site),microsite_name,str(user_fichier),str(user.id)))
                l=l+1

    #application field
    if application_field:
        for value in application_form:
            application_field_value = None
            if value['name'] in user_profile.keys():
                application_field_value = user_profile[value['name']]
            else:
                application_field_value = ""
            sheet.write(j, l, application_field_value)
            l=l+1

output = BytesIO()

wb.save(output)

_files_values = output.getvalue()
# envoyer un mail test

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de données du MOOC {}<br/><br/>Bonne réception<br>The MOOC Agency<br></p></body></html>".format(course.display_name)
part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "ne-pas-repondre@themoocagency.com"
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

#update json log file
"""
if persistent:
    _log_file = open(file_path,'w')
    _log_file.write(json.dumps(_log_content, indent=4, sort_keys=True))
    _log_file.close()
"""
