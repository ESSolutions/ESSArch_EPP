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

import os
import shutil
import uuid

from ESSArch_Core.configuration.models import ArchivePolicy, Path
from ESSArch_Core.ip.models import InformationPackage, InformationPackageRel
from ESSArch_Core.WorkflowEngine.dbtask import DBTask


class ReceiveSIP(DBTask):
    event_type = 20100

    def run(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
        policy = ArchivePolicy.objects.get(pk=archive_policy)
        ingest = policy.ingest_path
        aip_id = uuid.uuid4()
        aic_id = uuid.uuid4()

        aip = InformationPackage.objects.create(
            pk=aip_id,
            ObjectIdentifierValue=aip_id,
            policy=policy,
            package_type=InformationPackage.AIP
        )

        aic = InformationPackage.objects.create(
            pk=aic_id,
            ObjectIdentifierValue=aic_id,
            package_type=InformationPackage.AIC
        )

        InformationPackageRel.objects.create(aic_uuid=aic, uuid=aip)

        aip_dir = os.path.join(ingest.value, str(aip_id))
        os.mkdir(aip_dir)

        self.set_progress(100, total=100)
        return aip.pk

    def undo(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
        pass

    def event_outcome_success(self, xml=None, container=None, purpose=None, archive_policy=None, allow_unknown_files=False):
        ip_id = os.path.splitext(os.path.basename(xml))[0]
        return "Received IP '%s'" % ip_id
