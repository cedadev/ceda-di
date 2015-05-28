# Sample Elasticsearch Queries

## `sample_temporal_query.json`

A simple query using the built-in time bounding search options in
Elasticsearch. It uses a ["range" filter][1] wrapped inside "bool" and "must"
filters, searching on the field "temporal.start\_time".

The parameters "from" and "to" are used to denote the bounding dates for the
search. The fields listed in the "include" section of the search request are
the "temporal" and "file" fields - which contain the timestamps and file path
of the document respectively.

### Relevant documentation

[1]: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-range-filter.html


## `sample_geospatial_query.json`

Another fairly straightforward query using the built-in geospatial search
capability in Elasticsearch. It uses a "geo\_shape" filter ([see the
Elasticsearch documentation on the "geo\_shape" type][2]) to filter the
Elasticsearch results.

When the "size" and "from" parameters aren't specified in an Elasticsearch
query (like this one), Elasticsearch will default to returning the top 10
matching results.

There are also a number of other geospatial filters that may also fit your
purposes, like the ["geo\_distance" filter][3] and the
["geo\_bounding\_box"][4] filter.

### Relevant documentation

[2]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-geo-shape-type.html
[3]: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-geo-distance-filter.html
[4]: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-geo-bounding-box-filter.html


## `sample_parameter_text_search.json`

This is another simple query that searches the Elasticsearch indices based
upon the textual content in the data file's "parameter" fields. This will
search all of the available text fields in a given document for the
wild-carded phrase "alt\*". This will aggressively pattern-match any text
beginning with the sequence "alt".
