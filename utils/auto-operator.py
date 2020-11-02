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
from datetime import datetime, timedelta
import pytz
import logging
log = logging.getLogger()

from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)
from tma_apps.files_api.models import mongofiles

utc=pytz.UTC

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
try:
    course_id = sys.argv[2]
except:
    pass
    course_id = ""

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
one_week_ago = datetime.now() - timedelta(days=7)

#get microsite
org = course.org
query = "SELECT a.id,a.organization,b.key FROM microsite_configuration_micrositeorganizationmapping a,microsite_configuration_microsite b WHERE a.microsite_id = b.id"
microsite_list = MicrositeOrganizationMapping.objects.raw(query)
microsite_name = None
for row in microsite_list:
    if row.organization == org:
        microsite_name = row.key

domain_prefix = None

microsite = Microsite.objects.get(key=microsite_name)
microsite_value = microsite.values
i=0
for val in microsite_value:
    if val == 'domain_prefix':
        domain_prefix = microsite_value.values()[i]
    i=i+1

timestr = time.strftime("%Y_%m_%d")
timesfr = time.strftime("%d.%m.%Y")
timesfr = str(timesfr)

#headers
HEADERS = ["Nom","Prénom","adresse email","ville","pays","why mooc","note finale", "lien cv"]

#get course enrolls
course_enrollement=CourseEnrollment.objects.filter(course_id=course_key)

# European countries for filtering
euList = [
	{'country':'Austria','code':'AT','vat':20},
	{'country':'Belgium','code':'BE','vat':21},
	{'country':'Bulgaria','code':'BG','vat':20},
	{'country':'Croatia','code':'HR','vat':25},
	{'country':'Cyprus','code':'CY','vat':19},
	{'country':'Czech Republic','code':'CZ','vat':21},
	{'country':'Denmark','code':'DK','vat':25},
	{'country':'Estonia','code':'EE','vat':20},
	{'country':'Finland','code':'FI','vat':24},
	{'country':'France','code':'FR','vat':20},
	{'country':'Germany','code':'DE','vat':19},
	{'country':'Greece','code':'EL','vat':24},
	{'country':'Hungary','code':'HU','vat':27},
	{'country':'Ireland','code':'IE','vat':23},
	{'country':'Italy','code':'IT','vat':22},
	{'country':'Latvia','code':'LV','vat':21},
	{'country':'Lithuania','code':'LT','vat':21},
	{'country':'Luxembourg','code':'LU','vat':17},
	{'country':'Malta','code':'MT','vat':18},
	{'country':'Netherlands','code':'NL','vat':21},
	{'country':'Poland','code':'PO','vat':23},
	{'country':'Portugal','code':'PT','vat':23},
	{'country':'Romania','code':'RO','vat':20},
	{'country':'Slovakia','code':'SK','vat':20},
	{'country':'Slovenia','code':'SI','vat':22},
	{'country':'Spain','code':'ES','vat':21},
	{'country':'Sweden','code':'SW','vat':25},
	{'country':'United Kingdom','code':'GB','vat':20},
]

#prepare workbook

wb = Workbook(encoding='utf-8')

filename = '/home/edxtma/csv/{}_{}.xls'.format(timestr,course.display_name_with_default)
sheet = wb.add_sheet('Stats')
for i, header in enumerate(HEADERS):
   sheet.write(0, i, header)

j=0
for i in range(len(course_enrollement)):
    user=course_enrollement[i].user
    
    last_login = user.last_login
    if last_login and last_login >= utc.localize(one_week_ago) :
        #Grade
        course_grade = CourseGradeFactory().create(user, course)

        #Filter users who have grade 80% or more
        if course_grade.percent >= 0.8 :

            user_profile = {}
            try:
                user_profile = json.loads(UserProfile.objects.get(user=user).custom_field)
            except:
                user_profile = {}

            why_mooc=user_profile.get('why_mooc','n/a')

            country=user_profile.get('country','n/a')
            countryValid = False

            for eu in euList:
                if country in eu['country'] or country in eu['code']:
                    countryValid = True

            #Filter users who wants to become operator, and come from European country
            if why_mooc == 'op' and countryValid:
                j=j+1

                last_name=user_profile.get('last_name','n/a')
                first_name=user_profile.get('first_name','n/a')
                email=user.email
                town=user_profile.get('city','n/a')
                final_grade='n/a'
                cv_link='n/a'

                final_grade = str(course_grade.percent * 100)+'%'

                #cv link
                file_check=mongofiles().is_file('file_api','cv',user.id, domain_prefix)
                if file_check.get('status'):
                    cv_link='https://{}/tma_apps/files_api/v1/{}/cv/{}'.format(str(microsite.site),microsite_name,str(user.id))

                #insert rows
                primary_rows = [
                    last_name,first_name,email,town,country,why_mooc,final_grade,cv_link
                ]

                l=0
                for prim_row in primary_rows:
                    sheet.write(j, l, prim_row)
                    l=l+1

output = BytesIO()

wb.save(output)

_files_values = output.getvalue()
# envoyer un mail test

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de données du MOOC {} des personnes ayant eu 80 sur 100 ou plus à la note finale, souhaitant devenir opérateur et s'étant connecté au moins une fois ces 7 derniers jours.<br/><br/>Bonne réception<br>The MOOC Agency<br></p></body></html>".format(course.display_name)
part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "ne-pas-repondre@themoocagency.com"
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "Rapport de donnees restreint"
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