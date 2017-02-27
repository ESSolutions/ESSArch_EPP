from rest_framework import viewsets

from ESSArch_Core.tags.models import Tag

from tags.serializers import TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tags to be viewed or edited.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
