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
import time
import zipfile

from celery import states as celery_states
from celery.exceptions import Ignore
from celery.result import allow_join_result, AsyncResult

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, IntegerField, Max
from django.db.models.functions import Cast
from django.utils import timezone

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
    Workarea,
)
from ESSArch_Core.storage.exceptions import (
    TapeDriveLockedError,
    TapeMountedError,
    TapeMountedAndLockedByOtherError,
    TapeUnmountedError,
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
    StorageMethodTargetRelation,
    StorageObject,
)
from ESSArch_Core.WorkflowEngine.dbtask import DBTask
from ESSArch_Core.WorkflowEngine.models import ProcessTask, ProcessStep


class ReceiveSIP(DBTask):
    event_type = 30100

    def run(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=[]):
        aip = InformationPackage.objects.get(pk=ip)
        policy = ArchivePolicy.objects.get(pk=policy)
        ingest = policy.ingest_path
        objid, container_type = os.path.splitext(os.path.basename(container))

        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip.aic = aic

        parsed = parse_submit_description(xml, srcdir=os.path.split(container)[0])

        archival_institution = parsed.get('archival_institution')
        archivist_organization = parsed.get('archivist_organization')
        archival_type = parsed.get('archival_type')
        archival_location = parsed.get('archival_location')

        if archival_institution:
            arch, _ = ArchivalInstitution.objects.get_or_create(
                name=archival_institution['name']
            )
            aip.archival_institution = arch

        if archivist_organization:
            arch, _ = ArchivistOrganization.objects.get_or_create(
                name=archivist_organization['name']
            )
            aip.archivist_organization = arch

        if archival_type:
            arch, _ = ArchivalType.objects.get_or_create(
                name=archival_type['name']
            )
            aip.archival_type = arch

        if archival_location:
            arch, _ = ArchivalLocation.objects.get_or_create(
                name=archival_location['name']
            )
            aip.archival_location = arch

        aip.tags = tags

        aip_dir = os.path.join(ingest.value, aip.object_identifier_value)
        os.makedirs(aip_dir)

        content = os.path.join(aip_dir, 'content')
        metadata = os.path.join(aip_dir, 'metadata')

        os.mkdir(content)
        os.mkdir(metadata)

        if policy.receive_extract_sip:
            dst = content

            if container_type.lower() == '.tar':
                with tarfile.open(container) as tar:
                    tar.extractall(dst.encode('utf-8'))
            elif container_type.lower() == '.zip':
                with zipfile.ZipFile(container) as zipf:
                    zipf.extractall(dst.encode('utf-8'))
        else:
            dst = os.path.join(aip_dir, 'content', objid + container_type)
            shutil.copy(container, dst)

        aip.object_path = aip_dir

        aip.save(update_fields=[
            'aic', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'object_path',
        ])

        return ip

    def undo(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=None):
        pass

    def event_outcome_success(self, ip, xml, container, policy, purpose=None, allow_unknown_files=False, tags=None):
        return "Received IP '%s'" % str(ip)


class CacheAIP(DBTask):
    event_type = 20200

    def run(self, aip):
        aip_obj = InformationPackage.objects.prefetch_related('policy').get(pk=aip)
        policy = aip_obj.policy
        srcdir = aip_obj.object_path
        objid = aip_obj.object_identifier_value

        dstdir = os.path.join(policy.cache_storage.value, objid)
        dsttar = dstdir + '.tar'

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

                    shutil.copy2(src, dst)
                    tar.add(src, os.path.normpath(os.path.join(objid, rel, f)))

        checksum = ProcessTask.objects.create(
            name='ESSArch_Core.tasks.CalculateChecksum',
            params={
                'filename': dsttar,
                'algorithm': policy.get_checksum_algorithm_display(),
            },
            information_package_id=aip,
            responsible_id=self.responsible,
        ).run().get()

        InformationPackage.objects.filter(pk=aip).update(
            message_digest=checksum, message_digest_algorithm=policy.checksum_algorithm,
            cached=True
        )
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
        policy = InformationPackage.objects.prefetch_related('policy__storage_methods__targets').get(pk=aip).policy

        if not policy:
            raise ArchivePolicy.DoesNotExist("No policy found in IP: '%s'" % aip)

        storage_methods = policy.storage_methods.all()

        if not storage_methods.exists():
            raise StorageMethod.DoesNotExist("No storage methods found in policy: '%s'" % policy)

        size, count = ProcessTask.objects.create(
            name='ESSArch_Core.tasks.UpdateIPSizeAndCount',
            params={'ip': aip},
            information_package_id=aip,
            responsible_id=self.responsible,
        ).run().get()

        with transaction.atomic():
            for method in storage_methods:
                for method_target in method.storage_method_target_relations.filter(status=1):
                    req_type = 10 if method_target.storage_method.type == TAPE else 15

                    _, created = IOQueue.objects.get_or_create(
                        storage_method_target=method_target, req_type=req_type,
                        ip_id=aip, status__in=[0, 2, 5],
                        defaults={'user_id': self.responsible, 'status': 0, 'write_size': size}
                    )

                    if created:
                        InformationPackage.objects.filter(pk=aip).update(state='Preserving')

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Created entries in IO queue for AIP '%s'" % aip


class AccessAIP(DBTask):
    def run(self, aip, tar=True, extracted=False, new=False, object_identifier_value=None):
        aip = InformationPackage.objects.get(pk=aip)

        if new:
            old_aip = aip.pk
            new_aip = aip
            new_aip.pk = None
            new_aip.object_identifier_value = None
            new_aip.state = 'Access Workarea'
            new_aip.cached = False
            new_aip.archived = False

            max_generation = InformationPackage.objects.filter(aic=aip.aic).aggregate(Max('generation'))['generation__max']
            new_aip.generation = max_generation + 1
            new_aip.save()

            new_aip.object_identifier_value = object_identifier_value if object_identifier_value else str(new_aip.pk)
            new_aip.save(update_fields=['object_identifier_value'])

            aip = InformationPackage.objects.get(pk=old_aip)
        else:
            new_aip = aip

        storage_objects = aip.storage

        if not storage_objects.exists():
            raise StorageObject.DoesNotExist("IP %s not archived" % aip)

        dst = Path.objects.get(entity='access').value
        dst = os.path.join(dst, str(self.responsible))

        try:
            os.mkdir(dst)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        cache = Path.objects.get(entity='cache').value
        cache_obj = os.path.join(cache, aip.object_identifier_value)
        cache_tar_obj = cache_obj + '.tar'
        in_cache = os.path.exists(cache_obj)

        if in_cache:
            step = ProcessStep.objects.create(
                name='Copy from cache',
                parent_step_id=self.step,
            )
            with allow_join_result():
                if tar:
                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.CopyFile",
                        params={
                            'src': cache_tar_obj,
                            'dst': os.path.join(dst, new_aip.object_identifier_value + '.tar'),
                        },
                        processstep=step,
                    ).run().get()
                if extracted:
                    for root, dirs, filenames in walk(cache_obj):
                        for fname in filenames:
                            filepath = os.path.join(root, fname)
                            relpath = os.path.relpath(filepath, cache_obj)

                            ProcessTask.objects.create(
                                name="ESSArch_Core.tasks.CopyFile",
                                params={
                                    'src': filepath,
                                    'dst': os.path.join(dst, new_aip.object_identifier_value, relpath),
                                },
                                processstep=step,
                            ).run().get()

            Workarea.objects.create(ip=new_aip, user_id=self.responsible, type=Workarea.ACCESS, read_only=not new)
            return

        storage_objects = storage_objects.filter(
            storage_medium__status__in=[20, 30],
            storage_medium__location_status=50,
        )

        if not storage_objects.exists():
            raise StorageObject.DoesNotExist("IP %s not archived on active medium" % aip)

        on_disk = storage_objects.filter(storage_medium__storage_target__type=DISK).first()

        if on_disk is not None:
            storage_object = on_disk
            req_type = 25
        else:
            on_tape = storage_objects.filter(storage_medium__storage_target__type=TAPE).first()
            if on_tape is not None:
                storage_object = on_tape
                req_type = 20
            else:
                raise StorageObject.DoesNotExist()

        target = storage_object.storage_medium.storage_target
        method_target = StorageMethodTargetRelation.objects.filter(
            storage_target=target, status__in=[1, 2],
        ).first()

        if method_target is None:
            raise StorageMethodTargetRelation.DoesNotExist()

        dst = os.path.join(dst, new_aip.object_identifier_value + '.tar')
        entry, created = IOQueue.objects.get_or_create(
            storage_object=storage_object, req_type=req_type, object_path=dst,
            ip=aip, status__in=[0, 2, 5], defaults={
                'status': 0, 'user_id': self.responsible,
                'storage_method_target': method_target,
                'task_id': self.task_id,
            }
        )

        if not self.eager:
            while entry.status in (0, 2, 5):
                entry.refresh_from_db()
                time.sleep(1)

        tarpath = os.path.join(dst, new_aip.object_identifier_value) + '.tar'

        if extracted:
            with tarfile.open(dst) as tarf:
                tarf.extractall(dst[:-4])

        if not tar:
            os.remove(tarpath)

        Workarea.objects.create(ip=new_aip, user_id=self.responsible, type=Workarea.ACCESS, read_only=not new)
        return

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Created entries in IO queue for AIP '%s'" % aip


class PrepareDIP(DBTask):
    def run(self, label, object_identifier_value=None, orders=[]):
        disseminations = Path.objects.get(entity='disseminations').value

        ip = InformationPackage.objects.create(
            object_identifier_value=object_identifier_value,
            label=label,
            responsible_id=self.responsible,
            state="Prepared",
            package_type=InformationPackage.DIP,
        )

        self.ip = ip.pk
        ip.orders.add(*orders)

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


class PollIOQueue(DBTask):
    track = False
    def get_storage_medium(self, entry, storage_target, storage_type):
        if storage_type == TAPE:
            if entry.req_type == 10:
                storage_medium = storage_target.storagemedium_set.filter(
                    status=20,
                ).order_by('last_changed_local').first()

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

    def cleanup(self):
        entries = IOQueue.objects.filter(status=5).exclude(task_id='')

        for entry in entries.iterator():
            result = AsyncResult(entry.task_id)

            if result.ready() and (result.failed() or result.successful()):
                entry.status = 20 if result.successful() else 100
                entry.save(update_fields=['status'])
                continue

            task = ProcessTask.objects.filter(pk=entry.task_id).first()

            if task is not None and task.status in [celery_states.SUCCESS, celery_states.FAILURE]:
                entry.status = 20 if task.status == celery_states.SUCCESS else 100
                entry.save(update_fields=['status'])
                continue

            if result.status == 'PENDING':
                if task is not None and task.status == celery_states.PENDING:
                    task.run()

    def run(self):
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

            storage_method = entry.storage_method_target.storage_method
            storage_target = entry.storage_method_target.storage_target

            try:
                storage_medium = self.get_storage_medium(entry, storage_target, storage_method.type)
            except ValueError:
                entry.status = 100
                entry.save(update_fields=['status'])
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
                )

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
                )

                entry.task_id = str(t.pk)
                entry.save(update_fields=['task_id'])

                t.run()

    def undo(self):
        pass

    def event_outcome_success(self):
        pass

class IOTape(DBTask):
    queue = 'io_tape'

    def run(self, io_queue_entry, storage_medium):
        entry = IOQueue.objects.get(pk=io_queue_entry)

        storage_method = entry.storage_method_target.storage_method
        storage_target = entry.storage_method_target.storage_target

        entry.status = 5
        entry.save(update_fields=['status'])

        cache = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache, entry.ip.object_identifier_value) + '.tar'

        step = ProcessStep(name='IO Tape',)

        if hasattr(entry.task, 'processstep') and entry.task.processstep is not None:
            step.parent_step = entry.task.processstep
        else:
            step.information_package = entry.ip

        step.save()

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
                        'medium': storage_medium,
                        'num': int(content_location_value),
                    },
                    processstep=step,
                    processstep_pos=1,
                ).run().get()

                if entry.ip.cached:
                    src = cache_obj
                else:
                    src = entry.ip.object_path

                medium = StorageMedium.objects.get(pk=storage_medium)

                try:
                    ProcessTask.objects.create(
                        name="ESSArch_Core.tasks.WriteToTape",
                        params={
                            'medium': storage_medium,
                            'path': src,
                            'block_size': medium.block_size * 512,
                        },
                        processstep=step,
                        processstep_pos=2,
                    ).run().get()
                except OSError as e:
                    if e.errno == errno.ENOSPC:
                        medium.mark_as_full()
                        entry.status = 0
                        entry.storage_medium = None
                        entry.save(update_fields=['status', 'storage_medium'])
                        return
                    else:
                        raise

                StorageMedium.objects.filter(pk=storage_medium).update(used_capacity=F('used_capacity') + entry.write_size)

                StorageObject.objects.create(
                    content_location_type=storage_method.type,
                    content_location_value=content_location_value,
                    ip=entry.ip, storage_medium_id=storage_medium
                )

                if IOQueue.objects.exclude(ip=entry.ip, status__in=[0, 2, 5]).exists():
                    entry.ip.archived = True
                    entry.ip.cached = True
                    entry.ip.state = 'Preserved'
                    entry.ip.save(update_fields=['archived', 'cached', 'state'])

            elif entry.req_type == 20:  # Read from tape
                tape_pos = int(entry.storage_object.content_location_value)

                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.SetTapeFileNumber",
                    params={
                        'medium': storage_medium,
                        'num': tape_pos,
                    },
                    processstep=step,
                    processstep_pos=1,
                ).run().get()

                medium = StorageMedium.objects.get(pk=storage_medium)

                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.ReadTape",
                    params={
                        'medium': storage_medium,
                        'path': cache,
                        'block_size': medium.block_size * 512,
                    },
                    processstep=step,
                    processstep_pos=2,
                ).run().get()

                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.CopyFile",
                    params={
                        'src': cache_obj,
                        'dst': entry.object_path,
                    },
                    processstep=step,
                    processstep_pos=3,
                ).run().get()

                with tarfile.open(cache_obj) as tar:
                    tar.extractall(cache)
        except:
            entry.status = 100
            raise
        else:
            entry.status = 20
        finally:
            drive = StorageMedium.objects.get(pk=storage_medium).tape_drive
            drive.io_queue_entry = None
            drive.save(update_fields=['io_queue_entry'])
            entry.save(update_fields=['status'])

    def undo(self):
        pass

    def event_outcome_success(self):
        pass

class IODisk(DBTask):
    queue = 'io_disk'

    def run(self, io_queue_entry, storage_medium):
        entry = IOQueue.objects.get(pk=io_queue_entry)
        entry.status = 5
        entry.save(update_fields=['status'])

        storage_method = entry.storage_method_target.storage_method
        storage_target = entry.storage_method_target.storage_target

        cache = entry.ip.policy.cache_storage.value
        cache_obj = os.path.join(cache, entry.ip.object_identifier_value) + '.tar'

        step = ProcessStep(name='IO Disk',)

        if hasattr(entry.task, 'processstep') and entry.task.processstep is not None:
            step.parent_step = entry.task.processstep
        else:
            step.information_package = entry.ip

        step.save()

        try:
            if entry.req_type == 15:  # Write to disk
                content_location_value = os.path.join(storage_target.target, os.path.basename(entry.ip.object_path))
                storage_object = StorageObject.objects.create(
                    content_location_type=storage_method.type,
                    content_location_value=content_location_value,
                    ip=entry.ip, storage_medium_id=storage_medium
                )

                if entry.ip.cached:
                    src = cache_obj
                else:
                    src = entry.ip.object_path

                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.CopyFile",
                    params={
                        'src': src,
                        'dst': storage_target.target,
                    },
                    processstep=step,
                )
                step.run().get()

                if IOQueue.objects.exclude(ip=entry.ip, status__in=[0, 2, 5]).exists():
                    entry.ip.archived = True
                    entry.ip.cached = True
                    entry.ip.state = 'Preserved'
                    entry.ip.save(update_fields=['archived', 'cached', 'state'])

            elif entry.req_type == 25:  # Read from disk
                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.CopyFile",
                    params={
                        'src': entry.storage_object.content_location_value,
                        'dst': cache,
                    },
                    processstep=step,
                    processstep_pos=0,
                )

                ProcessTask.objects.create(
                    name="ESSArch_Core.tasks.CopyFile",
                    params={
                        'src': cache_obj,
                        'dst': entry.object_path,
                    },
                    processstep=step,
                    processstep_pos=5,
                )

                step.run().get()

                with tarfile.open(cache_obj) as tar:
                    tar.extractall(cache)
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
    track = False
    def run(self):
        entries = RobotQueue.objects.filter(
            status__in=[0, 2]
        ).select_related('storage_medium').order_by('-status', '-req_type', 'posted')[:5]

        if not len(entries):
            raise Ignore()

        for entry in entries.iterator():
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
            RobotQueue.objects.get_or_create(
                user=User.objects.get(username='system'),
                storage_medium=drive.storage_medium,
                req_type=20, status__in=[0, 2], defaults={'status': 0}
            )

    def undo(self):
        pass

    def event_outcome_success(self):
        pass


class ValidateFileFormat(tasks.ValidateFileFormat):
    event_type = 30260


class ValidateXMLFile(tasks.ValidateXMLFile):
    event_type = 30261


class ValidateLogicalPhysicalRepresentation(tasks.ValidateLogicalPhysicalRepresentation):
    event_type = 30262


class ValidateIntegrity(tasks.ValidateIntegrity):
    event_type = 30263


class ValidateFiles(tasks.ValidateFiles):
    fileformat_task = "workflow.tasks.ValidateFileFormat"
    checksum_task = "workflow.tasks.ValidateIntegrity"
