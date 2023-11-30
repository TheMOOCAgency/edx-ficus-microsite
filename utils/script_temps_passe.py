# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')


import os
import importlib
from io import BytesIO


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()



from courseware.courses import get_course_by_id
from tma_apps.models import TmaCourseEnrollment
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from student.models import User



from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import json
import datetime

from zipfile import ZipFile

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib


import logging
log = logging.getLogger()



email_subject = "Fichiers PDF compressés"
email_body = "Veuillez trouver ci-joint les fichiers PDF compressés."

all_pdf_urls = []


def convert_seconds_in_hours(time_in_seconds):  
    seconds = time_in_seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if len(str(seconds)) == 1:
        seconds = "0" + str(seconds)
    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    time_in_hours = '{}:{}:{}'.format(hours, minutes, seconds)
    return (time_in_hours)



# Fonction pour générer le fichier PDF pour un étudiant donné
def generate_student_time_sheet(course_id, user_email):

    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    user = User.objects.get(email=user_email)

    custom_field={}
    try :
        custom_field=json.loads(user.profile.custom_field)
        first_name=custom_field['first_name']
        last_name=custom_field['last_name']
    except :
        last_name='Undefined'
        first_name='Undefined'

    try:
        tma_course_enrollment = TmaCourseEnrollment.objects.get(course_enrollment_edx__user=user, course_enrollment_edx__course_id=course_key)
        global_time_tracking = tma_course_enrollment.global_time_tracking
    except:
        pass

    microsite= 'e-formation-artisanat'

    page_width = 600
    page_height = 1200
    line_height = 20
    font_size = 12


    image_up_left_url = '/edx/var/edxapp/media/microsite/{}/fiche_suivi/up_logo.png'.format(microsite)

    font_variants = ("OpenSans-Regular","OpenSans-Bold")
    folder = '/edx/var/edxapp/media/fonts/'
    for variant in font_variants:
        pdfmetrics.registerFont(TTFont(variant, os.path.join(folder, variant+'.ttf')))

    # Créer le fichier PDF pour l'étudiant
    pdf_filename = user_email + "_fiche_de_presence.pdf"
    p = canvas.Canvas(pdf_filename)

    p.setPageSize((page_width,page_height))
    # p.setFont(font_name, font_size)
    if microsite == "e-formation-artisanat":
        p.drawImage(image_up_left_url, 40, 1060, width=100,height=100, mask='auto')
    elif microsite == "e-ferro":
        p.drawImage(image_up_left_url, 40, 1060, width=125,height=100, mask='auto')
    else:
        p.drawImage(image_up_left_url, 40, 1060, width=100,height=100, mask='auto')


    x = 430
    y = 1150
    p.setFont("OpenSans-Bold", font_size)
    p.drawString(x, y, 'Fiche de suivi')
    y -= line_height 
    x -= 34
    p.setFont("OpenSans-Regular", font_size)
    p.drawString(x, y, 'Editée le: {}'.format(datetime.datetime.today().strftime('%d/%m/%Y')))
    y -= line_height * 7
    x = 50

    p.setFont("OpenSans-Bold", font_size)
    p.drawString(x, y, 'Formation :')
    y -= line_height 
    p.setFont("OpenSans-Regular", font_size)
    p.drawString(x, y, course.display_name_with_default)
    y -= line_height
    p.setFont("OpenSans-Bold", font_size) 
    p.drawString(x, y, 'Nom, Prénom du stagiaire :')
    y -= line_height
    p.setFont("OpenSans-Regular", font_size)
    try:
        p.drawString(x, y, last_name + ", "  + first_name)
    except:
        p.drawString(x, y, "Undefined")

    y -= line_height
    try:
        if custom_field["birthday"]:
            p.setFont("OpenSans-Bold", font_size)
            p.drawString(x, y, 'Date de naissance :')
            y -= line_height 
            p.setFont("OpenSans-Regular", font_size)
            p.drawString(x, y, custom_field["birthday"])
            y -= line_height
    except:
        pass


    try:
        p.setFont("OpenSans-Bold", font_size)
        p.drawString(x, y, 'Temps total passé :')
        y -= line_height
        p.setFont("OpenSans-Regular", font_size)
        try: 
            p.drawString(x, y, str(convert_seconds_in_hours(global_time_tracking)))
        except:
            p.drawString(x, y, "00:00:00")
            
        y -= line_height * 3
    except:
        pass

    try:
        # DETAILED TIME TRACKING DISPLAY
        detailed_time_tracking = json.loads(tma_course_enrollment.detailed_time_tracking)
        chapters = course.get_children()
        modules_total_time = sum(detailed_time_tracking[chapter.url_name] for chapter in chapters if chapter.url_name in detailed_time_tracking.keys())

        time_delta = global_time_tracking - modules_total_time
        delta_module_split = time_delta / len(chapters)
        log.info(user_email)
        log.info(delta_module_split)
        p.setFont("OpenSans-Bold", font_size)
        p.drawString(x, y, 'Détail par module:')
        y -= line_height
        
        for chapter in chapters:
            p.setFont("OpenSans-Bold", 10)
            if chapter.url_name in detailed_time_tracking.keys():
                p.drawString(x, y, chapter.display_name_with_default_escaped)
                y -= line_height
                p.setFont("OpenSans-Regular", 10)
                p.drawString(x, y, str(convert_seconds_in_hours((detailed_time_tracking[chapter.url_name]) + delta_module_split)))
            else:
                p.drawString(x, y, chapter.display_name_with_default_escaped)
                y -= line_height 
                p.setFont("OpenSans-Regular", 10)
                p.drawString(x, y, str(convert_seconds_in_hours(delta_module_split)))
            y -= line_height * 1.2
        y -= line_height * 2
    except:
        pass

    try:
        # DAILY TIME TRACKING DISPLAY
        daily_time_tracking = json.loads(tma_course_enrollment.daily_time_tracking)
        if daily_time_tracking.items():
            p.setFont("OpenSans-Bold", font_size)
            p.drawString(x, y, 'Détail par jour:')
            y -= line_height
            sorted_dates = daily_time_tracking.items()
            sorted_dates.sort(key=lambda date: datetime.datetime.strptime(date[0], "%d-%m-%Y"))
            daily_total_time = sum(date[1] for date in sorted_dates)

            if global_time_tracking > daily_total_time:
                p.setFont("OpenSans-Regular", 10)
                time_delta = global_time_tracking - daily_total_time
                p.drawString(x, y, 'Avant le {}: {}'.format(sorted_dates[0][0].replace('-', '/'), str(convert_seconds_in_hours(time_delta))))
                y -= line_height

            for date in sorted_dates:
                p.drawString(x, y, '{} : {}'.format(date[0].replace('-', '/'), str(convert_seconds_in_hours(date[1]))))
                y -= line_height

    except:
        pass

    try:
        # Not for everyone
        y_display_image = y - 100
        image_down_middle_url = '/edx/var/edxapp/media/microsite/{}/fiche_suivi/down_logo.jpg'.format(microsite)
        p.drawImage(image_down_middle_url, 200, y_display_image, width=200,height=100)
    except:
        pass
    
    p.showPage()
    p.save()
    return pdf_filename








# Fonction pour compresser les fichiers PDF dans un fichier ZIP
def compress_pdfs_to_zip(pdf_filenames, zip_filename):
    with ZipFile(zip_filename, "w") as zip_file:
        for pdf_filename in pdf_filenames:
            zip_file.write(pdf_filename)

# Fonction pour envoyer l'e-mail avec le fichier ZIP en pièce jointe
def send_email_with_attachment(zip_filename):

    msg = MIMEMultipart()
    msg["From"] = "ne-pas-repondre@themoocagency.com"
    msg["To"] = sys.argv[1]
    msg["Subject"] = email_subject
    msg.attach(MIMEText(email_body, "plain"))

    with open(zip_filename, "rb") as attachment:
        attached_zip = MIMEApplication(attachment.read(), _subtype="zip")
        attached_zip.add_header("Content-Disposition", "attachment; filename="+os.path.basename(zip_filename))
        msg.attach(attached_zip)

    text = msg.as_string()

    # Connexion au serveur SMTP et envoi de l'e-mail
    server = smtplib.SMTP('mail3.themoocagency.com', 25)

    server.starttls()
    server.login('contact', 'waSwv6Eqer89')
    server.sendmail("ne-pas-repondre@themoocagency.com", sys.argv[1], text)
    server.quit()
    log.info('Email sent to '+str(sys.argv[1]))



try:
    courses = sys.argv[2].split(';')
except:
    log.info('********************** Pas de cours **********************')
    courses = []


for course_id in courses :

    course_key = CourseKey.from_string(course_id)
    course_enrollments = CourseEnrollment.objects.filter(course_id=course_key)

    for enrollment in course_enrollments :

        pdf_url = generate_student_time_sheet(course_id, enrollment.user.email)

        all_pdf_urls.append(pdf_url)



    # Compresser les fichiers PDF dans un fichier ZIP
    zip_filename = "fichiers_pdf.zip"
    compress_pdfs_to_zip(all_pdf_urls, zip_filename)

    # Envoyer l'e-mail avec le fichier ZIP en pièce jointe
    send_email_with_attachment(zip_filename)

    # Supprimer le fichier ZIP après l'envoi
    os.remove(zip_filename)



# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/e-formation-artisanat/utils/script_temps_passe.py 'cyril.adolf@weuplearning.com' 'course-v1:e-formation-artisanat+essentiels+2020_T1;course-v1:e-formation-artisanat+2019+01'

