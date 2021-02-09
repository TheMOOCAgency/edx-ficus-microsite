#!/usr/bin/env python

import os
import importlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.core.management import execute_from_command_line
import django

from student.models import *

from xlwt import *

import json


_file = open('/home/edxtma/afpa_dev/export_user.log','r')
_content = _file.readlines()
i = 0
for n in _content:
    _log = json.loads(n)
    _name = _log[0]
    _name = _name.split(' ')
    try:
        _last_name = _name[0]
    except:
        _last_name = ''
    try:
        _first_name = _name[1]
    except:
        _first_name = ''
    _email = _log[1]
    print _last_name+' '+_first_name

    try:
        user = User.objects.get(email=_email)
        profile = UserProfile.objects.get(user=user)
        custom = profile.custom_field
        if not "_name" in custom:
            try:
                _json = json.loads(custom)
            except:
                _json = {}
            if _json.get('first_name') is None and _first_name:
                _json['first_name'] = _first_name
            if  _json.get('last_name') is None and _last_name:
                _json['last_name'] = _last_name

            profile.custom_field = json.dumps(_json)
            profile.save()
            print profile.custom_field
            i = i +1
            print i
    except:
        pass
