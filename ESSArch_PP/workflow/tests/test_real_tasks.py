"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation (EPP)
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

import errno
import filecmp
import os
import shutil
import tarfile
import tempfile
import unittest
import zipfile

from django.contrib.auth.models import User
from django.test import tag, TransactionTestCase, override_settings
from django.utils.timezone import localtime

import mock

from ESSArch_Core.configuration.models import (
    ArchivePolicy, Path,
)

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalLocation,
    ArchivalType,
    InformationPackage,
)

from ESSArch_Core.storage.exceptions import (
    RobotMountException,
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
    StorageTarget,
    StorageMethodTargetRelation,
)

from ESSArch_Core.storage.tape import (
    mount_tape,
    rewind_tape,
    unmount_tape,
)

from ESSArch_Core.WorkflowEngine.models import (
    ProcessTask,
)

from storage.exceptions import (
    TapeMountedError,
    TapeMountedAndLockedByOtherError,
)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class ReceiveSIPTestCase(TransactionTestCase):
    def setUp(self):
        self.root = os.path.dirname(os.path.realpath(__file__))

        self.gate = Path.objects.create(
            entity='gate',
            value=os.path.join(self.root, 'gate')
        )

        self.ingest = Path.objects.create(
            entity='ingest',
            value=os.path.join(self.root, 'ingest')
        )

        self.cache = Path.objects.create(
            entity='cache',
            value=os.path.join(self.root, 'cache')
        )

        self.xmldata = '''
            <mets:mets
                xmlns:mets="http://www.loc.gov/METS/"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://www.loc.gov/METS/ http://xml.essarch.org/METS/info.xsd"
                ID="IDbc94f115-d6c0-43a1-9be8-a073c467bf1b"
                OBJID="UUID:2259f52c-39c6-4a82-a9c3-3e7d29742c21"
                LABEL="test-ip"
                TYPE="SIP"
                PROFILE="my profile">
                <mets:metsHdr CREATEDATE="2016-12-01T11:54:31+01:00">
                </mets:metsHdr>
                <agent ROLE="ARCHIVIST" TYPE="ORGANIZATION">
                    <name>my_archivist_organization</name>
                </agent>
            </mets:mets>
            '''

        for path in [self.gate, self.ingest, self.cache]:
            try:
                os.makedirs(path.value)
            except OSError as e:
                if e.errno != 17:
                    raise

    def tearDown(self):
        for path in [self.gate, self.ingest, self.cache]:
            try:
                shutil.rmtree(path.value)
            except:
                pass

    def test_receive_sip(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        open(container, 'a').close()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xml,
                'container': container,
                'archive_policy': policy.pk
            },
        )

        aip_id = task.run().get()
        aip = InformationPackage.objects.filter(
            pk=aip_id,
            ObjectIdentifierValue=sip,
            package_type=InformationPackage.AIP
        )
        self.assertTrue(aip.exists())

        aic = aip.first().aic
        self.assertEqual(str(aic.pk), aic.ObjectIdentifierValue)
        self.assertEqual(aic.package_type, InformationPackage.AIC)

        aip = aip.first()
        self.assertEqual(aip.Label, 'test-ip')
        self.assertEqual(localtime(aip.entry_date).isoformat(), '2016-12-01T11:54:31+01:00')

        self.assertEqual(sip, aip.ObjectIdentifierValue)
        expected_aip = os.path.join(self.ingest.value, sip)
        self.assertTrue(os.path.isdir(expected_aip))

        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertTrue(os.path.isfile(expected_tar))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertFalse(os.path.isdir(expected_content_dir))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

        self.assertEqual(ArchivistOrganization.objects.get().name, 'my_archivist_organization')
        self.assertIsNotNone(aip.ArchivistOrganization)

    def test_receive_sip_with_information_class_same_as_policy(self):
        self.xmldata = '''
            <mets LABEL="test-ip">
                <metsHdr CREATEDATE="2016-12-01T11:54:31+01:00">
                </metsHdr>
                <altRecordID TYPE="INFORMATIONCLASS">1</altRecordID>
            </mets>
            '''
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        open(container, 'a').close()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            information_class=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xml,
                'container': container,
                'archive_policy': policy.pk
            },
        )

        aip_id = task.run().get()
        aip = InformationPackage.objects.filter(
            pk=aip_id,
            ObjectIdentifierValue=sip,
            package_type=InformationPackage.AIP,
            information_class=1,
        )
        self.assertTrue(aip.exists())

    def test_receive_sip_with_information_class_different_from_policy(self):
        self.xmldata = '''
            <mets LABEL="test-ip">
                <metsHdr CREATEDATE="2016-12-01T11:54:31+01:00">
                </metsHdr>
                <altRecordID TYPE="INFORMATIONCLASS">2</altRecordID>
            </mets>
            '''
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        open(container, 'a').close()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            information_class=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xml,
                'container': container,
                'archive_policy': policy.pk
            },
        )

        with self.assertRaises(ValueError):
            task.run().get()

        self.assertFalse(InformationPackage.objects.exists())

    def test_receive_sip_extract_tar(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.tar')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ["foo", "bar", "baz"]:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with tarfile.open(container, 'w') as tar:
            for f in files:
                arc = os.path.basename(os.path.normpath(f))
                tar.add(f, arc)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xml,
                'container': container,
                'archive_policy': policy.pk
            },
        )

        task.run()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))

    def test_receive_sip_extract_zip(self):
        sip = 'sip_objid'

        xml = os.path.join(self.gate.value, sip + '.xml')
        container = os.path.join(self.gate.value, sip + '.zip')

        with open(xml, 'w') as xmlf:
            xmlf.write(self.xmldata)

        files = []

        for name in ["foo", "bar", "baz"]:
            fpath = os.path.join(self.gate.value, name)
            open(fpath, 'a').close()
            files.append(fpath)

        with zipfile.ZipFile(container, 'w') as zipf:
            for f in files:
                arc = os.path.basename(os.path.normpath(f))
                zipf.write(f, arc)

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
            receive_extract_sip=True
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xml,
                'container': container,
                'archive_policy': policy.pk
            },
        )

        task.run()

        expected_aip = os.path.join(self.ingest.value, sip)
        expected_content = os.path.join(expected_aip, 'content')
        self.assertTrue(os.path.isdir(expected_content))

        expected_tar = os.path.join(expected_content, sip + '.tar')
        self.assertFalse(os.path.isfile(expected_tar))

        expected_zip = os.path.join(expected_content, sip + '.zip')
        self.assertFalse(os.path.isfile(expected_zip))

        expected_content_dir = os.path.join(expected_content, sip)
        self.assertTrue(os.path.isdir(expected_content_dir))

        for f in files:
            expected_file = os.path.join(expected_content_dir, os.path.basename(f))
            self.assertTrue(os.path.isfile(expected_file))

        expected_metadata = os.path.join(expected_aip, 'metadata')
        self.assertTrue(os.path.isdir(expected_metadata))


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class CacheAIPTestCase(TransactionTestCase):
    def setUp(self):
        self.root = os.path.dirname(os.path.realpath(__file__))

        self.ingest = Path.objects.create(
            entity='ingest',
            value=os.path.join(self.root, 'ingest')
        )

        self.cache = Path.objects.create(
            entity='cache',
            value=os.path.join(self.root, 'cache')
        )

        for path in [self.ingest, self.cache]:
            try:
                os.makedirs(path.value)
            except OSError as e:
                if e.errno != 17:
                    raise

    def tearDown(self):
        for path in [self.ingest, self.cache]:
            try:
                shutil.rmtree(path.value)
            except:
                pass

    def test_cache_aip(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(ObjectIdentifierValue='custom_obj_id', policy=policy)

        aip_dir = os.path.join(policy.ingest_path.value, aip.ObjectIdentifierValue)
        os.mkdir(aip_dir)
        os.mkdir(os.path.join(aip_dir, 'content'))
        os.mkdir(os.path.join(aip_dir, 'metadata'))

        contentfile = os.path.join(
            aip_dir, 'content', 'myfile.txt'
        )

        with open(contentfile, 'a') as f:
            f.write('foo')

        task = ProcessTask.objects.create(
            name='workflow.tasks.CacheAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run()

        cached_dir = os.path.join(aip.policy.cache_storage.value, aip.ObjectIdentifierValue)
        self.assertTrue(os.path.isdir(cached_dir))

        equal_content = filecmp.cmp(
            os.path.join(aip_dir, 'content', 'myfile.txt'),
            os.path.join(cached_dir, 'content', 'myfile.txt'),
            False
        )
        self.assertTrue(equal_content)

        extracted = os.path.join(aip.policy.cache_storage.value, 'extracted')
        os.mkdir(extracted)

        cached_container = os.path.join(aip.policy.cache_storage.value, aip.ObjectIdentifierValue + '.tar')
        self.assertTrue(os.path.isfile(cached_container))

        with tarfile.open(cached_container) as tar:
            tar.extractall(extracted)

        equal_content = filecmp.cmp(
            os.path.join(aip_dir, 'content', 'myfile.txt'),
            os.path.join(extracted, aip.ObjectIdentifierValue, 'content', 'myfile.txt'),
            False
        )
        self.assertTrue(equal_content)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class StoreAIPTestCase(TransactionTestCase):
    def setUp(self):
        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

        self.datadir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

        try:
            shutil.rmtree(self.storagedir)
        except:
            pass

    def test_store_aip_no_policy(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(policy=policy)

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        with self.assertRaises(StorageMethod.DoesNotExist):
            task.run().get()

    def test_store_aip_no_storage_method(self):
        aip = InformationPackage.objects.create()

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        with self.assertRaises(ArchivePolicy.DoesNotExist):
            task.run().get()

    def test_store_aip_disk(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        self.assertTrue(queue_entry.exists())

    def test_store_aip_disk_and_tape(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        method2 = StorageMethod.objects.create(archive_policy=policy, type=TAPE)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )
        method_target2 = StorageMethodTargetRelation.objects.create(
            storage_method=method2, storage_target=target, status=2
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )
        queue_entry2 = IOQueue.objects.filter(
            req_type=10, status=0, ip=aip, storage_method_target=method_target2,
        )

        self.assertTrue(queue_entry.exists())
        self.assertTrue(queue_entry2.exists())

    def test_store_aip_with_same_existing(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.datadir,
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task.run().get()
        task.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        self.assertEqual(queue_entry.count(), 1)

    def test_store_aip_with_different_existing(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.datadir,
        )
        aip2 = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id_2', policy=policy,
            ObjectPath=self.datadir
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(archive_policy=policy, type=DISK)
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target, status=1
        )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
            responsible=user,
        )

        task2 = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip2.pk
            },
            responsible=user,
        )

        task.run().get()
        task2.run().get()

        queue_entry = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip, storage_method_target=method_target,
        )

        queue_entry2 = IOQueue.objects.filter(
            req_type=15, status=0, ip=aip2, storage_method_target=method_target,
        )

        self.assertTrue(queue_entry.exists())
        self.assertTrue(queue_entry2.exists())


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollRobotQueueTestCase(TransactionTestCase):
    def setUp(self):
        self.datadir = tempfile.mkdtemp()

        self.label_dir = Path.objects.create(
            entity='label', value=os.path.join(self.datadir, 'label')
        )

        self.ingest = Path.objects.create(
            entity='ingest', value='ingest'
        )

        self.cache = Path.objects.create(
            entity='cache', value='cache',
        )

        try:
            os.mkdir(self.datadir)
        except OSError as e:
            if e.errno != 17:
                raise

        try:
            os.mkdir(self.label_dir.value)
        except OSError as e:
            if e.errno != 17:
                raise

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

    def test_no_entry(self):
        ProcessTask.objects.create(
            name='workflow.tasks.PollRobotQueue',
        ).run().get()

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mount(self, mock_mount_task):
        mock_mount_task.side_effect = lambda *args, **kwargs: None

        user = User.objects.create()

        tape_drive = TapeDrive.objects.create(
            id=0, robot=self.robot, device=self.device
        )

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create(type=301)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        medium = StorageMedium.objects.create(
            medium_id='AAA001', storage_target=target,
            status=20, location_status=50, block_size=128,
            format=103, agent=user, tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        ProcessTask.objects.create(
            name='workflow.tasks.PollRobotQueue',
        ).run().get()

        robot_queue.refresh_from_db()
        tape_drive.refresh_from_db()

        mock_mount_task.assert_called_once_with(drive=tape_drive.pk, medium=medium.pk)

        self.assertEqual(robot_queue.status, 20)
        self.assertIsNone(robot_queue.robot)
        self.assertEqual(tape_drive.io_queue_entry, io_queue)

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_failing_mount(self, mock_mount_task):
        mock_mount_task.side_effect = Exception()

        user = User.objects.create()

        tape_drive = TapeDrive.objects.create(
            id=0, robot=self.robot, device=self.device
        )

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create(type=301)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        medium = StorageMedium.objects.create(
            medium_id='AAA001', storage_target=target,
            status=20, location_status=50, block_size=128,
            format=103, agent=user, tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        with self.assertRaises(Exception):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()
        tape_drive.refresh_from_db()

        mock_mount_task.assert_called_once_with(drive=tape_drive.pk, medium=medium.pk)

        self.assertEqual(robot_queue.status, 100)
        self.assertIsNotNone(robot_queue.robot)
        self.assertEqual(tape_drive.io_queue_entry, io_queue)

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mounting_already_mounted_medium(self, mock_mount_task):
        user = User.objects.create()

        target = StorageTarget.objects.create()

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive
        )

        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
        )

        with self.assertRaises(TapeMountedError):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()

        self.assertEqual(robot_queue.status, 20)
        self.assertIsNone(robot_queue.robot)
        mock_mount_task.assert_not_called()

    @mock.patch('ESSArch_Core.tasks.MountTape.run')
    def test_mounting_already_mounted_and_locked_medium(self, mock_mount_task):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        robot_queue = RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue,
        )

        with self.assertRaises(TapeMountedAndLockedByOtherError):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

        robot_queue.refresh_from_db()

        self.assertEqual(robot_queue.status, 0)
        self.assertIsNone(robot_queue.robot)
        mock_mount_task.assert_not_called()

    def test_no_robot_available(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue, robot=self.robot,
        )

        with self.assertRaisesRegexp(ValueError, 'No robot available'):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()

    def test_no_drive_available(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot
        )

        io_queue = IOQueue.objects.create(
            req_type=10, user=user,
            storage_method_target=method_target,
        )
        RobotQueue.objects.create(
            user=user, storage_medium=medium, req_type=10,
            io_queue_entry=io_queue
        )

        with self.assertRaisesRegexp(ValueError, 'No tape drive available'):
            ProcessTask.objects.create(
                name='workflow.tasks.PollRobotQueue',
            ).run().get()


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.ingest = Path.objects.create(
            entity='ingest', value='ingest'
        )

        self.cache = Path.objects.create(
            entity='cache', value='cache',
        )

    def test_no_entry(self):
        ProcessTask.objects.create(name=self.taskname,).run().get()
        self.assertFalse(RobotQueue.objects.exists())

    def test_completed_entry(self):
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE,
        )
        target = StorageTarget.objects.create()

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=0,
            status=20
        )

        ProcessTask.objects.create(name=self.taskname,).run().get()
        self.assertFalse(RobotQueue.objects.exists())


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueWriteTapeTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def test_write_no_available_tape(self):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target='target')

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        TapeSlot.objects.create(slot_id=1, robot=self.robot)

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path='objpath', ip=ip,
        )

        with self.assertRaisesRegexp(ValueError, 'No tape available for allocation'):
            ProcessTask.objects.create(
                name=self.taskname,
                responsible=user,
            ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 100)
        self.assertFalse(StorageMedium.objects.filter(storage_target=target).exists())
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    def test_write_unmounted_tape(self):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target='target')

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path='objpath', ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 0)
        self.assertTrue(StorageMedium.objects.filter(storage_target=target).exists())
        self.assertTrue(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.WriteToTape.run')
    def test_write_mounted_tape(self, mock_write, mock_set_file_number):
        mock_write.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.ObjectPath, ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='1').exists())

        mock_write.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.WriteToTape.run')
    def test_write_mounted_tape_twice(self, mock_write, mock_set_file_number):
        mock_write.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.ObjectPath, ip=ip,
        )

        io_queue2 = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=10,
            object_path=ip.ObjectPath, ip=ip,
        )

        ProcessTask.objects.create(name=self.taskname,).run().get()

        mock_write.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)
        mock_write.reset_mock()
        mock_set_file_number.reset_mock()

        ProcessTask.objects.create(name=self.taskname,).run().get()

        mock_write.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=2)

        io_queue.refresh_from_db()
        io_queue2.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertEqual(io_queue2.status, 20)

        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='1').exists())
        self.assertTrue(StorageObject.objects.filter(content_location_value='2').exists())


@tag('tape')
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueReadTapeTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

        self.robot = Robot.objects.create(device='/dev/sg6')
        self.device = '/dev/nst0'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_tape_without_storage_object(self, mock_read):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user, tape_slot=tape_slot,
        )

        TapeDrive.objects.create(
            id=0, device=self.device, robot=self.robot,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=20,
            object_path=ip.ObjectPath, ip=ip,
        )

        with self.assertRaises(ValueError):
            ProcessTask.objects.create(
                name=self.taskname,
                responsible=user,
            ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 100)
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())
        mock_read.assert_not_called()

    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_unmounted_tape(self, mock_read):
        ip = InformationPackage.objects.create()
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user, tape_slot=tape_slot,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value='1', ip=ip,
            content_location_type=TAPE,
        )

        TapeDrive.objects.create(
            id=0, device=self.device, robot=self.robot,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target,
            storage_object=obj, req_type=20, object_path=ip.ObjectPath,
            ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 0)
        self.assertTrue(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())
        mock_read.assert_not_called()

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_mounted_tape(self, mock_read, mock_set_file_number):
        mock_read.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user, tape_slot=tape_slot, tape_drive=tape_drive,
        )
        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value='1', ip=ip,
            content_location_type=TAPE,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target,
            storage_object=obj, req_type=20, object_path=ip.ObjectPath,
            ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)
        mock_read.assert_called_once_with(medium=medium.pk, path=self.datadir)

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.filter(io_queue_entry=io_queue).exists())

    @mock.patch('ESSArch_Core.tasks.SetTapeFileNumber.run')
    @mock.patch('ESSArch_Core.tasks.ReadTape.run')
    def test_read_mounted_tape_twice(self, mock_read, mock_set_file_number):
        mock_read.side_effect = lambda *args, **kwargs: None
        mock_set_file_number.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        ip2 = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )
        target = StorageTarget.objects.create(target=self.device)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        tape_slot = TapeSlot.objects.create(slot_id=1, robot=self.robot, medium_id=target.target)
        tape_drive = TapeDrive.objects.create(id=0, device=self.device, robot=self.robot)

        medium = StorageMedium.objects.create(
            medium_id='medium', storage_target=target, status=20,
            location_status=50, block_size=128, format=103, agent=user,
            tape_slot=tape_slot, tape_drive=tape_drive,
        )

        obj = StorageObject.objects.create(
            content_location_value='1', content_location_type=TAPE, ip=ip,
            storage_medium=medium,
        )

        obj2 = StorageObject.objects.create(
            content_location_value='2', content_location_type=TAPE, ip=ip2,
            storage_medium=medium,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_medium=medium, req_type=20, ip=ip,
            storage_method_target=method_target, storage_object=obj,
            object_path=ip.ObjectPath,
        )

        io_queue2 = IOQueue.objects.create(
            user=user, storage_medium=medium, req_type=20, ip=ip,
            storage_method_target=method_target, storage_object=obj2,
            object_path=ip2.ObjectPath,
        )

        ProcessTask.objects.create(
            name=self.taskname,
        ).run().get()

        mock_read.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=1)
        mock_read.reset_mock()
        mock_set_file_number.reset_mock()

        ProcessTask.objects.create(
            name=self.taskname,
        ).run().get()

        mock_read.assert_called_once_with(medium=medium.pk, path=self.datadir)
        mock_set_file_number.assert_called_once_with(medium=medium.pk, num=2)

        io_queue.refresh_from_db()
        io_queue2.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertEqual(io_queue2.status, 20)
        self.assertFalse(RobotQueue.objects.exists())


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueWriteDiskTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()
        self.storagedir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        try:
            shutil.rmtree(self.storagedir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    def test_write(self, mock_copy):
        mock_copy.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=DISK
        )
        target = StorageTarget.objects.create(target=self.storagedir)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20, location_status=20,
            block_size=target.default_block_size, format=target.default_format,
            agent=user,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=15,
            object_path=self.datadir, ip=ip,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(storage_medium=medium, ip=ip).exists())

        mock_copy.assert_called_once_with(src=ip.ObjectPath, dst=target.target)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class PollIOQueueReadDiskTestCase(TransactionTestCase):
    def setUp(self):
        self.taskname = 'workflow.tasks.PollIOQueue'

        self.datadir = tempfile.mkdtemp()
        self.storagedir = tempfile.mkdtemp()

        self.ingest = Path.objects.create(entity='ingest', value='ingest')
        self.cache = Path.objects.create(entity='cache', value='cache')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        try:
            shutil.rmtree(self.storagedir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @mock.patch('ESSArch_Core.tasks.CopyFile.run')
    def test_read(self, mock_copy):
        mock_copy.side_effect = lambda *args, **kwargs: None

        ip = InformationPackage.objects.create(ObjectPath=self.datadir)
        user = User.objects.create()

        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        method = StorageMethod.objects.create(
            archive_policy=policy, type=DISK
        )
        target = StorageTarget.objects.create(target=self.datadir)

        method_target = StorageMethodTargetRelation.objects.create(
            storage_method=method, storage_target=target,
        )

        medium = StorageMedium.objects.create(
            storage_target=target, status=20,
            location_status=20,
            block_size=target.default_block_size,
            format=target.default_format,
            agent=user,
        )

        obj = StorageObject.objects.create(
            storage_medium=medium, content_location_value=self.storagedir, ip=ip,
            content_location_type=DISK,
        )

        io_queue = IOQueue.objects.create(
            user=user, storage_method_target=method_target, req_type=25,
            object_path=self.datadir, ip=ip, storage_object=obj,
        )

        ProcessTask.objects.create(
            name=self.taskname,
            responsible=user,
        ).run().get()

        io_queue.refresh_from_db()

        self.assertEqual(io_queue.status, 20)
        self.assertFalse(RobotQueue.objects.exists())
        self.assertTrue(StorageObject.objects.filter(storage_medium=medium, ip=ip).exists())

        mock_copy.assert_called_once_with(src=obj.content_location_value, dst=ip.ObjectPath)
