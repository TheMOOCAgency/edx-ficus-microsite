Yoann Mroz

26/01/2021

grade_report.py is launched every night at 00:00
it takes as arguments:
- org, wich in this case is bnpp-netexplo
- rapport_ancienne_aca_v2.csv wich is a file containing users datas of previous platform

the script generate a file wich path is '/edx/var/edxapp/media/microsite/bnpp-netexplo/reports/{}_BNP_ACA.xls'.format(time.strftime("%d.%m.%Y")

rapport_ancienne_aca_v2.csv is a merged file from 3 different files stored in backup : export-users-condensed.csv, export-users-expedition.csv, export-users-journey.csv
- export-users-condensed.csv is a file containing the best grade date of every users that has finished every courses in previous platform
- export-users-expedition.csv is a file containing every finish dates for every sub section of course expedition for users in previous platform
- export-users-journey.csv is a file containing every finish dates for every sub section of course journey for users in previous platform


Why merge these 3 files ?

Because the client wanted to to get a report that give these informations in columns expedition and journey:
- if user has completed every sub section in current or previous platform: show best grade date
- if user has finish some sub section in previous and/or current platform: show the number of sub section finished


Where do the client get the report ?

here: https://bnp-paribas.netexplo.academy/dashboard (Télécharger le rapport)