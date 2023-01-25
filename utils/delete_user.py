# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import logging
import importlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from enrollment.api import get_enrollments
from student.models import CourseEnrollment
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger()

users_list_to_delete = [
    "cpeyronnel@artisanat-bourgogne.fr","f.toffin@cma-hautsdefrance.fr","c.boudeele@cma-hautsdefrance.fr","l.mazourov@cma-hautsdefrance.fr","f.pages@cma-hautsdefrance.fr","nicole.negron@cma-allier.fr","laurence.lemaire@cma-allier.fr","marie-luce.aufaure@cma-allier.fr","fabienne.gonzalez@cma-allier.fr","magali.blot@cma-allier.fr","aurelie.livrozet@cma-allier.fr","dominique.vignaud@cma-allier.fr","jacqueline.enrico@cma-allier.fr","celie.melac@cma-allier.fr","laure.giraud@cma-allier.fr","fabienne.perronnet@cma-allier.fr","marie-laure.maitre-brunet@cma-allier.fr","m.vo@cmar-paca.fr","n.elhamdaoui@cmar-paca.fr","a.theze@cmar-paca.fr","g.cuynat@cmar-paca.fr","d.dostert@cmar-paca.fr","f.maltese@cmar-paca.fr","j.lopez@cmar-paca.fr","e.choisy@cmar-paca.fr","n.munezero@cm-ariege.fr","c.maubert@cma-ariege.fr","l.naudy@cm-ariege.fr","e.gomez@cm-ariege.fr","c.buffard@cm-ariege.fr","emaho@cma-aube.fr","jsampaio@cma-aube.fr","v.suarez@cm-aude.fr","j.arrighi@cm-aude.fr","formation@cm-aude.fr","p.mestre@cm-aude.fr","s.marsaud@cm-aude.fr","david.granel@cm-aude.fr","d.granel@cm-aude.fr","emmanuelle.grailhe-covinhes@cm-aveyron.fr","cbert@cm-alsace.fr","c.guidini@cmar-paca.fr","s.frichemann@cmar-paca.fr","c.reboul@cmar-paca.fr","v.altemir@cmar-paca.fr","m.denhadji@cmar-paca.fr","m.dangleant@cmar-paca.fr","c.inglard@cmar-paca.fr","m.moraldo@cmar-paca.fr","c.slomian@cmar-paca.fr","f.masselin@cmar-paca.fr","j.audat@cmar-paca.fr","p.garces@cmar-paca.fr","p.fritsch@cmar-paca.fr","c.luneau@cmar-paca.fr","c.changeux@cmar-paca.fr","m.berthelot@cmar-paca.fr","m.mielle@cmar-paca.fr","o.chazaud@cmar-paca.fr","v.lesant@cmar-paca.fr","u.chalard@cmar-paca.fr","s.sommer@cmar-paca.fr","s.gualtieri@cmar-paca.fr","c.pillier@cmar-paca.fr","m.esquembre@cmar-paca.fr","b.bernard@cmar-paca.fr","e.riffaud@cmar-paca.fr","s.degieux@cmar-paca.fr","m.vandendries@cmar-paca.fr","ghislaine.franceschini@cm-bourges.fr","ndeloule@artisanat-bfc.fr","h.varisco@artisanat-comtois.fr","carole.neveu@cma-28.fr","quentin.moyer@cma-28.fr","lbolze@cma-cvl.fr","corentin.demeersman@cma-28.fr","yannick.lemoigne@cma29.fr","christine.pasi@cma-gard.fr","sabah.najai@cma-gard.fr","myriam-boissiere.de-cillia@cma-gard.fr","jean-claude.galanti@cma-gard.fr","rafik.hadadi@cma-gard.fr","katia.browarski@cma-gard.fr","thierry.bertrand@cma-gard.fr","patricia.fratti@cma-gard.fr","caroline.nineuil@cma-gard.fr","sandrine.ducros@cma-gard.fr","bernard.bigorre@cma-gard.fr","celine.louis@cma-gard.fr","sylvie.parasmo@cma-gard.fr","aurelle.fullana@cma-gard.fr","thomas.rech@cma-gard.fr","sabine.fabre@cma-gard.fr","sandra.mallem-vaxelaire@cma-gard.fr","fvoglimacci@cm-toulouse.fr","lperrier@cm-toulouse.Fr","ljoulia@cm-toulouse.fr","mdebray@cm-toulouse.fr","phouard@cm-toulouse.fr","a.esmieu@cmar-paca.fr","s.leca@cmar-paca.fr","n.boisseranc@cmar-paca.fr","j.briand@cmar-paca.fr","sgoldstein@cm-alsace.fr","sbataille@cma-nanterre.fr","fjacomet@cma-nanterre.fr","j.palier@cma-herault.fr","ml.comos@cma-herault.fr","c.negron@cma-herault.fr","f.clerc@cma-herault.fr","o.gelebart@cma-herault.fr","S.MALLIE@cma-herault.fr","c.sergeant@cma-herault.fr","a.fregeac@cma-herault.fr","d.roulle@cma-herault.fr","e.roucoules@cma-herault.fr","s.malvaldi@cma-herault.fr","i.viraud@cm-indre.fr","aboussereau@cm-tours.fr","cecile.keller@cma-isere.fr","fabien.golbarani@cma-isere.fr","nadine.casula@cma-isere.fr","aurelien.carmona@cma-auvergnerhonealpes.fr","stephanie.hidalgo@cma-isere.fr","charlotte.laumay@cma-isere.fr","florian.nury@cma-isere.fr","aurelia.gros@cma-isere.fr","laurence.debernardi@cma-isere.fr","alexandre.franceschi@cma-isere.fr","olivier.dequick@cma-isere.fr","camille.barbagallo@cma-isere.fr","eric.balandreau@cma-isere.fr","jean-daniel.guillermin@cma-isere.fr","charline.nazaret@cma-isere.fr","guillaume.dore@cma-isere.fr","s.maghnaoui@artisanat-comtois.fr","al.mouget@artisanat-comtois.fr","philippe.ramin@cma-reunion.fr","celiane.audit@cma-reunion.fr","laurence.babet@cma-reunion.fr","cbeautrais@artisanatpaysdelaloire.fr","k.grivolat@crma-france.fr","K.Grivolat@crma-centre.fr","c.bille@cma-loiret.fr","ytomasi@cma-41.fr","francoise.gravil@cm-lozere.fr","c.lagin@cma-martinique.com","abarottin@cma-meurthe-et-moselle.fr","lmonso@cma-meurthe-et-moselle.fr","thierry.normand@cma-morbihan.fr","lrousseau@artisanat-bourgogne.fr","e.salerno@artisanat-bourgogne.fr","b.meunier@cma-hautsdefrance.fr","l.balsack@cma-hautsdefrance.fr","n.bertrand@artisanat-nordpasdecalais.fr","f.oudart@cma-hautsdefrance.fr","j.cablat@cma-hautsdefrance.fr","t.cerbelle@cma-hautsdefrance.fr","s.deblock@cma-hautsdefrance.fr","mathieu.dubois@cma-hautsdefrance.fr","t.edesa@cma-hautsdefrance.fr","t.gaulupeau@cma-hautsdefrance.fr","f.karst@cma-hautsdefrance.fr","c.menneveux@cma-hautsdefrance.fr","c.nomberg@cma-hautsdefrance.fr","c.adoum@cma-hautsdefrance.fr","jp.job@cma-hautsdefrance.fr","mc.vainck@cma-hautsdefrance.fr","a.saminathen@cma-hautsdefrance.fr","q.colette@cma-hautsdefrance.fr","c.valcke@cma-hautsdefrance.fr","r.daviau@cma-hautsdefrance.fr","d.piecq@cma-hautsdefrance.fr","j.kleczewski@cma-hautsdefrance.fr","j.assense@cma-hautsdefrance.fr","mi.togo@cma-hautsdefrance.fr","n.damm@cma-hautsdefrance.fr","c.floury@cma-hautsdefrance.fr","aurelien.guillemet@cma-idf.fr","berthelot.emilie@cma-paris.fr","christelle.margalho@cma-paris.fr","philippe.blaize@cma-paris.fr","brigitte.simonet@cma-paris.fr","francoise.neveu@cma-paris.fr","alban.tortevoix@cma-paris.fr","patricia.guyot@cma-paris.fr","des-courtis@cma-france.fr","e.deblock@cma-hautsdefrance.fr","x.evrard@cma-hautsdefrance.fr","m.mannessiez@cma-hautsdefrance.fr","c.deroy@cma-hautsdefrance.fr","p.perron@cma-hautsdefrance.fr","dominique.boutheon@cma66.fr","ebriche@artisanat-bourgogne.fr","pmartin@artisanat-bourgogne.fr","claudine.blanchys@cm-aveyron.fr","malika.nebchi@cma77.fr","tefery.duleme@cma77.fr","aissata.lesaffre@cma77.fr","jackie.margie@cma77.fr","jean-pierre.paviot@cma77.fr","delphine.barjolin@cma77.fr","clement.jerome@cma77.fr","junie.auguste@cma77.fr","severine.malgat@cma77.fr","s.cesa@cma93.fr","f.lefloch@cma93.fr","g.djoric@cma93.fr","valerie.gelard@cma-idf.fr","e.guyomard@cma-hautsdefrance.fr","c.henocq@cma-hautsdefrance.fr","julien.faure@cm-tarn.fr","a.pinel@cm-montauban.fr","p.dubernet@cm-montauban.fr","v.canourgues@cm-montauban.fr","c.barthes@cm-montauban.fr","h.gilhodes@cm-montauban.fr","a.gratusse@cm-montauban.fr","d.faron@artisanat-comtois.fr","jmias@artisanat-bfc.fr","s.guibert@artisanat-comtois.fr","adauchy@cma94.com","j.colonna@cmar-paca.fr","l.luccioni@cmar-paca.fr","a.bah@cmar-paca.fr","g.fillol@cmar-paca.fr","l.nguyen@cmar-paca.fr","r.rolfo@cmar-paca.fr","l.manche@cmar-paca.fr","s.petit@cmar-paca.fr","e.larre@cmar-paca.fr","s.goffart@cmar-paca.fr","annie.riou@cma29.fr"
]

for user_email in users_list_to_delete:
    log.info(user_email)
    user = User.objects.get(email=user_email)
    enrollments = get_enrollments(user.username)

    for enrollment in enrollments :
        course_id = enrollment.get('course_details').get('course_id')
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        log.info('[WUL] : {} has been unenrolled from : {}'.format(user_email, course_id))
        CourseEnrollment.unenroll(user, course_id)
    
    enrollments = get_enrollments(user.username)
    # if (len(enrollments) == 0) :
    #     user_id = user.id
    #     User.objects.get(id=user_id).delete()
    #     log.info('[WUL] : Successfully deleted user : {}'.format(user_email))
    # else:
    #     log.error('[WUL] : NOT ALL ENROLLMENTS DELETED FOR USER {}'.format(user_email))


# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/e-formation-artisanat/utils/delete_user.py