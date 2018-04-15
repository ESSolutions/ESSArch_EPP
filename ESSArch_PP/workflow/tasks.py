"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

from __future__ import absolute_import

import copy
import datetime
import errno
import logging
import os
import shutil
import smtplib
import tarfile
import tempfile
import time
import uuid
import zipfile

from copy import deepcopy

from celery import states as celery_states
from celery.exceptions import Ignore
from celery.result import allow_join_result, AsyncResult

from crontab import CronTab

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, IntegerField, Max
from django.db.models.functions import Cast
from django.utils import timezone

from groups_manager.utils import get_permission_name

from guardian.shortcuts import assign_perm

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

import requests

from scandir import walk

from six.moves import urllib

from ESSArch_Core import tasks
from ESSArch_Core.auth.models import Member, Notification
from ESSArch_Core.configuration.models import ArchivePolicy, Path, Parameter
from ESSArch_Core.essxml.util import parse_submit_description
from ESSArch_Core.fixity.checksum import calculate_checksum
from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalLocation,
    ArchivalType,
    EventIP,
    InformationPackage,
    Workarea,
)
from ESSArch_Core.maintenance.models import AppraisalRule, AppraisalJob, AppraisalJobEntry, ConversionRule, ConversionJob, ConversionJobEntry
from ESSArch_Core.profiles.utils import fill_specification_data
from ESSArch_Core.search.ingest import index_path
from ESSArch_Core.storage.exceptions import (
    TapeDriveLockedError,
    TapeMountedError,
    TapeMountedAndLockedByOtherError,
    TapeUnmountedError,
)
from ESSArch_Core.storage.copy import copy_file
from ESSArch_Core.storage.models import (
    DISK,
    TAPE,

    AccessQueue,
    IOQueue,

    Robot,
    RobotQueue,
    TapeDrive,
    TapeSlot,

    StorageMedium,
    StorageMethod,
    StorageMethodTargetRelation,
    StorageObject,
)
from ESSArch_Core.util import (
    creation_date,
    find_destination,
    timestamp_to_datetime,
)
from ESSArch_Core.WorkflowEngine.dbtask import DBTask
from ESSArch_Core.WorkflowEngine.models import ProcessTask, ProcessStep

from ip.serializers import InformationPackageDetailSerializer

from storage.serializers import IOQueueSerializer

User = get_user_model()

logger = logging.getLogger('essarch')

class ReceiveSIP(DBTask):
    event_type = 20100

    def run(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=[]):
        aip = InformationPackage.objects.get(pk=ip)
        policy = ArchivePolicy.objects.get(pk=policy)
        objid, container_type = os.path.splitext(os.path.basename(container))

        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC, responsible=aip.responsible,
                                                label=aip.label, start_date=aip.start_date, end_date=aip.end_date,
                                                archival_institution=aip.archival_institution,
                                                archivist_organization=aip.archivist_organization,
                                                archival_type=aip.archival_type,
                                                archival_location=aip.archival_location,)
        aip.aic = aic

        parsed = parse_submit_description(xml, srcdir=os.path.split(container)[0])

        archival_institution = parsed.get('archival_institution')
        archivist_organization = parsed.get('archivist_organization')
        archival_type = parsed.get('archival_type')
        archival_location = parsed.get('archival_location')

        if archival_institution:
            arch, _ = ArchivalInstitution.objects.get_or_create(
                name=archival_institution
            )
            aip.archival_institution = arch

        if archivist_organization:
            arch, _ = ArchivistOrganization.objects.get_or_create(
                name=archivist_organization
            )
            aip.archivist_organization = arch

        if archival_type:
            arch, _ = ArchivalType.objects.get_or_create(
                name=archival_type
            )
            aip.archival_type = arch

        if archival_location:
            arch, _ = ArchivalLocation.objects.get_or_create(
                name=archival_location
            )
            aip.archival_location = arch

        aip.tags = tags

        aip_dir = aip.object_path
        os.makedirs(aip_dir)

        ProcessTask.objects.create(
            name="ESSArch_Core.tasks.CreatePhysicalModel",
            params={
                "structure": aip.get_profile('aip').structure,
                "root": aip_dir,
            },
            log=EventIP,
            information_package=aip,
            responsible_id=self.responsible,
        ).run().get()

        if policy.receive_extract_sip:
            dst = find_destination('content', aip.get_profile('aip').structure, aip_dir)
            dst = os.path.join(dst[0], dst[1])

            if container_type.lower() == '.tar':
                with tarfile.open(container) as tar:
                    tar.extractall(dst.encode('utf-8'))
            elif container_type.lower() == '.zip':
                with zipfile.ZipFile(container) as zipf:
                    zipf.extractall(dst.encode('utf-8'))
        else:
            dst = os.path.join(aip_dir, 'content', objid + container_type)
            shutil.copy(container, dst)

        aip.save(update_fields=[
            'aic', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'object_path',
        ])

        recipient = User.objects.get(pk=self.responsible).email
        if recipient:
            try:
                logger.debug("Sending mail")
                subject = 'Received "%s"' % aip.object_identifier_value
                body = '"%s" is now received and ready for archiving' % aip.object_identifier_value
                send_mail(subject, body, 'e-archive@essarch.org', [recipient], fail_silently=False)
            except smtplib.SMTPException:
                logger.exception("Failed to send mail")
            except smtplib.socket.error:
                logger.exception("SMTP connection failed")
            else:
                logger.debug("Mail sent")

        return ip

    def undo(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=None):
        pass

    def event_outcome_success(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=None):
        return "Received IP '%s'" % str(ip)


class ReceiveAIP(DBTask):
    event_type = 30710

    def run(self, workarea):
        workarea = Workarea.objects.prefetch_related('ip').get(pk=workarea)
        ip = workarea.ip

        ip.state = 'Receiving'
        ip.save(update_fields=['state'])

        ingest = ip.policy.ingest_path
        dst = os.path.join(ingest.value, ip.object_identifier_value)

        ProcessTask.objects.create(
            name='ESSArch_Core.tasks.CopyDir',
            args=[ip.object_path, dst],
            processstep_id=self.step,
            information_package=ip,
            responsible_id=self.responsible,
        ).run().get()

        ip.object_path = dst
        ip.state = 'Received'
        ip.save()

        workarea.delete()

    def undo(self, workarea):
        pass

    def event_outcome_success(self, workarea):
        pass


class CacheAIP(DBTask):
    event_type = 30310

    def run(self, aip):
        aip_obj = InformationPackage.objects.prefetch_related('policy').get(pk=aip)
        policy = aip_obj.policy
        srcdir = aip_obj.object_path
        objid = aip_obj.object_identifier_value

        dstdir = os.path.join(policy.cache_storage.value, objid)
        dsttar = dstdir + '.tar'
        dstxml = dstdir + '.xml'

        try:
            os.makedirs(dstdir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with tarfile.open(dsttar, 'w') as tar:
            for root, dirs, files in walk(srcdir):
                rel = os.path.relpath(root, srcdir)
                for d in dirs:
                    src = os.path.join(root, d)
                    arc = os.path.join(objid, rel, d)
                    arc = os.path.normpath(arc)

                    index_path(aip_obj, src)

                    tar.add(src, arc, recursive=False)

                    try:
                        os.makedirs(os.path.normpath(os.path.join(dstdir, rel, d)))
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise

                for f in files:
                    src = os.path.join(root, f)
                    dst = os.path.join(dstdir, rel, f)
                    dst = os.path.normpath(dst)

                    index_path(aip_obj, src)

                    shutil.copy2(src, dst)
                    tar.add(src, os.path.normpath(os.path.join(objid, rel, f)))

        algorithm = policy.get_checksum_algorithm_display()
        checksum = calculate_checksum(dsttar, algorithm=algorithm)

        info = fill_specification_data(aip_obj.get_profile_data('aip_description'), ip=aip_obj, sa=aip_obj.submission_agreement)
        info["_IP_CREATEDATE"] = timestamp_to_datetime(creation_date(dsttar)).isoformat()

        aip_desc_profile = aip_obj.get_profile('aip_description')
        filesToCreate = {
            dstxml: {
                'spec': aip_desc_profile.specification,
                'data': info
            }
        }

        aip_profile = aip_obj.get_profile_rel('aip').profile
        mets_dir, mets_name = find_destination("mets_file", aip_profile.structure)
        mets_path = os.path.join(srcdir, mets_dir, mets_name)

        ProcessTask.objects.create(
            name="ESSArch_Core.tasks.GenerateXML",
            params={
                "filesToCreate": filesToCreate,
                "folderToParse": dsttar,
                "extra_paths_to_parse": [mets_path],
                "algorithm": algorithm,
            },
            processstep_id=self.step,
            processstep_pos=self.step_pos,
            information_package=aip_obj,
            responsible_id=self.responsible,
        ).run().get()

        InformationPackage.objects.filter(pk=aip).update(
            message_digest=checksum, message_digest_algorithm=policy.checksum_algorithm,
        )

        ProcessTask.objects.create(
            name='ESSArch_Core.tasks.UpdateIPSizeAndCount',
            params={'ip': aip},
            information_package_id=aip,
            responsible_id=self.responsible,
        ).run().get()

        aicxml = os.path.join(policy.cache_storage.value, str(aip_obj.aic.pk) + '.xml')
        aicinfo = fill_specification_data(aip_obj.get_profile_data('aic_description'), ip=aip_obj.aic)
        aic_desc_profile = aip_obj.get_profile('aic_description')

        filesToCreate = {
            aicxml: {
                'spec': aic_desc_profile.specification,
                'data': aicinfo
            }
        }

        parsed_files = []

        for ip in aip_obj.aic.information_packages.order_by('generation'):
            parsed_files.append({
                'FName': ip.object_identifier_value + '.tar',
                'FExtension': 'tar',
                'FDir': '',
                'FParentDir': '',
                'FChecksum': ip.message_digest,
                'FID': str(uuid.uuid4()),
                'daotype': "borndigital",
                'href': ip.object_identifier_value + '.tar',
                'FMimetype': 'application/x-tar',
                'FCreated': ip.create_date,
                'FFormatName': 'Tape Archive Format',
                'FFormatVersion': 'None',
                'FFormatRegistryKey': 'x-fmt/265',
                'FSize': str(ip.object_size),
                'FUse': 'Datafile',
                'FChecksumType': ip.get_message_digest_algorithm_display(),
                'FLoctype': 'URL',
                'FLinkType': 'simple',
                'FChecksumLib': 'ESSArch',
                'FIDType': 'UUID',
            })

        ProcessTask.objects.create(
            name="ESSArch_Core.tasks.GenerateXML",
            params={
                "filesToCreate": filesToCreate,
                "parsed_files": parsed_files,
                "algorithm": algorithm,
            },
            processstep_id=self.step,
            processstep_pos=self.step_pos,
            information_package=aip_obj,
            responsible_id=self.responsible,
        ).run().get()

        InformationPackage.objects.filter(pk=aip).update(
            object_path=dstdir, cached=True
        )

        return aip

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Cached AIP '%s'" % aip


class StoreAIP(DBTask):
    hidden = True

    def run(self, aip):
        policy = InformationPackage.objects.prefetch_related('policy__storage_methods__targets').get(pk=aip).policy

        if not policy:
            raise ArchivePolicy.DoesNotExist("No policy found in IP: '%s'" % aip)

        storage_methods = policy.storage_methods.filter(status=True)

        if not storage_methods.exists():
            raise StorageMethod.DoesNotExist("No storage methods found in policy: '%s'" % policy)

        objid, aic, size = InformationPackage.objects.values_list('object_identifier_value', 'aic_id', 'object_size').get(pk=aip)
        aic = str(aic)
        cache_dir = policy.cache_storage.value
        xml_file = os.path.join(cache_dir, objid) + '.xml'
        xml_size = os.path.getsize(xml_file)
        aic_xml_file = os.path.join(cache_dir, aic) + '.xml'
        aic_xml_size = os.path.getsize(aic_xml_file)

        step = ProcessStep.objects.create(
            name='Write to storage',
            parent_step_id=self.step,
        )

        with transaction.atomic():
            for method in storage_methods.secure_storage():
                for method_target in method.storage_method_target_relations.filter(status=1):
                    req_type = 10 if method_target.storage_method.type == TAPE else 15

                    entry, created = IOQueue.objects.get_or_create(
                        storage_method_target=method_target, req_type=req_type,
                        ip_id=aip, status__in=[0, 2, 5],
                        defaults={'user_id': self.responsible, 'status': 0, 'write_size': size+xml_size+aic_xml_size}
                    )

                    if created:
                        InformationPackage.objects.filter(pk=aip).update(state='Preserving')

                    entry.step = step
                    entry.save(update_fields=['step'])

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Created entries in IO queue for AIP '%s'" % aip


class AccessAIP(DBTask):
    def run(self, aip, tar=True, extracted=False, new=False, package_xml=False, aic_xml=False, object_identifier_value=""):
        aip = InformationPackage.objects.get(pk=aip)

        # if it is a received IP, i.e. from ingest and not from storage,
        # then we read it directly from disk and move it to the ingest workarea
        if aip.state == 'Received':
            if not extracted and not new:
                raise ValueError('An IP must be extracted when transferred to ingest workarea')

            responsible = User.objects.get(pk=self.responsible)

            if new:
                # Create new generation of the IP

                old_aip = aip.pk
                new_aip = aip.create_new_generation('Ingest Workarea', responsible, object_identifier_value)
                aip = InformationPackage.objects.get(pk=old_aip)
            else:
                new_aip = aip

            workarea = Path.objects.get(entity='ingest_workarea').value
            workarea_user = os.path.join(workarea, responsible.username)
            dst_dir = os.path.join(workarea_user, new_aip.object_identifier_value, )

            ProcessTask.objects.create(
                name='ESSArch_Core.tasks.CopyDir',
                args=[aip.object_path, dst_dir],
                information_package=aip
            ).run().get()

            workarea_obj = Workarea.objects.create(ip=new_aip, user_id=self.responsible, type=Workarea.INGEST, read_only=not new)
            Notification.objects.create(message="%s is now in workarea" % new_aip.object_identifier_value, level=logging.INFO, user_id=self.responsible, refresh=True)

            if new:
                new_aip.object_path = dst_dir
                new_aip.save(update_fields=['object_path'])

            return str(workarea_obj.pk)

        if object_identifier_value is None:
            object_identifier_value = ''

        AccessQueue.objects.get_or_create(
            ip=aip, status__in=[0, 2, 5], package=tar,
            extracted=extracted, new=new,
            defaults={'user_id': self.responsible, 'object_identifier_value': object_identifier_value,
                      'package_xml': package_xml, 'aic_xml': aic_xml}
        )
        return


    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Created entries in IO queue for AIP '%s'" % aip


class PrepareDIP(DBTask):
    logger = logging.getLogger('essarch.epp.tasks.PrepareDIP')

    def run(self, label, object_identifier_value=None, orders=[]):
        disseminations = Path.objects.get(entity='disseminations').value

        try:
            perms = copy.deepcopy(settings.IP_CREATION_PERMS_MAP)
        except AttributeError:
            msg = 'IP_CREATION_PERMS_MAP not defined in settings'
            self.logger.error(msg)
            raise ImproperlyConfigured(msg)

        ip = InformationPackage.objects.create(
            object_identifier_value=object_identifier_value,
            label=label,
            responsible_id=self.responsible,
            state="Prepared",
            package_type=InformationPackage.DIP,
        )

        self.ip = ip.pk
        ip.orders.add(*orders)

        member = Member.objects.get(django_user__id=self.responsible)
        user_perms = perms.pop('owner', [])
        organization = member.django_user.user_profile.current_organization
        organization.assign_object(ip, custom_permissions=perms)

        for perm in user_perms:
            perm_name = get_permission_name(perm, ip)
            assign_perm(perm_name, member.django_user, ip)

        ProcessTask.objects.filter(pk=self.request.id).update(
            information_package=ip,
        )

        ProcessStep.objects.filter(tasks__pk=self.request.id).update(
            information_package=ip,
        )

        ip_dir = os.path.join(disseminations, ip.object_identifier_value)
        os.mkdir(ip_dir)

        ip.object_path = ip_dir
        ip.save(update_fields=['object_path'])

        return ip.pk

    def undo(self, label, object_identifier_value=None, orders=[]):
        pass

    def event_outcome_success(self, label, object_identifier_value=None, orders=[]):
        return 'Prepared DIP "%s"' % self.ip


class CreateDIP(DBTask):
    event_type = 30600

    def run(self, ip):
        ip = InformationPackage.objects.get(pk=ip)

        if ip.package_type != InformationPackage.DIP:
            raise ValueError('"%s" is not a DIP, it is a "%s"' % (ip, ip.package_type))

        ip.state = 'Creating'
        ip.save(update_fields=['state'])

        src = ip.object_path
        order_path = Path.objects.get(entity='orders').value

        order_count = ip.orders.count()

        for idx, order in enumerate(ip.orders.all()):
            dst = os.path.join(order_path, str(order.pk), ip.object_identifier_value)
            shutil.copytree(src, dst)

            self.set_progress(idx+1, order_count)

        ip.state = 'Created'
        ip.save(update_fields=['state'])

    def undo(self, ip):
        pass

    def event_outcome_success(self, ip):
        return 'Created DIP "%s"' % ip


class PollAccessQueue(DBTask):
    def copy_from_cache(self, entry):
        step = ProcessStep.objects.create(
            name='Copy from cache',
            parent_step_id=self.step,
        )
        cache_dir = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache_dir, entry.ip.object_identifier_value)
        cache_tar_obj = cache_obj + '.tar'
        in_cache = os.path.exists(cache_tar_obj)

        if not in_cache:
            # not in cache
            entry.status=100
            entry.save(update_fields=['status'])
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), cache_tar_obj)
        else:
            entry.ip.cached = True
            entry.ip.save(update_fields=['cached'])

        if not os.path.exists(cache_obj):
            with tarfile.open(cache_tar_obj) as tarf:
                tarf.extractall(cache_obj.encode('utf-8'))

        access = Path.objects.get(entity='access_workarea').value
        access_user = os.path.join(access, entry.user.username)
        dst_dir = os.path.join(access_user, entry.new_ip.object_identifier_value)
        dst_tar = dst_dir + '.tar'

        try:
            os.mkdir(access_user)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        copy_file(cache_tar_obj, dst_tar)

        if entry.package_xml:
            copy_file(cache_obj + '.xml', dst_dir + '.xml')

        if entry.aic_xml:
            copy_file(os.path.join(cache_dir, str(entry.ip.aic.pk) + '.xml'), os.path.join(access_user, str(entry.ip.aic.pk) + '.xml'))

        if entry.extracted:
            # Since the IP is packaged with the name of the first IP generation it will be extracted under that name.
            # If we are extracting for a new generation and we already have the first generation in the workarea as
            # read-only, we have to make sure we don't move (rename) the read-only version.
            # We do this by instead extracting the new generation to a temporary folder which we then move to the
            # correct destination

            tmpdir = tempfile.mkdtemp(dir=access_user)

            with tarfile.open(dst_tar) as tarf:
                tarf.extractall(tmpdir.encode('utf-8'))

            os.rename(os.path.join(tmpdir, str(entry.ip.object_identifier_value)), dst_dir)
            shutil.rmtree(tmpdir)

        if not entry.package:
            os.remove(dst_tar)

        Workarea.objects.create(ip=entry.new_ip, user=entry.user, type=Workarea.ACCESS, read_only=not entry.new)
        Notification.objects.create(message="%s is now in workarea" % entry.new_ip.object_identifier_value, level=logging.INFO, user=entry.user, refresh=True)

        if entry.new:
            entry.new_ip.object_path = dst_dir
            entry.new_ip.save(update_fields=['object_path'])

        entry.status = 20
        entry.save(update_fields=['status'])
        return

    def get_available_storage_objects(self, entry):
        storage_objects = entry.ip.storage.filter(
            storage_medium__status__in=[20, 30],
            storage_medium__location_status=50,
        )

        if not storage_objects.exists():
            entry.status = 100
            entry.save(update_fields=['status'])
            raise StorageObject.DoesNotExist("IP %s not archived on active medium" % entry.ip)

        return storage_objects


    def run(self):
        # Completed IOQueue entries are in the cache,
        # continue entry by copying from there

        entries = AccessQueue.objects.filter(
            status=5, ioqueue__status=20
        ).order_by('posted')

        for entry in entries:
            try:
                self.copy_from_cache(entry)
            except:
                entry.status = 100
                entry.save(update_fields=['status'])
                raise

        # Look for failed IOQueue entries

        entries = AccessQueue.objects.filter(
            status=5, ioqueue__status=100
        ).order_by('posted')

        for entry in entries:
            # io entry failed, are there any other available storage_objects we can use?
            self.get_available_storage_objects(entry)

            # at least one available storage object, try again
            entry.status = 2
            entry.save(update_fields=['status'])
            IOQueue.objects.filter(access_queue=entry).update(access_queue=None)


        entries = AccessQueue.objects.filter(
            status__in=[0, 2]
        ).order_by('posted')[:5]

        if not len(entries):
            raise Ignore()

        for entry in entries:
            entry.status = 2
            entry.save(update_fields=['status'])

            if entry.new:
                # Create new generation of the IP
                old_aip = entry.ip.pk
                new_aip = entry.ip.create_new_generation('Access Workarea', entry.user, entry.object_identifier_value)
                aip = InformationPackage.objects.get(pk=old_aip)
            else:
                new_aip = entry.ip

            entry.new_ip = new_aip
            entry.save(update_fields=['new_ip'])

            if entry.ip.cached:
                # The IP is flagged as cached, try copying from there

                try:
                    entry.status = 5
                    entry.save(update_fields=['status'])

                    self.copy_from_cache(entry)

                    entry.status = 20
                    entry.save(update_fields=['status'])
                    return
                except:
                    # failed to copy from cache, get from storage instead
                    entry.status = 2
                    entry.save(update_fields=['status'])

                    entry.ip.cached = False
                    entry.ip.save(update_fields=['cached'])

            def get_optimal(objects):
                # Prefer disks over tapes
                on_disk = objects.filter(content_location_type=DISK).first()

                if on_disk is not None:
                    storage_object = on_disk
                    req_type = 25
                else:
                    on_tape = objects.filter(content_location_type=TAPE).first()
                    if on_tape is not None:
                        storage_object = on_tape
                        req_type = 20
                    else:
                        raise StorageObject.DoesNotExist

                return storage_object, req_type

            storage_objects = self.get_available_storage_objects(entry)
            local_storage_objects = storage_objects.filter(storage_medium__storage_target__remote_server__exact='')

            try:
                # Local storage is (probably) faster, prefer it over remote storage
                storage_object, req_type = get_optimal(local_storage_objects)
            except StorageObject.DoesNotExist:
                # No local storage, try remote instead
                storage_object, req_type = get_optimal(storage_objects)

            target = storage_object.storage_medium.storage_target
            method_target = StorageMethodTargetRelation.objects.filter(
                storage_target=target, status__in=[1, 2],
            ).first()

            if method_target is None:
                entry.status = 100
                entry.save(update_fields=['status'])
                raise StorageMethodTargetRelation.DoesNotExist()

            try:
                io_entry, _ = IOQueue.objects.get_or_create(
                    storage_object=storage_object, req_type__in=[20, 25],
                    ip=entry.ip, status__in=[0, 2, 5], defaults={
                        'status': 0, 'user': entry.user,
                        'storage_method_target': method_target,
                        'req_type': req_type, 'access_queue': entry,
                    }
                )
            except Exception:
                entries = IOQueue.objects.filter(
                    storage_object=storage_object, req_type__in=[20, 25],
                    ip=entry.ip, status__in=[0, 2, 5]
                )

                if entries.count > 1:
                    io_entry = entries.first()
                else:
                    entry.status = 100
                    entry.save(update_fields=['status'])
                    raise

            entry.status = 5
            entry.save(update_fields=['status'])

            return str(io_entry.pk)

    def undo(self):
        pass

    def event_outcome_success(self):
        pass



class PollIOQueue(DBTask):
    track = False
    def get_storage_medium(self, entry, storage_target, storage_type):
        if entry.req_type in [20, 25]:
            return entry.storage_object.storage_medium

        storage_medium = storage_target.storagemedium_set.filter(
            status=20, location_status=50
        ).order_by('last_changed_local').first()

        if storage_type == TAPE:
            if storage_medium is not None:
                new_size = storage_medium.used_capacity + entry.write_size

                if storage_target.max_capacity > 0 and new_size > storage_target.max_capacity:
                    try:
                        storage_medium.mark_as_full()
                    except AssertionError:
                        pass

                    storage_medium = None
                else:
                    return storage_medium

            # Could not find any storage medium, create one

            slot = TapeSlot.objects.filter(
                status=20, storage_medium__isnull=True,
                medium_id__startswith=storage_target.target
            ).exclude(medium_id__exact='').first()

            if slot is None:
                raise ValueError("No tape available for allocation")

            storage_medium = StorageMedium.objects.create(
                medium_id=slot.medium_id,
                storage_target=storage_target, status=20,
                location=Parameter.objects.get(entity='medium_location').value,
                location_status=50,
                block_size=storage_target.default_block_size,
                format=storage_target.default_format, agent=entry.user,
                tape_slot=slot,
            )

            return storage_medium

        elif storage_type == DISK:
            if storage_medium is None:
                return StorageMedium.objects.create(
                    medium_id=storage_target.name,
                    storage_target=storage_target, status=20,
                    location=Parameter.objects.get(entity='medium_location').value,
                    location_status=50,
                    block_size=storage_target.default_block_size,
                    format=storage_target.default_format, agent=entry.user,
                )

            return storage_medium


    def cleanup(self):
        entries = IOQueue.objects.filter(status=5, storage_method_target__storage_target__remote_server='').exclude(task_id='')

        for entry in entries.iterator():
            result = AsyncResult(entry.task_id)

            if result.ready() and (result.failed() or result.successful()):
                entry.status = 20 if result.successful() else 100
                entry.save(update_fields=['status'])

                if entry.remote_io:
                    data = IOQueueSerializer(entry, context={'request': None}).data
                    entry.sync_with_master(data)

                continue

            task = ProcessTask.objects.filter(pk=entry.task_id).first()

            if task is not None and task.status in [celery_states.SUCCESS, celery_states.FAILURE]:
                entry.status = 20 if task.status == celery_states.SUCCESS else 100
                entry.save(update_fields=['status'])

                if entry.remote_io:
                    data = IOQueueSerializer(entry, context={'request': None}).data
                    entry.sync_with_master(data)

                continue

            if result.status == 'PENDING':
                if task is not None and task.status == celery_states.PENDING:
                    task.run()

    def mark_as_complete(self):
        ips = InformationPackage.objects.filter(state='Preserving').prefetch_related('policy__storage_methods')

        for ip in ips.iterator():
            entries = ip.ioqueue_set.filter(req_type__in=[10, 15])

            if not entries.exists() or entries.exclude(status=20).exists():
                continue  # unfinished IO entry exists for IP, skip

            for storage_method in ip.policy.storage_methods.secure_storage().filter(status=True).iterator():
                if not entries.filter(storage_method_target__storage_method=storage_method).exists():
                    raise Exception("No entry for storage method '%s' for IP '%s'" % (storage_method.pk, ip.pk))

            ip.archived = True
            ip.state = 'Preserved'
            ip.save(update_fields=['archived', 'state'])

            # if we preserved directly from workarea then we need to delete that workarea object
            ip.workareas.all().delete()

            msg = '%s preserved to %s' % (ip.object_identifier_value, ', '.join(ip.storage.all().values_list('storage_medium__medium_id', flat=True)))
            agent = entries.first().user.username
            extra = {'event_type': 30300, 'object': ip.pk, 'agent': agent, 'outcome': EventIP.SUCCESS}
            logger.info(msg, extra=extra)
            Notification.objects.create(message="%s is now preserved" % ip.object_identifier_value, level=logging.INFO, user=entries.first().user, refresh=True)

            recipient = entries.first().user.email
            if recipient:
                subject = 'Preserved "%s"' % ip.object_identifier_value
                body = '"%s" is now preserved' % ip.object_identifier_value
                try:
                    send_mail(subject, body, 'e-archive@essarch.org', [recipient], fail_silently=False)
                except Exception:
                    logger.exception("Failed to send mail to notify user about preserved IP")

    def is_cached(self, entry):
        cache_dir = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache_dir, entry.ip.object_identifier_value)
        cache_tar_obj = cache_obj + '.tar'
        in_cache = os.path.exists(cache_tar_obj)

        InformationPackage.objects.filter(pk=entry.ip_id).update(cached=in_cache)
        return in_cache

    def transfer_to_master(self, entry):
        master_server = entry.storage_method_target.storage_target.master_server
        host, user, passw = master_server.split(',')
        dst = urllib.parse.urljoin(host, 'api/io-queue/%s/add-file/' % entry.pk)

        session = requests.Session()
        session.verify = False
        session.auth = (user, passw)

        cache_dir = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache_dir, entry.ip.object_identifier_value)
        cache_tar_obj = cache_obj + '.tar'

        copy_file(cache_tar_obj, dst, session)

        dst = urllib.parse.urljoin(host, 'api/io-queue/%s/all-files-done/' % entry.pk)
        response = session.post(dst)
        response.raise_for_status()

    def run(self):
        self.mark_as_complete()
        self.cleanup()

        entries = IOQueue.objects.filter(
            status__in=[0, 2]
        ).select_related('storage_method_target').order_by('ip__policy', 'ip', 'posted')[:5]

        if not len(entries):
            raise Ignore()

        for entry in entries:
            entry.status = 2
            entry.save(update_fields=['status'])

            if entry.req_type in [20, 25]:  # read
                if entry.storage_object is None:
                    entry.status = 100
                    entry.save(update_fields=['status'])
                    raise ValueError("Storage Object needed to read from storage")

                storage_object = entry.storage_object


                if self.is_cached(entry):
                    try:
                        if entry.remote_io:
                            self.transfer_to_master(entry)

                        entry.status = 20
                        entry.save(update_fields=['status'])

                        if entry.remote_io:
                            data = IOQueueSerializer(entry, context={'request': None}).data
                            entry.sync_with_master(data)

                        return
                    except:
                        # failed to copy from cache, get from storage instead
                        pass

            storage_method = entry.storage_method_target.storage_method
            storage_target = entry.storage_method_target.storage_target

            if storage_target.remote_server:
                entry.status = 2
                entry.save(update_fields=['status'])

                host, user, passw = storage_target.remote_server.split(',')
                dst = urllib.parse.urljoin(host, 'api/io-queue/')
                session = requests.Session()
                session.verify = False
                session.auth = (user, passw)

                data = IOQueueSerializer(entry, context={'request': None}).data

                methods_to_keep = []

                target_id = str(storage_target.pk)

                for method in data['ip']['policy']['storage_methods']:
                    if target_id in method['targets']:
                        method['targets'] = [target_id]

                        for relation in method['storage_method_target_relations']:
                            if relation['storage_target']['id'] == target_id:
                                relation['storage_target'].pop('remote_server')
                                break

                        method['storage_method_target_relations'] = [relation]
                        methods_to_keep.append(method)

                data.pop('access_queue', None)
                data['ip'].pop('cached', None)
                data['ip']['policy']['storage_methods'] = methods_to_keep

                try:
                    response = session.post(dst, json=data)
                    response.raise_for_status()
                except:
                    entry.status = 100
                    raise
                else:
                    entry.status = 5
                finally:
                    entry.save(update_fields=['status'])

                dst = urllib.parse.urljoin(host, 'api/io-queue/%s/add-file/' % entry.pk)

                # copy files if write request and not already copied
                if entry.req_type in [10, 15] and entry.remote_status != 20:
                    try:
                        entry.remote_status = 5
                        entry.save(update_fields=['remote_status'])

                        t = ProcessTask.objects.create(
                            name='ESSArch_Core.tasks.CopyFile',
                            args=[os.path.join(entry.ip.policy.cache_storage.value, entry.ip.object_identifier_value) + '.tar', dst],
                            params={'requests_session': session},
                            information_package=entry.ip,
                            eager=False,
                        )

                        entry.transfer_task_id = str(t.pk)
                        entry.save(update_fields=['transfer_task_id'])

                        t.run().get()

                        dst = urllib.parse.urljoin(host, 'api/io-queue/%s/all-files-done/' % entry.pk)
                        response = session.post(dst)
                        response.raise_for_status()
                    except:
                        entry.status = 100
                        entry.remote_status = 100
                        entry.save(update_fields=['status', 'remote_status'])
                        raise
                    else:
                        entry.remote_status = 20
                        entry.save(update_fields=['remote_status'])

                return

            try:
                storage_medium = self.get_storage_medium(entry, storage_target, storage_method.type)
                entry.storage_medium = storage_medium
                entry.save(update_fields=['storage_medium'])
            except ValueError:
                entry.status = 100
                entry.save(update_fields=['status'])

                if entry.remote_io:
                    data = IOQueueSerializer(entry, context={'request': None}).data
                    entry.sync_with_master(data)
                raise

            if storage_method.type == TAPE and storage_medium.tape_drive is None:  # Tape not mounted, queue to mount it
                RobotQueue.objects.get_or_create(
                    storage_medium=storage_medium, req_type=10,
                    status__in=[0, 2, 5], defaults={
                        'user': entry.user, 'status': 0,
                        'io_queue_entry': entry
                    }
                )
                continue

            if entry.req_type in [10, 20]:  # tape
                drive_entry = storage_medium.tape_drive.io_queue_entry
                if drive_entry is not None and drive_entry != entry:
                    raise ValueError('Tape Drive locked')
                else:
                    storage_medium.tape_drive.io_queue_entry = entry
                    storage_medium.tape_drive.save(update_fields=['io_queue_entry'])

                entry.status = 5
                entry.save(update_fields=['status'])
                t = ProcessTask.objects.create(
                    name="workflow.tasks.IOTape",
                    args=[entry.pk, storage_medium.pk],
                    eager=False,
                    information_package=entry.ip,
                )

                if entry.step is not None:
                    entry.step.tasks.add(t)

                entry.task_id = str(t.pk)
                entry.save(update_fields=['task_id'])

                t.run()

            elif entry.req_type in [15, 25]:  # Write to disk
                entry.status = 5
                entry.save(update_fields=['status'])
                t = ProcessTask.objects.create(
                    name="workflow.tasks.IODisk",
                    args=[entry.pk, storage_medium.pk],
                    eager=False,
                    information_package=entry.ip,
                )

                if entry.step is not None:
                    entry.step.tasks.add(t)

                entry.task_id = str(t.pk)
                entry.save(update_fields=['task_id'])

                t.run()

    def undo(self):
        pass

    def event_outcome_success(self):
        pass

class IO(DBTask):
    abstract = True

    def write(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        medium_obj = StorageMedium.objects.get(pk=storage_medium)
        storage_backend = storage_target.get_storage_backend()
        storage_object = storage_backend.write(cache_obj, entry.ip, storage_method, medium_obj)
        storage_backend.write(cache_obj_xml, entry.ip, storage_method, medium_obj, create_obj=False, update_obj=storage_object)
        storage_backend.write(cache_obj_aic_xml, entry.ip, storage_method, medium_obj, create_obj=False, update_obj=storage_object)

        StorageMedium.objects.filter(pk=storage_medium).update(used_capacity=F('used_capacity') + entry.write_size)

        entry.storage_object = storage_object
        entry.save(update_fields=['storage_object'])

        return storage_object

    def read(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        storage_backend = storage_target.get_storage_backend()
        return storage_backend.read(entry.storage_object, cache)

    def io_success(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        pass

    def run(self, io_queue_entry, storage_medium):
        entry = IOQueue.objects.get(pk=io_queue_entry)
        entry.status = 5
        entry.save(update_fields=['status'])

        storage_method = entry.storage_method_target.storage_method
        storage_target = entry.storage_method_target.storage_target

        cache = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache, entry.ip.object_identifier_value) + '.tar'
        cache_obj_xml = os.path.join(cache, entry.ip.object_identifier_value) + '.xml'
        cache_obj_aic_xml = os.path.join(cache, str(entry.ip.aic_id)) + '.xml'

        try:
            if entry.req_type in self.write_types:
                self.write(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)
            elif entry.req_type in self.read_types:
                self.read(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

                with tarfile.open(cache_obj) as tar:
                    tar.extractall(cache.encode('utf-8'))

                entry.ip.cached = True
                entry.ip.save(update_fields=['cached'])

                if entry.remote_io:
                    master_server = entry.storage_method_target.storage_target.master_server
                    host, user, passw = master_server.split(',')
                    dst = urllib.parse.urljoin(host, 'api/io-queue/%s/add-file/' % entry.pk)

                    session = requests.Session()
                    session.verify = False
                    session.auth = (user, passw)

                    copy_file(cache_obj, dst, requests_session=session)

                    dst = urllib.parse.urljoin(host, 'api/io-queue/%s/all-files-done/' % entry.pk)
                    response = session.post(dst)
                    response.raise_for_status()
            else:
                raise ValueError('Invalid request type')
        except:
            entry.status = 100
            raise
        else:
            entry.status = 20
        finally:
            entry.save(update_fields=['status'])

            if entry.remote_io:
                data = IOQueueSerializer(entry, context={'request': None}).data
                entry.sync_with_master(data)

            self.io_success(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class IOTape(IO):
    queue = 'io_tape'
    storage_type = 'tape'
    write_types = (10,)
    read_types = (20,)

    def write(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        super(IOTape, self).write(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

        msg = 'IP written to %s' % entry.storage_medium.medium_id
        agent = entry.user.username
        extra = {'event_type': 40700, 'object': entry.ip.pk, 'agent': agent, 'task': self.task_id, 'outcome': EventIP.SUCCESS}
        logger.info(msg, extra=extra)

    def read(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        super(IOTape, self).read(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

        msg = 'IP read from %s' % entry.storage_medium.medium_id
        agent = entry.user.username
        extra = {'event_type': 40710, 'object': entry.ip.pk, 'agent': agent, 'task': self.task_id, 'outcome': EventIP.SUCCESS}
        logger.info(msg, extra=extra)

    def io_success(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        drive = StorageMedium.objects.get(pk=storage_medium).tape_drive
        drive.io_queue_entry = None
        drive.save(update_fields=['io_queue_entry'])


class IODisk(IO):
    queue = 'io_disk'
    storage_type = 'disk'
    write_types = (15,)
    read_types = (25,)

    def write(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        super(IODisk, self).write(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

        msg = 'IP written to %s' % entry.storage_medium.medium_id
        agent = entry.user.username
        extra = {'event_type': 40600, 'object': entry.ip.pk, 'agent': agent, 'task': self.task_id, 'outcome': EventIP.SUCCESS}
        logger.info(msg, extra=extra)

    def read(self, entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target):
        super(IODisk, self).read(entry, cache, cache_obj, cache_obj_xml, cache_obj_aic_xml, storage_medium, storage_method, storage_target)

        msg = 'IP read from %s' % entry.storage_medium.medium_id
        agent = entry.user.username
        extra = {'event_type': 40610, 'object': entry.ip.pk, 'agent': agent, 'task': self.task_id, 'outcome': EventIP.SUCCESS}
        logger.info(msg, extra=extra)


class PollRobotQueue(DBTask):
    track = False
    def run(self):
        force_entries = RobotQueue.objects.filter(
            req_type=30, status__in=[0, 2]
        ).select_related('storage_medium').order_by('-status', 'posted')

        non_force_entries = RobotQueue.objects.filter(
            status__in=[0, 2]
        ).exclude(req_type=30).select_related('storage_medium').order_by('-status', '-req_type', 'posted')[:5]

        entries = list(force_entries) + list(non_force_entries)

        if not len(entries):
            raise Ignore()

        for entry in entries:
            entry.status = 2
            entry.save(update_fields=['status'])

            medium = entry.storage_medium

            if entry.req_type == 10:  # mount
                if medium.tape_drive is not None:  # already mounted
                    if hasattr(entry, 'io_queue_entry'):  # mounting for read or write
                        if medium.tape_drive.io_queue_entry != entry.io_queue_entry:
                            raise TapeMountedAndLockedByOtherError("Tape already mounted and locked by '%s'" % medium.tape_drive.io_queue_entry)

                        entry.status = 20
                        entry.save(update_fields=['status'])

                    raise TapeMountedError("Tape already mounted")

                drive = entry.tape_drive

                if drive is None:
                    free_drive = TapeDrive.objects.filter(
                        status=20, storage_medium__isnull=True, io_queue_entry__isnull=True, locked=False,
                    ).order_by('num_of_mounts').first()

                    if free_drive is None:
                        raise ValueError('No tape drive available')

                    drive = free_drive

                free_robot = Robot.objects.filter(robot_queue__isnull=True).first()

                if free_robot is None:
                    raise ValueError('No robot available')

                entry.robot = free_robot
                entry.status = 5
                entry.save(update_fields=['robot', 'status'])

                with allow_join_result():

                    try:
                        ProcessTask.objects.create(
                            name="ESSArch_Core.tasks.MountTape",
                            params={
                                'medium': medium.pk,
                                'drive': drive.pk,
                            }
                        ).run().get()
                    except TapeMountedError:
                        entry.status = 20
                        raise
                    except:
                        entry.status = 100
                        raise
                    else:
                        medium.tape_drive = drive
                        medium.save(update_fields=['tape_drive'])
                        entry.status = 20
                    finally:
                        entry.robot = None
                        entry.save(update_fields=['robot', 'status'])

            elif entry.req_type in [20, 30]:  # unmount
                if medium.tape_drive is None:  # already unmounted
                    entry.status = 20
                    entry.save(update_fields=['status'])

                    raise TapeUnmountedError("Tape already unmounted")

                if medium.tape_drive.locked:
                    if entry.req_type == 20:
                        raise TapeDriveLockedError("Tape locked")

                free_robot = Robot.objects.filter(robot_queue__isnull=True).first()

                if free_robot is None:
                    raise ValueError('No robot available')

                entry.robot = free_robot
                entry.status = 5
                entry.save(update_fields=['robot', 'status'])

                with allow_join_result():
                    try:
                        ProcessTask.objects.create(
                            name="ESSArch_Core.tasks.UnmountTape",
                            params={
                                'drive': medium.tape_drive.pk,
                            }
                        ).run().get()
                    except TapeUnmountedError:
                        entry.status = 20
                        raise
                    except:
                        entry.status = 100
                        raise
                    else:
                        medium.tape_drive = None
                        medium.save(update_fields=['tape_drive'])
                        entry.status = 20
                    finally:
                        entry.robot = None
                        entry.save(update_fields=['robot', 'status'])


    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class UnmountIdleDrives(DBTask):
    track = False
    def run(self):
        idle_drives = TapeDrive.objects.filter(
            status=20, storage_medium__isnull=False,
            last_change__lte=timezone.now()-F('idle_time'),
            locked=False,
        )

        if not idle_drives.exists():
            raise Ignore()

        for drive in idle_drives.iterator():
            if not RobotQueue.objects.filter(storage_medium=drive.storage_medium, req_type=20, status__in=[0, 2]).exists():
                RobotQueue.objects.create(
                    user=User.objects.get(username='system'),
                    storage_medium=drive.storage_medium,
                    req_type=20, status=0,
                )

    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class ScheduleAppraisalJobs(DBTask):
    track = False

    def run(self):
        now = timezone.now()

        # get rules without future jobs scheduled
        rules = AppraisalRule.objects.filter(
            information_packages__isnull=False, information_packages__active=True,
            information_packages__appraisal_date__lte=now
        ).exclude(jobs__start_date__gte=now)

        for rule in rules.iterator():
            cron_entry = CronTab(rule.frequency)

            try:
                latest_job = rule.jobs.latest()
                delay = cron_entry.next(timezone.localtime(latest_job.start_date))
                last = latest_job.start_date
            except AppraisalJob.DoesNotExist:
                # no job has been created yet
                delay = cron_entry.next(timezone.localtime(now))
                last = now

            next_date = last + datetime.timedelta(seconds=delay)
            AppraisalJob.objects.create(rule=rule, start_date=next_date)


    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class PollAppraisalJobs(DBTask):
    track = False

    def run(self):
        now = timezone.now()
        jobs = AppraisalJob.objects.select_related('rule').filter(status=celery_states.PENDING, start_date__lte=now)

        for job in jobs.iterator():
            job.run()

    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class ScheduleConversionJobs(DBTask):
    track = False

    def run(self):
        now = timezone.now()

        # get rules without future jobs scheduled
        rules = ConversionRule.objects.filter(
            information_packages__isnull=False, information_packages__active=True,
        ).exclude(jobs__start_date__gte=now)

        for rule in rules.iterator():
            cron_entry = CronTab(rule.frequency)

            try:
                latest_job = rule.jobs.latest()
                delay = cron_entry.next(timezone.localtime(latest_job.start_date))
                last = latest_job.start_date
            except ConversionJob.DoesNotExist:
                # no job has been created yet
                delay = cron_entry.next(timezone.localtime(now))
                last = now

            next_date = last + datetime.timedelta(seconds=delay)
            ConversionJob.objects.create(rule=rule, start_date=next_date)


    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class PollConversionJobs(DBTask):
    track = False

    def run(self):
        now = timezone.now()
        jobs = ConversionJob.objects.select_related('rule').filter(status=celery_states.PENDING, start_date__lte=now)

        for job in jobs.iterator():
            job.run()

    def undo(self):
        pass

    def event_outcome_success(self):
        pass
