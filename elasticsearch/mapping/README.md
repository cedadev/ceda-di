# Elasticsearch Mapping/Schema Guide

This is the corresponding documentation for the Elasticsearch schema used in
`ceda-di`. "Schema" is actually sort of the wrong word - it's really a JSON
document describing the settings and data types used in a particular
Elasticsearch *index*.

"But what's an Elasticsearch index?" I hear you cry. Well, it's difficult to
explain but it's sort of analogous to a database in a relational database
architecture. Each index has a set of associated *mappings* - and mappings are
sort of analogous-to-tables-but-not-quite. Each mapping contains a set of
fields that each have an associated data type. Usually Elasticsearch can guess
the data type automatically, but sometimes you'll want to define these data
types yourself - in case you want things done in a certain way.

If you want to get more familiar with the terminology and basic concepts,
there are some great resources online - particularly [this blog post][1] and
the official [Elasticsearch documentation on the index API][2].

So, what's this schema used for? Well, you send the schema to Elasticsearch
when you want to create a new index. So if I want to create a new index
containing EUFAR data, I just send a simple request to the Elasticsearch API
and attach this schema as a payload. Elasticsearch then creates the index with
the relevant settings (using the schema as a template), and let you know when
it's done.

[1]: https://www.elastic.co/blog/what-is-an-elasticsearch-index
[2]: https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html


## The "settings" Section

This section defines the settings for the index. There isn't much to say about
this object other than that it's necessary as part of the structure of the
document.


### "analysis"

This section describes the index's analysis settings. "Analysis" refers to the
pre-processing steps that data goes through when being indexed into
Elasticsearch. For more information, look at the [Elasticsearch documentation
on Analysis][3].

[3]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html


#### "filter"

This defines the pre-processing filters to apply to the data when it is being
indexed into Elasticsearch. The filtering stage can encompass several steps,
including filtering out irrelevant entries, performing transformations on the
data, and so on. Read the [relevant Elasticsearch documentation][4] to get a
better understanding of the analysis stage.

[4]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html


##### "min\_length\_5\_filter"

This is a basic index filter constructed using Elasticsearch's filter
definition syntax that rejects any data fields that are under 5 characters in
length.

This index filter is constructed using the [length token filter][5], and it's
mostly used to filter out short and invalid parameter name entries.

[5]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-length-tokenfilter.html


##### "path\_filter"

This is another fairly straightforward filter. It's designed to split file
paths and index the separate parts of the path as different tokens. It's built
from a [word\_delimiter][6]

[6]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-word-delimiter-tokenfilter.html


#### "analyzer"

This section describes the analyzers used in the analysis stage of the
indexing process. These are mostly constructed using the filters defined in
the "filter" section above. Basically, the analyzers define how each document
is split up and parsed before being put into the search index.

The Elasticsearch documentation on [analyzers][7] is helpful when learning
about how terms can be parsed.

[7]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-analyzers.html


##### "variable\_name\_analyzer"

This analyzer uses the `min\_length\_5\_filter` defined above to ignore any
terms with fewer than 5 characters. It uses the built-in [keyword
tokenizer][8] to analyze and parse terms. The keyword tokenizer basically
indexes the entire input as a single entry - which makes it useful for, say,
cf-standard names.

[8]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-keyword-tokenizer.html


##### "path\_hierarchy\_analyzer"

This is just a simple analyzer built on top of Elasticsearch's built-in
[path\_hierarchy tokenizer][9]. This splits a file path based on each
delimiting character (in the case of Unix operating systems, a `/` character),
and indexes each level of the path as a token.

[9]: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-pathhierarchy-tokenizer.html


##### "path\_analyzer"

This is a simple analyzer built using a "standard analyzer" and the custom
`path\_filter` filter defined above to split a file path into separate tokens
and analyze them separately.


## "mappings"

This section defines the mappings and their associated data types. Sort of
like a database schema, but not quite. Read the Elasticsearch [documentation
on mappings][10] for more information on how mappings work and what they do.

[10]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html


### "geo\_metadata"

This section contains the data types for the `geo\_metadata` mapping.


#### "\_all"

This is a useful catch-all field in Elasticsearch that acts as a pointer to
all other text fields in a document - i.e. you can search the `\_all` field
for a term and it will search all text fields in the document.

The [Elasticsearch documentation has some useful information on the `_all`
field][11].

[11]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-all-field.html


#### "\_id"

This field acts in a similar manner to a primary key in a relational database.
The `\_id` field is just a unique identifier for each individual record. In
the context of `ceda\_di`, each document's ID is simply the SHA-1 hash of the
full file path - as that is guaranteed to be unique.


#### "properties"

This object describes the other structured data types within each document.


##### "data\_format"

A raw string containing the format of the data - for example, "NASA Ames".


##### "index\_entry\_creation"

This is a raw string used to record the application that created the metadata
record. In the case of `ceda\_di`, it would just be the string "ceda\_di".


##### "file"

An object recording file-level metadata.


###### "filename"

A string containing the file name (similar to the output of the `basename`
command).


###### "path"

A string containing the full file path, indexed with the `path\_analyzer`
defined above.


###### "path.hierarchy"

A version of the file path that's been tokenised with the
`path\_hierarchy\_analyzer` - it generates a full hierarchy for each file
path.


##### "misc"

A placeholder object for all miscellaneous metadata.


##### "parameters"

This field is fairly complex - it's a list of Elasticsearch [nested
documents[][12] which contain key/value pairs of "name" and "value" for each
individual parameter in the data files.

[12]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-nested-type.html


###### "parameters.name"

The variable name type, analyzed with the `variable\_name\_analyzer` from above.
Usually contains standard values like "long\_name", "standard\_name", etc.


###### "parameters.value"

The variable value (e.g. "surface\_temperature\_downwelling") indexed as a
single term.

This is a fairly complex data type, as it is analyzed multiple times for
different purposes. It's worth reading the Elasticsearch documentation on the
[multi\_field][13] data type, as it describes the role of this field really
well.

There is a sub-field called "autocomplete", which contains a data type that's
useful for... autocompletions! This field allows you to link up typeahead UI
elements with the Elasticsearch indices - which allows you to get as-you-type
autocompletion on parameter values.

[13]: https://www.elastic.co/guide/en/elasticsearch/reference/current/_multi_fields.html


##### "spatial"

This section also contains two separate fields - both analyze the geospatial
data slightly differently.


###### "geometries"

This is a special Elasticsearch type (the [geo\_shape][14] type) that takes
GeoJSON and allows for geospatial search. Essentially you can do rudimentary
operations on geospatial data such as seeing if two polygons overlap, whether
a point lies within a particular bounding box, and so on. It's worth reading
the [Elasticsearch documentation][14] on the topic.

[14]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-geo-shape-type.html


###### "display"

This is a fairly straightforward type - essentially just directly storing the
GeoJSON data in the index for fast retrieval. This is useful for interfacing
with online mapping services, or anythign else that can plot GeoJSON directly.


##### "temporal"

This stores temporal data for a data file - but just the start and end times,
meaning that time-correlated data isn't currently supported.


###### "start\_time" and "end\_time"

Both of these fields are Elasticsearch ["date" fields][15], which take ISO
8601 datetimestamps and index them in a clever way to make them searchable in
an efficient manner.

[15]: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-core-types.html#date
