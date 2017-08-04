from rest_framework import serializers

from ESSArch_Core.essxml.ProfileMaker.models import extensionPackage, templatePackage

class ProfileMakerExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = extensionPackage
        fields = (
            'id', 'allElements', 'existingElements', 'allAttributes', 'prefix', 'schemaURL', 'targetNamespace',
        )

class ProfileMakerTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = templatePackage
        fields = (
            'existingElements', 'allElements', 'name', 'root_element',
            'extensions', 'prefix', 'schemaURL', 'targetNamespace',
        )