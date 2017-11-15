================
 Search
================

.. contents::
    :local:

.. http:get:: /search/

    :param q: The search keywords
    :type q: string
    :param type: Restrict results to a single type (e.g. archive, volume, document)
    :type type: string
    :param start_date: Restrict results to a start date
    :type start_date: string of format YYYY[-MM-DD]
    :param end_date: Restrict results to an end date
    :type end_date: string of format YYYY[-MM-DD]
    :param page: page number
    :type page: integer
    :param page_size: number of results per page. Default: 10
    :type page_size: integer

    :status 200: When search is successful
    :status 400: when :code:`start_date > end_date` or when accessing objects
        outside of `max_result_window`_
    :status 404: when accessing an invalid :code:`page`

    **Example response**:

       .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json
          Count: 379

          {
            "hits": [
              {
                "_type": "series",
                "_source": {
                  "name": "Foo bar",
                  "end_date": "1900-12-31T00:00:00",
                  "reference_code": "H II",
                  "start_date": "1932-07-18T00:00:00",
                  "desc": "A description of foo bar"
                  },
                  "_score": 0.7205324,
                  "_index": "tags",
                  "highlight": {
                      "name": [
                          "Foo <strong>bar</strong"
                      ]
                  },
                  "_id": "AV-mEw9KtKryYoefnsRN"
                },
                ...
              ]
              "aggregations": {
                "_filter_type": {
                  "type": {
                    "buckets": [
                      {
                        "key": "series",
                        "doc_count": 51
                      },
                      {
                        "key": "volume",
                        "doc_count": 328
                      }
                    ],
                    "sum_other_doc_count": 0,
                    "doc_count_error_upper_bound": 0
                  },
                  "doc_count": 379
                },
                "_filter_parents": {
                  "parents": {
                    "buckets": [],
                    "sum_other_doc_count": 0,
                    "doc_count_error_upper_bound": 0
                  },
                  "doc_count": 379
                }
              }
            }

.. http:get:: /search/(tag_id)/

    Information about the tag with id :code:`tag_id`

    :status 200: when a tag with id :code:`tag_id` exists
    :status 404: when a tag with id :code:`tag_id` does not exist

.. http:get:: /search/(tag_id)/children/

    The tags related to :code:`tag_id`

    :param tree_id: the id of the tree that the children of tag (:code:`tag_id`) belong to
    :type tree_id: string

    :status 200: when a tag with id :code:`tag_id` exists
    :status 404: when a tag with id :code:`tag_id` does not exist

.. _max_result_window: https://www.elastic.co/guide/en/elasticsearch/reference/5.6/index-modules.html#dynamic-index-settings
