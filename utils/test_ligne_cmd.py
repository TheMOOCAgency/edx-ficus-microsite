from common.djangoapps.student.models import User
from lms.djangoapps.courseware.models import StudentModule
# from openpyxl import Workbook
#openpyxl 3.0.7
import os
import time
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# ## Workbook
# wb = Workbook()
# ws = wb.active
# ws.title = "Grade report"


# list_of_student_modules = StudentModule.objects.filter(course_id__exact="course-v1:amazon+amazon001+SP", module_type__exact="video").order_by().values().distinct()

# list_user_in_video_db =[]

# for e in list_of_student_modules:
#     list_user_in_video_db.append(e['student_id'])
    
# print(list_user_in_video_db)
# ## Construct data
# users = User.objects.all()
# users_data = dict()
# siret = dict()

# for user in users:
#     user_data = dict()

#     # Escape fake email address
#     if user.email.find("@example")!= -1 or user.email.find("@themoocagency") != -1 or user.email.find("@weuplearning")!= -1 or user.email.find("@yopmail")!= -1 or user.email.find("@amazon")!= -1 or user.email.find("@fake")!= -1:
#         pass

#     else:
#         # Access region and company via shell cmd

#         # cmd = ' zgrep -hoP "\\[WUL\\]\\K.*" /edx/var/log/supervisor/* | sed \'s/ Email: //\' | sed \'s/ - Specialty: /|/\' | sed \'s/ - Company: /|/\' | grep "{}" '.format(user.email)
#         # stream = os.popen(cmd)
#         # output = stream.read()
#         # output = output.replace("\n", "|")
#         # output = str(output).split("|")

#         try:
#             user_data["id"] = user.id
#         except:
#             user_data["id"] = ""

#         try:
#             user_data["username"] = user.username
#         except:
#             user_data["username"] = ""

#         try:
#             user_data["email"] = user.email
#         except:
#             user_data["email"] = ""

#         try:
#             user_data["region"] = output[1]
#         except:
#             user_data["region"] = ""

#         try:
#             user_data["siret"] = output[2]
#             if output[2] == "":
#                 pass
#             else:
#                 siret[output[2]] = siret.get(output[2],0) +1
#         except:
#             user_data["siret"] = ""

#         try:
#             user_data["date_joined"] = user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
#         except:
#             user_data["date_joined"] = ""

#         try:
#             for result in list_of_student_modules:
#                 if(user.id == result["student_id"]):
#                     user_data["watch_a_video"] = "oui"
#                     break
#                 else:
#                     user_data["watch_a_video"] = ""
#         except:
#             print("error with watch a video field")
#             user_data["watch_a_video"] = ""

#         users_data[user.username.capitalize()]= user_data

# ordered_users = sorted(users_data.items(), key=lambda x: x[1]["username"])

# ## Print excel file
# # Headers
# row = 1
# cell1 = ws.cell(row=row, column=1, value="Username")
# cell2 = ws.cell(row=row, column=2, value="Email")
# cell3 = ws.cell(row=row, column=3, value="A vu une vidéo")
# cell4 = ws.cell(row=row, column=4, value="Region")
# cell5 = ws.cell(row=row, column=5, value="Siret")
# cell6 = ws.cell(row=row, column=6, value="Nombre de users de l'entreprise")
# cell7 = ws.cell(row=row, column=7, value="Date de création de compte")
# row += 1
# # Data
# for user in ordered_users:
#     cell1 = ws.cell(row=row, column=1, value=user[1]["username"])
#     cell2 = ws.cell(row=row, column=2, value=user[1]["email"])
#     cell3 = ws.cell(row=row, column=3, value=user[1]["watch_a_video"])
#     cell4 = ws.cell(row=row, column=4, value=user[1]["region"])
#     cell5 = ws.cell(row=row, column=5, value=user[1]["siret"])
#     cell6 = ws.cell(row=row, column=6, value=siret.get(user[1]["siret"],0))
#     cell7 = ws.cell(row=row, column=7, value=user[1]["date_joined"])
#     row += 1

# timestr = time.strftime("%Y_%m_%d")
# filename = "Rapport_amazon_{}.xlsx".format(timestr)
# filepath = '/home/ubuntu/amazon_reports/{}'.format(filename)
# wb.save(filename)


# ## Send email
# output = BytesIO()
# wb.save(output)
# _files_values = output.getvalue()

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en pièce jointe le rapport de donn&eacute;es Amazon"

part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

fromaddr = "ne-pas-repondre@themoocagency.com"
toaddr = "cyril.adolf@weuplearning.com"
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Rapport Amazon"

attachment = _files_values
part = MIMEBase('application', 'octet-stream')
part.set_payload(attachment)
encoders.encode_base64(part)
part.add_header('Content-Disposition', "attachment; filename= {}".format(filename))
msg.attach(part)

server = smtplib.SMTP('mail3.themoocagency.com', 25)
server.starttls()
server.login('contact', 'waSwv6Eqer89')
msg.attach(part2)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

print('Email sent to ',toaddr)


# script located in /home/ubuntu (koa-PRODAMAZON)
# start with : 
# source /edx/app/edxapp/edxapp_env && /edx/app/edxapp/edx-platform/manage.py lms shell < test_rapport_CA.py