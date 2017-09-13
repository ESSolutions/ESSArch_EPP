from lxml import etree

from rest_framework.exceptions import ValidationError
from rest_framework import serializers

import requests

from ESSArch_Core.essxml.ProfileMaker.models import extensionPackage, templatePackage
from ESSArch_Core.essxml.ProfileMaker.xsdtojson import generateExtensionRef, generateJsonRes

class ProfileMakerExtensionSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        schema_url = validated_data.pop('schemaURL')
        schema_request = requests.get(schema_url)
        schema_request.raise_for_status()

        schemadoc = etree.fromstring(schema_request.content)

        print schemadoc.nsmap
        nsmap = {k: v for k, v in schemadoc.nsmap.iteritems() if k and v != "http://www.w3.org/2001/XMLSchema"}
        targetNamespace = schemadoc.get('targetNamespace')

        prefix = validated_data.pop('prefix')
        extensionElements, extensionAll, attributes = generateExtensionRef(schemadoc, prefix)

        return extensionPackage.objects.create(
            prefix=prefix, schemaURL=schema_url, targetNamespace=targetNamespace,
            allElements=extensionAll, existingElements=extensionElements,
            allAttributes=attributes, nsmap=nsmap, **validated_data
        )

    class Meta:
        model = extensionPackage
        fields = (
            'id', 'allElements', 'existingElements', 'allAttributes', 'prefix', 'schemaURL', 'targetNamespace',
        )

        read_only_fields = (
            'existingElements', 'allElements', 'allAttributes',
        )

        extra_kwargs = {
            'targetNamespace': {
                'required': False
            }
        }

class ProfileMakerTemplateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        schema_request = requests.get(validated_data['schemaURL'])
        schema_request.raise_for_status()

        schemadoc = etree.fromstring(schema_request.content)
        targetNamespace = schemadoc.get('targetNamespace')
        nsmap = {k: v for k, v in schemadoc.nsmap.iteritems() if k and v != "http://www.w3.org/2001/XMLSchema"}

        try:
            existingElements, allElements = generateJsonRes(schemadoc, validated_data['root_element'], validated_data['prefix']);
        except ValueError as e:
            raise ValidationError(e.message)

        return templatePackage.objects.create(
            existingElements=existingElements, allElements=allElements,
            targetNamespace=targetNamespace, nsmap=nsmap, **validated_data
        )

    class Meta:
        model = templatePackage
        fields = (
            'existingElements', 'allElements', 'name', 'root_element',
            'extensions', 'prefix', 'schemaURL', 'targetNamespace', 'structure'
        )

        read_only_fields = (
            'existingElements', 'allElements',
        )

        extra_kwargs = {
            'extensions': {
                'required': False,
                'allow_empty': True,
            },
            'root_element': {
                'required': True
            },
            'targetNamespace': {
                'required': False
            }
        }
