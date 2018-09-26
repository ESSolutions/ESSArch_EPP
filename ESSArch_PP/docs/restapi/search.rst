================
 Search
================

.. py:attribute:: EXPORT_FORMATS

   File formats available to export search results to:

   * CSV
   * PDF

.. http:get:: /search/

   Searches all archives the user has access to in their current organization.

   The response consists of two parts, ``hits`` and ``aggregations``. ``hits``
   contains the search results while ``aggregations`` contains statistics about
   how the results is split up in different groups. 

   Each result consists of the matched document and some information about why
   it was included in the results. The ``_score`` is a positive floating-point
   number that increases the more relevant a search result is to the query.
   The ``highlight`` is used to show the user which part of a value
   that matched the query.

   :query string q: The search keywords
   :query string archive: Which are archive to search in
   :query [string] extension: Which file extensions to include
   :query string type: Restrict results to a single type (e.g. archive, volume, document)
   :query string start_date: Restrict results to a start date (YYYY[-MM-DD])
   :query string end_date: Restrict results to an end date (YYYY[-MM-DD])
   :query int page: page number
   :query int page_size: number of results per page. Default: 10
   :query string export: Exports the results to a file, must be a value in :py:attr:`EXPORT_FORMATS`

   :status 400: :code:`start_date > end_date` or accessing objects outside of
      `max_result_window`_
   :status 404: invalid :code:`page`

   **Example response**:

   .. sourcecode:: http

      HTTP 200 OK
      Vary: Accept
      Content-Type: application/json
      Count: 379

      {
        "hits": [
          {
            "_type": "series",
            "_source": {
              "name": "Foo bar",
              "start_date": "1932-07-18T00:00:00",
              "end_date": "1944-12-31T00:00:00",
              "reference_code": "H II",
              "desc": "A description of foo bar"
            },
            "_score": 0.7205324,
            "_index": "component",
            "highlight": {
              "name": [
                "Foo <strong>bar</strong"
              ]
            },
            "_id": "AV-mEw9KtKryYoefnsRN"
          },
          {
            "_type": "volume",
            "_source": {
              "name": "Foo bar, vol 1",
              "start_date": "1932-07-18T00:00:00",
              "end_date": "1944-12-31T00:00:00",
              "reference_code": "H II I",
              "desc": "A description of foo bar vol 1"
            },
            "_score": 0.7205987,
            "_index": "component",
            "highlight": {
              "name": [
                "Foo <strong>bar</strong"
              ]
            },
            "_id": "AV-mEw9KtKryYoefnsRO"
          }
        ],
        "aggregations": {
          "_filter_type": {
            "type": {
              "buckets": [
                {
                  "key": "series",
                  "doc_count": 1
                },
                {
                  "key": "volume",
                  "doc_count": 1
                }
              ],
              "sum_other_doc_count": 0,
              "doc_count_error_upper_bound": 0
            },
            "doc_count": 2
          },
          "_filter_parents": {
            "parents": {
              "buckets": [],
              "sum_other_doc_count": 0,
              "doc_count_error_upper_bound": 0
            },
            "doc_count": 2
          }
        }
      }

.. http:get:: /search/(uuid:node)/

   Returns data about a single node

   :status 404: the node does not exist

.. http:get:: /search/(uuid:node)/children/

   Fetches the children of the node

   :status 404: the node does not exist

.. http:get:: /search/(uuid:node)/child-by-value/

   Fetches a single child of `node` that matches the provided filter

   **Example request**:

   .. sourcecode:: http

      GET /search/ed835644-0845-4ada-91f4-e3fd66d581c4/child-by-value/?field=arkivobjekt_id.keyword&value=2018-0009:4

   **Example response**:

   .. sourcecode:: http

      HTTP 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "_type": "doc",
        "_source": {
          "name": "hmm",
          "parent": {
            "index": "archive",
            "id": "b351ca1f-0d27-483b-8f79-ede633f3c4c7"
          },
          "reference_code": "1",
          "current_version": true,
          "type": "hmm",
          "archive": "b351ca1f-0d27-483b-8f79-ede633f3c4c7"
        },
        "_score": 2.672456,
        "_index": "component-20180912081120",
        "highlight": {
          "name": [
            "<strong>hmm</strong>"
          ]
        },
        "_id": "b19fc857-689a-4eaf-a88c-751d1258e9be"
      }

   :query string field: The field to filter against
   :query string value: The value to filter against

   :status 400: incorrect input or more than one match
   :status 404: the node does not exist

.. http:post:: /search/(uuid:node)/send-as-email/

   Sends the node in an email to the logged in user using the configured email
   backend. If the node describes a file, the file is included as an
   attachment.

   :status 400: the user doesn't have an email address
   :status 404: the node does not exist

.. http:post:: /search/mass-email/

   Sends the selected nodes in an email to the logged in user using the configured email
   backend. If a node describes a file, the file is included as an
   attachment.

   :param [uuid] ids: The ids of the nodes to include

   :status 400: the user doesn't have an email address or the ids parameter is
   invalid
   :status 404: a node does not exist

.. http:post:: /search/(uuid:node)/new-version/

   Creates a new version of the node

   :status 404: the node does not exist

.. http:post:: /search/(uuid:node)/set-as-current-version/

   Sets this node version as the current version of itself

   :status 404: the node does not exist

.. http:post:: /search/(uuid:node)/change-organization/

   Changes the organization of the node. This can only be done for ``archive``
   nodes.

   :param int organization: The id of the new organization

   :status 400: the organization parameter is invalid or missing
   :status 404: the node does not exist

.. http:post:: /search/

   Creates a new node

   :param string index: The index to create the node in. Must be "archive" or "component"
   :param string name: The name of the node
   :param string type: The type of the node, e.g. "Ärende", "Handling" or "Volym"
   :param string reference_code: The reference_code of the node
   :param uuid structure (optional): The classification structure to place the node in. Required for archives.
   :param uuid parent (optional): The classification structure to place the node in. Required for non-archives nodes

   :status 201: the organization parameter is invalid or missing

.. http:delete:: /search/(uuid:node)/

   Deletes a node

   :status 204: the node was deleted
   :status 404: the node does not exist

.. _max_result_window: https://www.elastic.co/guide/en/elasticsearch/reference/6.3/index-modules.html#dynamic-index-settings
