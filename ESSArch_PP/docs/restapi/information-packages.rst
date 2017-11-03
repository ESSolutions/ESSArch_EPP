================
 Information Packages
================

.. contents::
    :local:

.. http:get:: /information-packages/

    The information packages visible to the logged in user

.. http:post:: /information-packages/(uuid:ip_id)/preserve/

    Preserves IP (`ip_id`) on storage mediums specified in the policy assigned
    to the IP.

    :status 200: when information package is being preserved
    :status 400: when the information package already is preserved
