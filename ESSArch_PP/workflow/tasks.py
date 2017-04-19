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

import errno
import os
import shutil
import tarfile
import zipfile

from celery.result import allow_join_result

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import IntegerField
from django.db.models.functions import Cast

from scandir import walk

from ESSArch_Core import tasks
from ESSArch_Core.configuration.models import ArchivePolicy, Path, Parameter
from ESSArch_Core.essxml.util import parse_submit_description
from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalLocation,
    ArchivalType,
    InformationPackage,
)
from ESSArch_Core.storage.models import (
    DISK,
    TAPE,

    IOQueue,

    Robot,
    RobotQueue,
    TapeDrive,
    TapeSlot,

    StorageMedium,
    StorageMethod,
    StorageObject,
)
from ESSArch_Core.WorkflowEngine.dbtask import DBTask
from ESSArch_Core.WorkflowEngine.models import ProcessTask, ProcessStep

from storage.exceptions import (
    TapeMountedError,
    TapeMountedAndLockedByOtherError,
)


class ReceiveSIP(DBTask):
    event_type = 20100

    def run(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False, tags=[]):
        policy = ArchivePolicy.objects.get(pk=archive_policy)
        ingest = policy.ingest_path
        objid, container_type = os.path.splitext(os.path.basename(container))

        parsed = parse_submit_description(xml, srcdir=os.path.split(container)[0])

        information_class = parsed.get('information_class', policy.information_class)

        if information_class != policy.information_class:
            raise ValueError('Information class of IP and policy does not match')

        aic = InformationPackage.objects.create(
            package_type=InformationPackage.AIC
        )

        aip = InformationPackage.objects.create(
            ObjectIdentifierValue=objid,
            policy=policy,
            package_type=InformationPackage.AIP,
            Label=parsed.get('label'),
            State='Receiving',
            entry_date=parsed.get('create_date'),
            aic=aic,
            Responsible_id=self.responsible,
            Startdate=parsed['altrecordids'].get('STARTDATE'),
            Enddate=parsed['altrecordids'].get('ENDDATE'),
            information_class=information_class,
        )

        archival_institution = parsed.get('archival_institution')
        archivist_organization = parsed.get('archivist_organization')
        archival_type = parsed.get('archival_type')
        archival_location = parsed.get('archival_location')

        if archival_institution:
            arch, _ = ArchivalInstitution.objects.get_or_create(
                name=archival_institution
            )
            aip.ArchivalInstitution = arch

        if archivist_organization:
            arch, _ = ArchivistOrganization.objects.get_or_create(
                name=archivist_organization
            )
            aip.ArchivistOrganization = arch

        if archival_type:
            arch, _ = ArchivalType.objects.get_or_create(
                name=archival_type
            )
            aip.ArchivalType = arch

        if archival_location:
            arch, _ = ArchivalLocation.objects.get_or_create(
                name=archival_location
            )
            aip.ArchivalLocation = arch

        aip.save(update_fields=[
            'ArchivalInstitution', 'ArchivistOrganization', 'ArchivalType',
            'ArchivalLocation',
        ])

        aip.tags = tags

        ProcessTask.objects.filter(pk=self.request.id).update(
            information_package=aip
        )

        ProcessStep.objects.filter(pk=self.step).update(
            information_package=aip
        )

        aip_dir = os.path.join(ingest.value, aip.ObjectIdentifierValue)
        os.makedirs(aip_dir)

        content = os.path.join(aip_dir, 'content')
        metadata = os.path.join(aip_dir, 'metadata')

        os.mkdir(content)
        os.mkdir(metadata)

        if policy.receive_extract_sip:
            dst = os.path.join(content, objid)
            os.mkdir(dst)

            if container_type.lower() == '.tar':
                with tarfile.open(container) as tar:
                    tar.extractall(dst)
            elif container_type.lower() == '.zip':
                with zipfile.ZipFile(container) as zipf:
                    zipf.extractall(dst)
        else:
            dst = os.path.join(aip_dir, 'content', objid + container_type)
            shutil.copy(container, dst)

        self.set_progress(100, total=100)
        return aip.pk

    def undo(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False, tags=None):
        pass

    def event_outcome_success(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False, tags=None):
        ip_id = os.path.splitext(os.path.basename(xml))[0]
        return "Received IP '%s'" % ip_id


class CacheAIP(DBTask):
    event_type = 20200

    def run(self, aip):
        srcdir, dstdir, objid = InformationPackage.objects.values_list(
            'policy__ingest_path__value', 'policy__cache_storage__value',
            'ObjectIdentifierValue',
        ).get(pk=aip)

        srcdir = os.path.join(srcdir, objid)
        dstdir = os.path.join(dstdir, objid)
        dsttar = dstdir + '.tar'

        try:
            os.makedirs(dstdir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with tarfile.open(dsttar, 'w') as tar:
            for root, dirs, files in walk(srcdir):
                for d in dirs:
                    try:
                        os.makedirs(os.path.join(dstdir, d))
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise

                for f in files:
                    rel = os.path.relpath(root, srcdir)
                    src = os.path.join(root, f)
                    dst = os.path.join(dstdir, rel, f)

                    shutil.copy2(src, dst)
                    tar.add(src, os.path.join(objid, rel, f))

        InformationPackage.objects.filter(pk=aip).update(
            ObjectPath=dsttar,
        )

        self.set_progress(100, total=100)
        return aip

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Cached AIP '%s'" % aip


class UpdateIPStatus(tasks.UpdateIPStatus):
    event_type = 30280


class StoreAIP(DBTask):
    event_type = 20300

    def run(self, aip):
        policy = InformationPackage.objects.prefetch_related('policy__storagemethod_set__targets').get(pk=aip).policy

        if not policy:
            raise ArchivePolicy.DoesNotExist("No policy found in IP: '%s'" % aip)

        storage_methods = policy.storagemethod_set.all()

        if not storage_methods.exists():
            raise StorageMethod.DoesNotExist("No storage methods found in policy: '%s'" % policy)

        for method in storage_methods:
            for method_target in method.storagemethodtargetrelation_set.all():
                req_type = 10 if method_target.storage_method.type == TAPE else 15

                started = IOQueue.objects.filter(
                    storage_method_target=method_target, req_type=req_type,
                    ip_id=aip, status__in=[0, 2, 5],
                )

                if not started.exists():
                    IOQueue.objects.create(
                        req_type=req_type, user_id=self.responsible, status=0,
                        ip_id=aip, storage_method_target=method_target,
                    )

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Created entries in IO queue for AIP '%s'" % aip


class PollIOQueue(DBTask):
    def get_storage_medium(self, entry, storage_target, storage_type):
        if storage_type == TAPE:
            if entry.req_type == 10:
                storage_medium = storage_target.storagemedium_set.filter(
                    status=20,
                ).order_by('last_changed_local').first()

                if storage_medium is None:
                    slot = TapeSlot.objects.filter(
                        storage_medium__isnull=True,
                        medium_id__startswith=storage_target.target
                    ).exclude(medium_id__exact='').first()

                    if slot is None:
                        raise ValueError("No tape available for allocation")

                    storage_medium = StorageMedium.objects.create(
                        medium_id=storage_target.name,
                        storage_target=storage_target, status=20,
                        location_status=20,
                        block_size=storage_target.default_block_size,
                        format=storage_target.default_format, agent=entry.user,
                        tape_slot=slot,
                    )

                return storage_medium
            elif entry.req_type == 20:
                return entry.storage_object.storage_medium

        elif storage_type == DISK:
            if entry.req_type == 15:
                storage_medium = storage_target.storagemedium_set.filter(
                    status=20,
                ).order_by('last_changed_local').first()

                if storage_medium is None:
                    storage_medium = StorageMedium.objects.create(
                        medium_id=storage_target.name,
                        storage_target=storage_target, status=20,
                        location=Parameter.objects.get(entity='medium_location').value,
                        location_status=50,
                        block_size=storage_target.default_block_size,
                        format=storage_target.default_format, agent=entry.user,
                    )
                return storage_target.storagemedium_set.first()
            elif entry.req_type == 25:
                return entry.storage_object.storage_medium

    def run(self):
        try:
            entry = IOQueue.objects.filter(status=0).select_related('storage_method_target').earliest()
        except IOQueue.DoesNotExist:
            return

        if entry.req_type in [20, 25]:  # read
            if entry.storage_object is None:
                entry.status = 100
                entry.save(update_fields=['status'])
                raise ValueError("Storage Object needed to read tape")

            storage_object = entry.storage_object

        storage_method = entry.storage_method_target.storage_method
        storage_target = entry.storage_method_target.storage_target

        try:
            storage_medium = self.get_storage_medium(entry, storage_target, storage_method.type)
        except ValueError:
            entry.status = 100
            entry.save(update_fields=['status'])
            raise

        if storage_method.type == TAPE and storage_medium.tape_drive is None:  # Tape not mounted, queue to mount it
            started = RobotQueue.objects.filter(
                storage_medium=storage_medium, req_type=10,
                status__in=[0, 2, 5],
            )

            if not started.exists():  # add to queue if not already in queue
                RobotQueue.objects.create(
                    user=entry.user,
                    storage_medium=storage_medium,
                    req_type=10, io_queue_entry=entry
                )
            return

        with allow_join_result():
            try:
                if entry.req_type == 10:  # Write to tape
                    last_written_obj = StorageObject.objects.filter(
                        storage_medium=storage_medium
                    ).annotate(
                        content_location_value_int=Cast('content_location_value', IntegerField())
                    ).order_by('content_location_value_int').only('content_location_value').last()

                    if last_written_obj is None:
                        content_location_value = '1'
                    else:
                        content_location_value = str(last_written_obj.content_location_value_int + 1)

                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.SetTapeFileNumber",
                        params={
                            'medium': storage_medium.pk,
                            'num': int(content_location_value),
                        }
                    ).run().get()

                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.WriteToTape",
                        params={
                            'medium': storage_medium.pk,
                            'path': entry.object_path,
                        }
                    ).run().get()

                    StorageObject.objects.create(
                        content_location_type=storage_method.type,
                        content_location_value=content_location_value,
                        ip=entry.ip, storage_medium=storage_medium
                    )
                elif entry.req_type == 20:  # Read from tape
                    tape_pos = int(storage_object.content_location_value)

                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.SetTapeFileNumber",
                        params={
                            'medium': storage_medium.pk,
                            'num': tape_pos,
                        }
                    ).run().get()

                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.ReadTape",
                        params={
                            'medium': storage_medium.pk,
                            'path': entry.object_path
                        }
                    ).run().get()
                elif entry.req_type == 15:  # Write to disk
                    storage_object = StorageObject.objects.create(
                        content_location_type=storage_method.type,
                        content_location_value=storage_target.target,
                        ip=entry.ip, storage_medium=storage_medium
                    )
                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.CopyFile",
                        params={
                            'src': entry.ip.ObjectPath,
                            'dst': storage_target.target,
                        }
                    ).run().get()

                elif entry.req_type == 25:  # Read from disk
                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.CopyFile",
                        params={
                            'src': storage_object.content_location_value,
                            'dst': entry.object_path,
                        }
                    ).run().get()
            except:
                entry.status = 100
                raise
            else:
                entry.status = 20
            finally:
                entry.save(update_fields=['status'])

    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class PollRobotQueue(DBTask):
    def run(self):
        try:
            entry = RobotQueue.objects.filter(
                status=0
            ).select_related('storage_medium').earliest()
        except RobotQueue.DoesNotExist:
            return

        free_robot = Robot.objects.filter(robot_queue__isnull=True).first()

        if free_robot is None:
            raise ValueError('No robot available')

        entry.robot = free_robot
        entry.status = 2
        entry.save(update_fields=['robot', 'status'])

        if entry.req_type == 10:  # mount
            medium = entry.storage_medium

            if medium.tape_drive is not None:  # already mounted
                if hasattr(entry, 'io_queue_entry'):  # mounting for read or write
                    if medium.tape_drive.io_queue_entry != entry.io_queue_entry:
                        entry.robot = None
                        entry.status = 0
                        entry.save(update_fields=['robot', 'status'])
                        raise TapeMountedAndLockedByOtherError("Tape already mounted and locked by '%s'" % medium.tape_drive.io_queue_entry)

                    if medium.tape_drive.io_queue_entry is None:
                        medium.tape_drive.io_queue_entry = entry.io_queue_entry
                        medium.tape_drive.save(update_fields=['io_queue_entry'])

                    entry.status = 20
                    entry.robot = None
                    entry.save(update_fields=['status', 'robot'])

                raise TapeMountedError("Tape already mounted")

            free_drive = TapeDrive.objects.filter(
                storage_medium__isnull=True, io_queue_entry__isnull=True
            ).order_by('num_of_mounts').first()

            if free_drive is None:
                raise ValueError('No tape drive available')

            free_drive.io_queue_entry = entry.io_queue_entry
            free_drive.save(update_fields=['io_queue_entry'])

            with allow_join_result():
                try:
                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.MountTape",
                        params={
                            'medium': medium.pk,
                            'drive': free_drive.pk,
                        }
                    ).run().get()
                except:
                    entry.status = 100
                    raise
                else:
                    medium.tape_drive = free_drive
                    medium.save()
                    entry.robot = None
                    entry.status = 20
                finally:
                    entry.save(update_fields=['robot', 'status'])


    def undo(self):
        pass

    def event_outcome_success(self):
        pass

