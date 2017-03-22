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

import filecmp
import os
import shutil
import tarfile
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TransactionTestCase, override_settings
from django.utils.timezone import localtime

from ESSArch_Core.configuration.models import (
    ArchivePolicy, Path,
)

from ESSArch_Core.ip.models import (
    InformationPackage,
)

from ESSArch_Core.storage.models import (
    DISK,
    TAPE,

    StorageMedium,
    StorageMethod,
    StorageTarget,
    StorageMethodTargetRelation,
)

from ESSArch_Core.WorkflowEngine.models import (
    ProcessTask,
)


@override_settings(CELERY_ALWAYS_EAGER=True)
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
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


@override_settings(CELERY_ALWAYS_EAGER=True)
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
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


@override_settings(CELERY_ALWAYS_EAGER=True)
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class StoreAIPTestCase(TransactionTestCase):
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

        self.datadir = os.path.join(self.root, 'datadir')
        self.storage_target_dir = os.path.join(self.datadir, 'target')

        self.tarfile = os.path.join(self.datadir, 'file.tar')

        os.mkdir(self.datadir)
        os.mkdir(self.storage_target_dir)

        open(self.tarfile, 'a').close()

        for path in [self.ingest, self.cache]:
            try:
                os.makedirs(path.value)
            except OSError as e:
                if e.errno != 17:
                    raise

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

        for path in [self.ingest, self.cache]:
            try:
                shutil.rmtree(path.value)
            except:
                pass

    def test_store_aip_disk(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.tarfile
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(
            archive_policy=policy, type=DISK
        )

        targets = []

        for i in range(2):
            target_dir = os.path.join(self.storage_target_dir, str(i))
            targets.append(target_dir)
            os.mkdir(target_dir)

            target = StorageTarget.objects.create(
                name='target_%s' % i, max_capacity=1024, target=target_dir
            )

            StorageMethodTargetRelation.objects.create(
                storage_method=method, storage_target=target, status=1
            )

            StorageMedium.objects.create(
                medium_id='medium_%s' % i, storage_target=target,
                status=20, location_status=50, block_size=128,
                format=103, agent=user,
            )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run().get()

        for target in targets:
            dst = os.path.join(target, os.path.basename(self.tarfile))
            self.assertTrue(filecmp.cmp(self.tarfile, dst, False))

    def test_store_aip_tape(self):
        policy = ArchivePolicy.objects.create(
            cache_storage=self.cache,
            ingest_path=self.ingest,
        )
        aip = InformationPackage.objects.create(
            ObjectIdentifierValue='custom_obj_id', policy=policy,
            ObjectPath=self.tarfile
        )
        user = User.objects.create()

        method = StorageMethod.objects.create(
            archive_policy=policy, type=TAPE
        )

        targets = []

        for i in range(2):
            target_dir = os.path.join(self.storage_target_dir, str(i))
            targets.append(target_dir)
            os.mkdir(target_dir)

            target = StorageTarget.objects.create(
                name='target_%s' % i, max_capacity=1024, target=target_dir
            )

            StorageMethodTargetRelation.objects.create(
                storage_method=method, storage_target=target, status=1
            )

            StorageMedium.objects.create(
                medium_id='medium_%s' % i, storage_target=target,
                status=20, location_status=50, block_size=128,
                format=103, agent=user,
            )

        task = ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            params={
                'aip': aip.pk
            },
        )

        task.run().get()

        for target in targets:
            dst = os.path.join(target, os.path.basename(self.tarfile))
            self.assertTrue(filecmp.cmp(self.tarfile, dst, False))
