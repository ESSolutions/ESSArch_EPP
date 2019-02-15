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

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from ESSArch_Core.WorkflowEngine.views import ProcessViewSet, ProcessStepViewSet, ProcessTaskViewSet
from ESSArch_Core.auth.views import (GroupViewSet, OrganizationViewSet, PermissionViewSet, MeView, NotificationViewSet,
                                     UserViewSet)
from ESSArch_Core.configuration.views import ArchivePolicyViewSet, ParameterViewSet, PathViewSet, SysInfoView
from ESSArch_Core.fixity.views import ValidationViewSet
from ESSArch_Core.ip.views import EventIPViewSet, WorkareaEntryViewSet
from ESSArch_Core.maintenance.views import (AppraisalRuleViewSet, AppraisalJobViewSet, ConversionRuleViewSet,
                                            ConversionJobViewSet)
from ESSArch_Core.profiles.views import ProfileIPViewSet, ProfileIPDataViewSet
from ESSArch_Core.routers import ESSArchRouter
from configuration.views import EventTypeViewSet
from ip.views import (InformationPackageViewSet, InformationPackageReceptionViewSet, OrderViewSet, WorkareaViewSet,
                      WorkareaFilesViewSet)
from profiles.views import (
    ProfileViewSet,
    ProfileSAViewSet,
    ProfileMakerExtensionViewSet,
    ProfileMakerTemplateViewSet,
    SubmissionAgreementViewSet,
    SubmissionAgreementTemplateView
)
from storage.views import (AccessQueueViewSet, IOQueueViewSet, RobotViewSet, RobotQueueViewSet, StorageObjectViewSet,
                           StorageMediumViewSet, StorageMethodViewSet, StorageMethodTargetRelationViewSet,
                           StorageTargetViewSet, TapeDriveViewSet, TapeSlotViewSet)
from tags.search import ComponentSearchViewSet
from tags.views import (
    AgentViewSet,
    ArchiveViewSet,
    StructureViewSet,
    StructureUnitViewSet,
    TagViewSet,
    TagInformationPackagesViewSet,
)

router = ESSArchRouter()

admin.site.site_header = 'ESSArch Preservation Platform Administration'
admin.site.site_title = 'ESSArch Preservation Platform Administration'

router.register(r'access-queue', AccessQueueViewSet)
router.register(r'agents', AgentViewSet).register(
    r'archives',
    ArchiveViewSet,
    base_name='agent-archives',
    parents_query_lookups=['agent']
)
router.register(r'archive_policies', ArchivePolicyViewSet)
router.register(r'classification-structures', StructureViewSet).register(
    r'units',
    StructureUnitViewSet,
    base_name='structure-units',
    parents_query_lookups=['structure']
)
router.register(r'classification-structure-units', StructureUnitViewSet)
router.register(r'event-types', EventTypeViewSet)
router.register(r'events', EventIPViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'organizations', OrganizationViewSet, base_name='organizations')
router.register(r'appraisal-jobs', AppraisalJobViewSet)
router.register(r'appraisal-rules', AppraisalRuleViewSet)
router.register(r'conversion-jobs', ConversionJobViewSet)
router.register(r'conversion-rules', ConversionRuleViewSet)
router.register(r'information-packages', InformationPackageViewSet, base_name='informationpackage')
router.register(r'information-packages', InformationPackageViewSet).register(
    r'appraisal-rules',
    AppraisalRuleViewSet,
    base_name='ip-appraisal-rules',
    parents_query_lookups=['information_packages']
)
router.register(r'information-packages', InformationPackageViewSet).register(
    r'conversion-rules',
    ConversionRuleViewSet,
    base_name='ip-conversion-rules',
    parents_query_lookups=['information_packages']
)
router.register(r'information-packages', InformationPackageViewSet).register(
    r'events',
    EventIPViewSet,
    base_name='ip-events',
    parents_query_lookups=['linkingObjectIdentifierValue']
)
router.register(r'information-packages', InformationPackageViewSet).register(
    r'storage-objects',
    StorageObjectViewSet,
    base_name='ip-storage-objects',
    parents_query_lookups=['ip']
)
router.register(r'io-queue', IOQueueViewSet)
router.register(r'ip-reception', InformationPackageReceptionViewSet, base_name="ip-reception")
router.register(r'notifications', NotificationViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'parameters', ParameterViewSet)
router.register(r'paths', PathViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'profile-ip', ProfileIPViewSet)
router.register(r'profile-ip-data', ProfileIPDataViewSet)
router.register(r'profile-sa', ProfileSAViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'profilemaker-extensions', ProfileMakerExtensionViewSet)
router.register(r'profilemaker-templates', ProfileMakerTemplateViewSet)
router.register(r'robots', RobotViewSet)
router.register(r'robots', ProcessStepViewSet, base_name='robots').register(
    r'queue',
    RobotQueueViewSet,
    base_name='robots-queue',
    parents_query_lookups=['robot']
)
router.register(r'robot-queue', RobotQueueViewSet)
router.register(r'steps', ProcessStepViewSet)
router.register(r'steps', ProcessStepViewSet, base_name='steps').register(
    r'tasks',
    ProcessTaskViewSet,
    base_name='steps-tasks',
    parents_query_lookups=['processstep']
)
router.register(r'steps', ProcessStepViewSet, base_name='steps').register(
    r'children',
    ProcessViewSet,
    base_name='steps-children',
    parents_query_lookups=['processstep']
)

router.register(r'submission-agreements', SubmissionAgreementViewSet)
router.register(r'tags', TagViewSet)
router.register(r'tags', TagViewSet, base_name='tags').register(
    r'information-packages',
    TagInformationPackagesViewSet,
    base_name='tags-informationpackages',
    parents_query_lookups=['tag']
)
router.register(r'tags', TagViewSet, base_name='tags').register(
    r'descendants',
    TagViewSet,
    base_name='tags-descendants',
    parents_query_lookups=['tag']
)

router.register(r'tasks', ProcessTaskViewSet)
router.register(r'tasks', ProcessTaskViewSet).register(
    r'validations',
    ValidationViewSet,
    base_name='task-validations',
    parents_query_lookups=['task']
)
router.register(r'users', UserViewSet)
router.register(r'workareas', WorkareaViewSet, base_name='workarea')
router.register(r'workareas', WorkareaViewSet, base_name='workarea').register(
    r'events',
    EventIPViewSet,
    base_name='workarea-events',
    parents_query_lookups=['linkingObjectIdentifierValue']
)
router.register(r'workarea-entries', WorkareaEntryViewSet, base_name='workarea-entries')
router.register(r'workarea-files', WorkareaFilesViewSet, base_name='workarea-files')

router.register(r'storage-objects', StorageObjectViewSet)
router.register(r'storage-mediums', StorageMediumViewSet)

router.register(r'storage-methods', StorageMethodViewSet)
router.register(r'storage-method-target-relations', StorageMethodTargetRelationViewSet)
router.register(r'storage-targets', StorageTargetViewSet)
router.register(r'tape-drives', TapeDriveViewSet)
router.register(r'tape-slots', TapeSlotViewSet)


router.register(r'storage-mediums', StorageMediumViewSet, base_name='storagemedium').register(
    r'storage-objects',
    StorageObjectViewSet,
    base_name='storagemedium-storageobject',
    parents_query_lookups=['storage_medium']
)
router.register(r'robots', RobotViewSet, base_name='robots').register(
    r'tape-slots',
    TapeSlotViewSet,
    base_name='robots-tapeslots',
    parents_query_lookups=['tape_slots']
)
router.register(r'robots', RobotViewSet, base_name='robots').register(
    r'tape-drives',
    TapeDriveViewSet,
    base_name='robots-tapedrives',
    parents_query_lookups=['tape_drives']
)

router.register(r'search', ComponentSearchViewSet, base_name='search')

urlpatterns = [
    url(r'^', include('ESSArch_Core.frontend.urls'), name='home'),
    url(r'^accounts/changepassword', auth_views.password_change, {'post_change_redirect': '/'}),
    url(r'^accounts/login/$', auth_views.login),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),
    url(r'^api/sysinfo/', SysInfoView.as_view()),
    url(r'^api/me/$', MeView.as_view(), name='me'),
    url(r'^api/submission-agreement-template/$', SubmissionAgreementTemplateView.as_view()),
    url(r'^docs/', include('ESSArch_Core.docs.urls')),
    url(r'^rest-auth/', include('ESSArch_Core.auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
]

if getattr(settings, 'ENABLE_ADFS_LOGIN', False):
    urlpatterns.append(url(r'^saml2/', include('djangosaml2.urls', namespace='saml2')))
