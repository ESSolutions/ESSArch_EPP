from django.db.models import Q

from ESSArch_Core.configuration.models import EventType
from ESSArch_Core.configuration.views import EventTypeViewSet as CoreEventTypeViewSet


class EventTypeViewSet(CoreEventTypeViewSet):
    queryset = EventType.objects.filter(eventType__range=(30000, 59999))
