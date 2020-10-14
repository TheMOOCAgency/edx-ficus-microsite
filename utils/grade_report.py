# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import time
import logging
from unidecode import unidecode
from xlwt import *

from io import BytesIO

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from datetime import datetime, date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey

from student.models import *

from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from lms.djangoapps.grades.context import grading_context_for_course, grading_context
from lms.djangoapps.tma_ensure_form.utils import ensure_form_factory
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from pprint import pformat


recipients_geography = {
    "parcours-createur@artisanat-nouvelle-aquitaine.fr" : u"Nouvelle-Aquitaine",
    "secretariat.sdae@cma-martinique.com" : u"Martinique",
    "parcrea@crma-centre.fr" : u"Centre-Val de Loire",
    "j.senellart@cma-hautsdefrance.fr" : u"Hauts-de-France",
    "eartisanat@crma-idf.fr" : u"\u00cele-de-France",
    "parcours-createur@crma-grandest.fr" : u"Grand-Est",
    "parcours.createur@crma-occitanie.fr" : u"Occitanie",
    "parcours.createur@crm-bretagne.fr" : u"Bretagne",
    "parcours.createur@cmar-paca.fr" : u"Provence-Alpes-C\u00f4te d'Azur",
    "parcours.createur@artisanatpaysdelaloire.fr":u"Pays de la Loire",
    "ParcoursCrea@artisanat-bfc.fr":u"Bourgogne-Franche-Comt\u00e9",
    "parcours-creation@crma-auvergnerhonealpes.fr":u"Auvergne-Rh\u00f4ne-Alpes",
    "aurelien.croq@weuplearning.com":u"Tout",
    "tom.douce@weuplearning.com":u"Tout",
    "yoann.mroz@weuplearning.com":u"Tout"
}

# Auxiliary functions
def is_course_open(course):
    now = datetime.now(UTC())
    if course.start > now:
        return False
    else:
        return True

# SET MAIN VARIABLES
org = "e-formation-artisanat"
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')
certificate_extra_form = configuration_helpers.get_value_for_org(org, 'CERTIFICATE_FORM_EXTRA')
form_factory = ensure_form_factory()
db = 'ensure_form'
collection = 'certificate_form'
form_factory.microsite = u"e-formation-artisanat"

# Get headers
HEADERS_GLOBAL = []
HEADERS_USER = [u"ID", u"Nom d'utilisateur", u"Email", u"Prénom", u"Nom",u"Date d'inscription",u"Dernière connexion"]

HEADERS_FORM = []
if register_form is not None:
    for row in register_form:
        if row.get('type') is not None:
            if 'first_name' not in row.get('name') and 'last_name' not in row.get('name'):
                HEADERS_FORM.append(row.get('name'))

NICE_HEADER = list(HEADERS_FORM)
NICE_HEADER.extend(["QP-Axe1","QP-Axe1p","QP-Axe3","QP-Axe4","QP-Axe5","QP-Axe7","QP-Axe8","QP-Axe9","QP-Axe9p","QP-Axe10","QP-Axe11","QP-Axe12"])

TECHNICAL_HEADER = list(HEADERS_FORM)
TECHNICAL_HEADER.extend(["score1","score1p","score3","score4","score5","score7","score8","score9","score9p","score10","score11","score12"])

HEADERS_USER.extend(NICE_HEADER)

HEADER = HEADERS_USER

print HEADER


course_ids=[
    "course-v1:e-formation-artisanat+Pack_Micro+e-formation-2020",
    "course-v1:e-formation-artisanat+commercial+2020_T1",
    "course-v1:e-formation-artisanat+essentiels+2020_T1",
    "course-v1:e-formation-artisanat+gestion+2020_T1",
    "course-v1:e-formation-artisanat+premium+2020_T1",
    "course-v1:e-formation-artisanat+Module_01+SP_01",
    "course-v1:e-formation-artisanat+Module_02+SP_02",
    "course-v1:e-formation-artisanat+Module_03+SP_03",
    "course-v1:e-formation-artisanat+Module_04+SP_04",
    "course-v1:e-formation-artisanat+Module_05+SP_05",
    "course-v1:e-formation-artisanat+Module_06+SP_06",
    "course-v1:e-formation-artisanat+Module_07+SP_07",
    "course-v1:e-formation-artisanat+Module_08+SP_08",
    "course-v1:e-formation-artisanat+Module_09+SP_09",
    "course-v1:e-formation-artisanat+Module_09-+SP_09-",
    "course-v1:e-formation-artisanat+Module_10+SP_10",
    "course-v1:e-formation-artisanat+Module_11+SP_11",
    "course-v1:e-formation-artisanat+Module_12+SP_12"
    ]


def get_user_info(user):
    user_profile = {}
    email = user.email
    custom_field = {}
    certificate_field = {}

    user_id = str(user.id)
    user_profile = UserProfile.objects.get(user_id=user_id)

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except:
        pass

    form_factory.user_id = long(user_id)
    
    if user.first_name:
        first_name = user.first_name
    elif custom_field :
        first_name = custom_field.get('first_name', 'n/a')
    else:
        first_name = "n/a"

    if user.last_name:
        last_name = user.last_name
    elif custom_field :
        last_name = custom_field.get('last_name', 'n/a')
    else:
        last_name = "n/a"

    try:
        date_inscription = user.date_joined.strftime('%d %b %y')
    except:
        date_inscription = "n/a"

    try:
        last_login = user.last_login.strftime('%d %b %y')
    except:
        last_login = "n/a"
        
    user_row = [user.id, user.username, email, first_name, last_name, date_inscription, last_login]
    
    # CUSTOM FIELDS INFO
    for field in TECHNICAL_HEADER:
        try:
            user_row.append(custom_field[field])
        except:
            user_row.append('n/a')

    return user_row

def get_user_first_connect(user, course_id):
    custom_field = {}
    date_value='n/a'

    user_id = str(user.id)

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except Exception as e:
        log.info(e)
        pass

    form_factory.user_id = long(user_id)
    
    try:
        field_value = custom_field.get(course_id, 'n/a')
        if isinstance(field_value, int):
            field_value_string = datetime.fromtimestamp(field_value / 1e3).strftime("%d/%m/%Y")
            date_value = field_value_string
    except Exception as e:
        log.info(e)
        date_value = 'n/a'

    return date_value


#### TRUE SCRIPT

j=0
for j in range(len(course_ids)):
    # Course info from argument
    course_id = course_ids[j]
    # Course info from argument
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key) 
    HEADER.append('Note "{}"'.format(course.display_name_with_default))
    HEADER.append('1ere connexion "{}"'.format(course.display_name_with_default))

# First get all users even if not enrolled in any course
potentially_non_enrolled_user_ids = []
user_profiles = UserProfile.objects.all()
for user_profile in user_profiles:
    try:
        custom_field = json.loads(user_profile.custom_field)
    except:
        custom_field = {}
    if custom_field.get("microsite") == "e-formation-artisanat":
        potentially_non_enrolled_user_ids.append(user_profile.user_id)

users_data = {}

# Now get info for all users enrolled in courses
j=0
for j in range(len(course_ids)):
    # Course info from argument
    course_id = course_ids[j]
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key) 
    enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    # Write headers for course grades
    first_enrollment = enrollments[0]
    user_summary = first_enrollment.user
    
    i = 0
    for i in range(len(enrollments)):
        user = enrollments[i].user

        #As the user is enrolled in something remove it from potentially non enrolled users
        if user.id in potentially_non_enrolled_user_ids:
            potentially_non_enrolled_user_ids.remove(user.id)
        
        # If the user has never been seen before get its basic info
        if user.id not in users_data.keys():
            # USER INFO
            users_data[user.id] = get_user_info(user)
        
        # get first login value
        first_connection = get_user_first_connect(user, course_id)
            
        # User already exists so
        # GET GRADES
        percent = "inscrit sans note"
        try:
            course_grade = CourseGradeFactory().create(user, course)
            percent = str(course_grade.percent * 100)+'%'
        except:
            pass

        # Final grade
        diff = len(HEADER) - len(course_ids)*2 + j - len(users_data[user.id])

        if diff > 0 :
            users_data[user.id].extend([None] * diff)

        users_data[user.id].append(percent)
        # insert first login value
        users_data[user.id].append(first_connection)

            

## Now we get all non enrolled users
for user_id in potentially_non_enrolled_user_ids:
    users_data[user_id] = get_user_info(User.objects.get(id=user_id))

for recipient in recipients_geography:
    # WRITE FILE
    # Prepare workbook
    wb = Workbook(encoding='utf-8')
    filename = '/home/edxtma/csv/e-formation.artisanat.fr_{}.xls'.format(time.strftime("%d.%m.%Y"))
    sheet = wb.add_sheet('Rapport')
    style_title = easyxf('font: bold 1')
    for i in range(len(HEADER)):
        sheet.write(0, i, HEADER[i],style_title)

    j = 1
    for user in users_data:
        user_data = users_data[user]
        # unidecode and avoid spaces and dashes
        if unidecode(user_data[11].lower()).replace(" ","").replace("-","").replace("'","") == unidecode(recipients_geography[recipient].lower()).replace(" ","").replace("-","").replace("'","") or recipients_geography[recipient].lower() == "tout":
            for i in range(len(user_data)):
                sheet.write(j, i, user_data[i])
            j = j + 1

    # SEND MAILS
    output = BytesIO()
    wb.save(output)
    _files_values = output.getvalue()

    html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de donn&eacute;es des inscrits aux formations disponibles sur e-formation.artisanat.fr pour votre r&eacute;gion: "+recipients_geography[recipient]+".<br/><br/>Pour toute question sur ce rapport merci de contacter technical@themoocagency.com.<br/><br/>Bonne r&eacute;ception<br><br>L'&eacute;quipe e-formation-artisanat.fr</p></body></html>"

    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

    fromaddr = "ne-pas-repondre@themoocagency.com"
    toaddr = [recipient,"technical@themoocagency.com","benissan-wicart@cma-france.fr"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Rapport e-formation-artisanat.fr - " + time.strftime("%d.%m.%Y")
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
    log.info('Email sent to '+str(toaddr))
