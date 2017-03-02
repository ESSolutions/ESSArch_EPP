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

from ESSArch_Core.configuration.models import ArchivePolicy, Path
from ESSArch_Core.essxml.util import parse_submit_description
from ESSArch_Core.ip.models import InformationPackage, InformationPackageRel
from ESSArch_Core.WorkflowEngine.dbtask import DBTask


class ReceiveSIP(DBTask):
    event_type = 20100

    def run(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
        policy = ArchivePolicy.objects.get(pk=archive_policy)
        ingest = policy.ingest_path
        objid, container_type = os.path.splitext(os.path.basename(container))

        parsed = parse_submit_description(xml, srcdir=os.path.split(container)[0])

        aip = InformationPackage.objects.create(
            ObjectIdentifierValue=objid,
            policy=policy,
            package_type=InformationPackage.AIP,
            Label=parsed.get('label'),
            entry_date=parsed.get('create_date')
        )

        aic = InformationPackage.objects.create(
            package_type=InformationPackage.AIC
        )

        InformationPackageRel.objects.create(aic_uuid=aic, uuid=aip)

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
        return aic.pk

    def undo(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
        pass

    def event_outcome_success(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
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
