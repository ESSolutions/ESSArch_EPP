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

from scandir import walk

from ESSArch_Core import tasks
from ESSArch_Core.configuration.models import ArchivePolicy, Path
from ESSArch_Core.essxml.util import parse_submit_description
from ESSArch_Core.ip.models import InformationPackage
from ESSArch_Core.storage.models import (
    DISK,
    TAPE,

    StorageMethod,
    StorageObject,
)
from ESSArch_Core.WorkflowEngine.dbtask import DBTask
from ESSArch_Core.WorkflowEngine.models import ProcessTask, ProcessStep


class ReceiveSIP(DBTask):
    event_type = 20100

    def run(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False, tags=[]):
        policy = ArchivePolicy.objects.get(pk=archive_policy)
        ingest = policy.ingest_path
        objid, container_type = os.path.splitext(os.path.basename(container))

        parsed = parse_submit_description(xml, srcdir=os.path.split(container)[0])

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
        )

        aip.tags = tags
        aip.save()

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

                    with open(src, 'r') as srcf, open(dst, 'w') as dstf:
                        dstf.write(srcf.read())
                        tar.add(src, os.path.join(objid, rel, f))

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

    def create_storage_objs(self, aip, policy):
        storage_methods = policy.storagemethod_set.all()

        if not storage_methods.count():
            raise StorageMethod.DoesNotExist("No storage methods found in policy: '%s'" % policy)

        for method in storage_methods:
            for target in method.active_targets:
                mediums = target.storagemedium_set.filter(used_capacity__lt=target.max_capacity)

                for medium in mediums:
                    yield StorageObject.objects.create(
                        ip_id=aip,
                        storage_medium=medium,
                        content_location_type=method.type
                    )

    def run(self, aip):
        policy = InformationPackage.objects.prefetch_related('policy__storagemethod_set__targets').get(pk=aip).policy
        storage_objs = self.create_storage_objs(aip, policy)

        step = ProcessStep.objects.create(
            name="Write Storage Objects",
            parallel=True,
            eager=False,
        )
        tasks = []

        for s_obj in storage_objs:
            tasks.append(ProcessTask(
                name="workflow.tasks.WriteStorageObject",
                params={
                    'storage_obj': s_obj.id
                },
                processstep=step,
            ))

        ProcessTask.objects.bulk_create(tasks)
        step.run()

        """
        if target.type in range(200, 300):  # disk
            req_type = 15
            req_purpose = 'Write package to disk'
        elif target.type in range(300, 400):  # tape
            req_type = 10
            req_purpose = 'Write package to tape'
        """

    def undo(self, aip):
        pass

    def event_outcome_success(self, aip):
        return "Preserved AIP '%s'" % aip


class WriteStorageObject(DBTask):
    def run(self, storage_obj=None):
        storage_obj = StorageObject.objects.select_related(
            'storage_medium__storage_target', 'ip'
        ).get(pk=storage_obj)

        src = storage_obj.ip.ObjectPath
        dst = storage_obj.storage_medium.storage_target.target

        if storage_obj.content_location_type == DISK:
            copy_task = ProcessTask.objects.create(
                name="ESSArch_Core.tasks.CopyFile",
                params={
                    "src": src,
                    "dst": dst
                },
            )

            copy_task.run()

        elif storage_obj.content_location_type == TAPE:
            pass

    def undo(self, storage_obj=None):
        pass

    def event_outcome_success(self, storage_obj=None):
        pass
