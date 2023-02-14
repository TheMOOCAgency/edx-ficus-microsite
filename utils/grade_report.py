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
from datetime import datetime, date, timedelta

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
from tma_apps.models import TmaCourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment, UserProfile

from pprint import pformat


recipients_geography = {
    "e-formation@cma-auvergnerhonealpes.fr" : u"Auvergne-Rh\u00f4ne-Alpes",
    "formation@artisanat-bfc.fr": u"Bourgogne-Franche-Comt\u00e9",
    "contact-cfar@cma-bretagne.fr": u"Bretagne",
    "contact-formation.continue@cma-cvl.fr": u"Centre-Vale-de-Loire",
    "pdesire@cfm-ajaccio.org": u"Corse",
    "jpierrot@cmguadeloupe.org": u"Guadeloupe",
    "secretariat.fpc@cma-martinique.com": u"Martinique",
    "mbuisson@cmamayotte.com": u"Mayotte",
    "contact@cma-grandest.fr": u"Grand-Est",
    "formationscma@cma-hautsdefrance.fr": u"Hauts-de-France",
    "alexandre.chaubet-tavenot@cma-idf.fr": u"Ile-de-France",
    "formation@cma-normandie.fr": u"Normandie",
    "cmar-formation-continue@artisanat-nouvelle-aquitaine.fr": u"Nouvelle-Aquitaine",
    "urma@artisanatpaysdelaloire.fr": u"Pays de la Loire",
    "e-formation@crma-occitanie.fr": u"Occitanie",
    "e-formationcontinuepaca@cmar-paca.fr" : u"Provence-Alpes-C\u00f4te d'Azur",
    "vincent.bayol@cma-reunion.fr": u"La-Reunion",
    "l.lucenay@cfa-guyane.fr": u"Guyanne",
    "guimbert@cma-france.fr": u"Saint-Pierre-et-Miquelon",
    "guimbert@cma-france.fr": u"Saint-Barthelemy",
    "guimbert@cma-france.fr": u"Saint-Martin",
    "guimbert@cma-france.fr": u"Wallis et Futuna",
    "guimbert@cma-france.fr": u"Polynesie Française",
    "guimbert@cma-france.fr": u"Nouvelle Caledonie",
    "dimitri.hoareau@weuplearning.com": "tout"
}


# Auxiliary functions
def is_course_open(course):
    now = datetime.now(UTC())
    if course.start > now:
        return False
    else:
        return True

# SET MAIN VARIABLES
org = "academie-digitale"
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')
certificate_extra_form = configuration_helpers.get_value_for_org(org, 'CERTIFICATE_FORM_EXTRA')
form_factory = ensure_form_factory()
db = 'ensure_form'
collection = 'certificate_form'
form_factory.microsite = u"academie-digitale"

# Get headers
HEADERS_GLOBAL = []
HEADERS_USER = [u"Date d'inscription",u"Email"]

HEADERS_FORM = []
NICE_HEADERS_FORM = []
if register_form is not None:
    for row in register_form:
        if row.get('type') is not None:
            if 'first_name' not in row.get('name') and 'last_name' not in row.get('name'):
                HEADERS_FORM.append(row.get('name'))
                NICE_HEADERS_FORM.append(row.get('label'))

NICE_HEADER = list(NICE_HEADERS_FORM)
# NICE_HEADER.extend(["QP-Axe1","QP-Axe1p","QP-Axe3","QP-Axe4","QP-Axe5","QP-Axe7","QP-Axe8","QP-Axe9","QP-Axe9p","QP-Axe10","QP-Axe11","QP-Axe12","Note de cas pratique"])
TECHNICAL_HEADER = list(HEADERS_FORM)
# TECHNICAL_HEADER.extend(["score1","score1p","score3","score4","score5","score7","score8","score9","score9p","score10","score11","score12","cas_pratique_grade"])
HEADERS_USER.extend(NICE_HEADER)
HEADER = HEADERS_USER

course_ids=[
    "course-v1:academie-digitale+FC_B50+2022",
    "course-v1:academie-digitale+FC_20+2022",
    "course-v1:academie-digitale+FC_B20+2022",
    "course-v1:academie-digitale+FC_B40+2022",
    "course-v1:academie-digitale+FC_B30+2022"
]

def get_time_tracking(enrollment):

    try:
        tma_enrollment=TmaCourseEnrollment.objects.get_or_create(course_enrollment_edx=enrollment)
        global_time=tma_enrollment[0].global_time_tracking
    except:
        global_time = 0
    return global_time


def get_user_info(user, enrollment_date=''):

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
        first_name = custom_field.get('first_name', '')
    else:
        first_name = ""

    if user.last_name:
        last_name = user.last_name
    elif custom_field :
        last_name = custom_field.get('last_name', '')
    else:
        last_name = ""

    try:
        date_inscription = user.date_joined.strftime('%d %b %y')
    except:
        date_inscription = ""

    try:
        last_login = user.last_login.strftime('%d %b %y')
    except:
        last_login = ""

        
    user_row = [date_inscription, email]
    
    # CUSTOM FIELDS INFO
    for field in TECHNICAL_HEADER:
        try:
            user_row.append(custom_field[field])
        except:
            user_row.append('')

    # user_row.append("tma_global_time")

    return user_row

def get_user_first_connect(user, course_id):
    custom_field = {}
    date_value=''

    user_id = str(user.id)

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except Exception as e:
        log.info(e)
        pass

    form_factory.user_id = long(user_id)
    
    try:
        field_value = custom_field.get(course_id, '')
        if isinstance(field_value, int):
            field_value_string = datetime.fromtimestamp(field_value / 1e3).strftime("%d/%m/%Y")
            date_value = field_value_string
    except Exception as e:
        log.info(e)
        date_value = ''

    return date_value

# HEADER.append('Temps global') 

#### TRUE SCRIPT

j=0
for j in range(len(course_ids)):
    # Course info from argument
    course_id = course_ids[j]
    # Course info from argument
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key) 
    # HEADER.append('Note "{}"'.format(course.display_name_with_default))
    # HEADER.append('date d\'inscription "{}"'.format(course.display_name_with_default))
    # HEADER.append('1ere connexion "{}"'.format(course.display_name_with_default))

# First get all users even if not enrolled in any course
potentially_non_enrolled_user_ids = []
user_profiles = UserProfile.objects.all()
for user_profile in user_profiles:
    try:
        custom_field = json.loads(user_profile.custom_field)
    except:
        custom_field = {}
    if custom_field.get("microsite") == "academie-digitale":
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
    global_time = 0
    for i in range(len(enrollments)):

        # FOR DEBUG PURPOSES
        # if i > 50:
        #    break

        user = enrollments[i].user
        # Look for email and remove @weuplearning
        if user.email.find('@weuplearning') != -1 or user.email.find('@themoocagenc') != -1 :
            continue

        enrollment_user = enrollments.filter(course_id=course_key).filter(user=user.id).values('created')
        enrollment_date = enrollment_user[0]['created'].strftime("%m/%d/%Y")
        #As the user is enrolled in something remove it from potentially non enrolled users
        if user.id in potentially_non_enrolled_user_ids:
            potentially_non_enrolled_user_ids.remove(user.id)
        
        # If the user has never been seen before get its basic info
        if user.id not in users_data.keys():
            # USER INFO
            users_data[user.id] = {}
            users_data[user.id]["data"] = get_user_info(user, enrollment_date)
            users_data[user.id]["global_time"] = 0
        
        # get first login value
        first_connection = get_user_first_connect(user, course_id)
        first_register = enrollment_date
            
        # User already exists so
        # GET GRADES
        percent = "inscrit sans note"
        try:
            course_grade = CourseGradeFactory().create(user, course)
            percent = str(course_grade.percent * 100)+'%'
        except:
            pass

        # Final grade
        # diff = len(HEADER) - len(course_ids)*2 + j*2 - len(user_data[user.id]["data"])
        # log.info(diff)

        # if diff > 4 :
        #     user_data[user.id]["data"].extend([None] * diff)

        # users_data[user.id]["data"].append(percent)

        # users_data[user.id]["data"].append(first_register)

        # insert first login value
        # users_data[user.id]["data"].append(first_connection)

        #get global time tracking
        # global_time = get_time_tracking(enrollments[i])

        # users_data[user.id]["global_time"] += global_time

## Now we get all non enrolled users
for user_id in potentially_non_enrolled_user_ids:
    users_data[user.id] = {}
    users_data[user.id]["data"] = get_user_info(User.objects.get(id=user_id))
    # users_data[user.id]["global_time"] = 0


for recipient in recipients_geography:
    # WRITE FILE FOR ALL TIMES
    # Prepare workbook
    wb = Workbook(encoding='utf-8')
    filename_all_values = '/home/edxtma/csv/echantillon_complet.xls'
    sheet = wb.add_sheet('Rapport')
    style_title = easyxf('font: bold 1')
    for i in range(len(HEADER)):
        sheet.write(0, i, HEADER[i],style_title)

    j = 1
    for user in users_data:
        user_data = users_data[user]["data"]
        # global_time = users_data[user]["global_time"]
        # dans le cas d'un utilisateur ou tma_global_time a été remplacé par la valeur choisie, il n'y aura donc plus de 'tma_globaml_time' dans le tableau mais une date 

        # list_index = user_data.index('tma_global_time')
        # user_data[list_index] = str(timedelta(seconds=global_time))
                    
        # unidecode and avoid spaces and dashes
        #script may fail as user_data[6] seems to be int in some cases, meaning region is incorrectly provided
        try:
            unidecoded_user_field = unidecode(user_data[6].lower()).replace(" ","").replace("-","").replace("'","")
        except:
            unidecoded_user_field = ""

        try:
            unidecoded_recipient_geo = unidecode(recipients_geography[recipient].lower()).replace(" ","").replace("-","").replace("'","") 
        except:
            unidecoded_recipient_geo = ""


        if unidecoded_user_field == unidecoded_recipient_geo or unidecoded_recipient_geo == "tout":
            for i in range(len(user_data)):
                try:
                    sheet.write(j, i, user_data[i])
                except:
                    pass
            j = j + 1
        # user_data[list_index] = 'tma_global_time'

    output = BytesIO()
    wb.save(output)
    file_all_values = output.getvalue()


    # WRITE FILE FOR LAST WEEK ONLY
    # Prepare workbook
    wb = Workbook(encoding='utf-8')
    filename_lastweek = '/home/edxtma/csv/semaine_precedente.xls'
    sheet = wb.add_sheet('Rapport')
    style_title = easyxf('font: bold 1')
    for i in range(len(HEADER)):
        sheet.write(0, i, HEADER[i],style_title)

    j = 1
    now =  datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for user in users_data:
        user_data = users_data[user]["data"]

        # unidecode and avoid spaces and dashes
        try:
            unidecoded_user_field = unidecode(user_data[6].lower()).replace(" ","").replace("-","").replace("'","")
        except:
            unidecoded_user_field =  ""

        try:
            unidecoded_recipient_geo = unidecode(recipients_geography[recipient].lower()).replace(" ","").replace("-","").replace("'","")
        except:
            unidecoded_recipient_geo = ""

        if unidecoded_user_field == unidecoded_recipient_geo or unidecoded_recipient_geo == "tout":

            # We make sure that only new users are in the report
            date_joined = user_data[0]
            date_joined = datetime.strptime(user_data[0], '%d %b %y')
            if not(date_joined >=  now - timedelta(days=7) and date_joined < now):
                continue

            for i in range(len(user_data)):
                try:
                    sheet.write(j, i, user_data[i])
                except:
                    pass
            j = j + 1

    output = BytesIO()
    wb.save(output)
    file_lastweek = output.getvalue()


    html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de donn&eacute;es des inscrits aux formations disponibles sur formation.artisanat.fr pour votre r&eacute;gion: "+recipients_geography[recipient]+".<br/><br/>Pour toute question sur ce rapport merci de contacter technical@themoocagency.com.<br/><br/>Bonne r&eacute;ception<br><br>L'&eacute;quipe formation.artisanat.fr</p></body></html>"
    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

    fromaddr = "ne-pas-repondre@themoocagency.com"
    toaddr = [recipient,"technical@themoocagency.com", "guimbert@cma-france.fr", "alexandre.berteau@weuplearning.com"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Rapports formation.artisanat.fr - " + time.strftime("%d.%m.%Y")

    attachment = file_all_values
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename_all_values))
    msg.attach(part)

    attachment = file_lastweek
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename_lastweek))
    msg.attach(part)

    server = smtplib.SMTP('mail3.themoocagency.com', 25)
    server.starttls()
    server.login('contact', 'waSwv6Eqer89')
    msg.attach(part2)
    text = msg.as_string()
    #For debug purposes
    # server.sendmail(fromaddr, "dimitri.hoareau@weuplearning.com", text)
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    log.info('Email sent to '+str(toaddr))


# 30 0 * * MON sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/academie-digitale/utils/grade_report.py
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/academie-digitale/utils/grade_report.py
