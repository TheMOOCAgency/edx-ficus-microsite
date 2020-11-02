# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#Password & Hash
import random
import string

#IMPORT FOR SCRIPT TO
##RUN
##WRITE EXCEL FILE
##SEND EMAIL
import os
import glob
import importlib
import time
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
import django
##USE EDX FUNCTIONS
from django.http import HttpResponse
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.courseware import courses
from student.models import *
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
# from tma_apps.files_api.api import file_api
from datetime import datetime, timedelta
import pytz
import logging
log = logging.getLogger()
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)
from tma_apps.files_api.models import mongofiles

utc=pytz.UTC
one_week_ago = datetime.now() - timedelta(days=7)

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
try:
    course_id = sys.argv[2]
except:
    pass
    course_id = ""

course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
timestr = time.strftime("%Y_%m_%d")
zip_path = '/edx/var/edxapp/media/microsite/operation-raffinage/zip/'
cv_path = '/edx/var/edxapp/media/microsite/operation-raffinage/cv/'
download_url = 'https://operation-raffinage.com/media/microsite/operation-raffinage/zip/'

#clean zip folder
zip_files = glob.glob(zip_path+'*')
for f in zip_files:
    os.remove(f)

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
#mongo certificate_form models
_mongo = ensure_form_models()
db = 'ensure_form'
collection = 'certificate_form'
_mongo.connect(db=db,collection=collection)
_mongo.microsite = domain_prefix

#get course enrolls
course_enrollement=CourseEnrollment.objects.filter(course_id=course_key)

#Create fake request
class Request:
  def __init__(self, user):
    self.user = user

class file_api(mongofiles):
    def __init__(self):
        mongofiles.__init__(self)

    def download_file(self,request,datatype,user_id):
        #check if cv link available
        file_check=mongofiles().is_file('file_api',datatype,user.id, domain_prefix)
        if file_check.get('status'):
            _valid_ext = {
                'jpg':'image/png',
                'jpeg':'image/png',
                'png':'image/png',
                'pdf':'application/pdf',
                'doc':'application/vnd.ms-word',
                'docx':'application/vnd.ms-word',
                'odt':'application/vnd.oasis.opendocument.text'
            }

            user_id = int(user_id)
            collection = 'file_api'
            _download = self.download(collection,user.id,domain_prefix,datatype)
            infos = _download.get('return_data')
            _ext = infos._file.get('extention')
            upload_date =  infos.upload_date.strftime('%Y-%m-%d')
            filename = '{}_{}.{}'.format(upload_date,user.email,_ext)
            #filename = infos._file.get('filename')
            _file = infos.read()
            content_type = _valid_ext[_ext]

            if infos.upload_date >= one_week_ago :
                log.info('[WUL] user {} has a cv : {}'.format(str(user.id),filename))
                return {'file':_file,'filename':filename}
            else :
                log.info('[WUL] user {} has an outdated cv : {}'.format(str(user.id),filename))
                return False
        else:
            return False

request = Request(User.objects.get(email="yoann.mroz@themoocagency.com"))

for i in range(len(course_enrollement)):
    user=course_enrollement[i].user
    user_cv = file_api().download_file(request,'cv',user.id)
    if user_cv:
        f = open(cv_path+user_cv['filename'], "w")
        f.write(user_cv['file'])
        f.close()
        
def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

#create new zip file
file_hash = get_random_alphanumeric_string(32)
password = get_random_alphanumeric_string(8)
zip_filename = 'cv_{}_{}.zip'.format(timestr,file_hash)
os_command = ("7z -r -p{} a {}{} {}".format(password,zip_path,zip_filename,cv_path))
log.info(os_command)
os.system(os_command)

#clean cv folder
cv_files = glob.glob(cv_path+'*')
for f in cv_files:
    os.remove(f)

# envoyer un mail test

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous pouvez télécharger le fichier ZIP des utilisateurs ayant uploadé leur CV entre le {} et le {} à l'issue du cours {} en cliquant sur le lien suivant :<br/><br/>{}{}<br/>Vous aurez besoin du mot de passe suivant pour ouvrir le fichier : {}<br/><br/>Bonne réception<br>The MOOC Agency<br></p></body></html>".format(one_week_ago.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'),course.display_name, download_url,zip_filename, password)
part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "ne-pas-repondre@themoocagency.com"
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "Les CV des utilisateurs 'operation-raffinage'"
   #attachment = _zip_file
   part = MIMEBase('application', 'octet-stream')
   #part.set_payload(attachment)
   encoders.encode_base64(part)
   #part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(_zip_file))
   #msg.attach(part)
   server = smtplib.SMTP('mail3.themoocagency.com', 25)
   server.starttls()
   server.login('contact', 'waSwv6Eqer89')
   msg.attach(part2)
   text = msg.as_string()
   server.sendmail(fromaddr, toaddr, text)
   server.quit()
   print 'mail send to '+str(TO_EMAILS[i])
