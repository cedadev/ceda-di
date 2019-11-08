Configuration File
==================

A sample JSON config file is provided in :download:`../../config/ceda_di.json`.
This contains all of the mandatory options, as well as a brief description of
the role of each option.

All options are described below in more detail if necessary.

**Note:** The default configuration will work for most use-cases - all that most
users will need to change are the Elasticsearch options and the file paths.


Options
-------

.. option:: es-host [url]

    The master Elasticsearch node of the Elasticsearch cluster used.
    In the example configuration file, this is set to "https://jasmin-es1.ceda.ac.uk".
    Use full url including protocol and port if not 80 or 443.

.. option:: es-port [port] DEPRECATED

    The port that the Elasticsearch installation is running on.
    In the example configuration file, this is set to 9200.

.. option:: es-index [index name]

    The name of the Elasticsearch index to store extracted metadata in.
    In the example configuration file, this is set to "badc".

.. option:: es-mapping [mapping name]

    **Note:** This is an advanced option for Elasticsearch. The defaults provided
    in ``ceda-di`` should be appropriate for most uses.

    The name of the Elasticsearch mapping.
    An Elasticsearch mapping exists so that Elasticsearch can infer data types
    from data stored in the index. This enables Elasticsearch to search across
    date/timestamps, do autocompletion on text fields, provide full-text search
    across all text data, and so on.

    In the example configuration file, the default mapping name is "eufar".
    The default mapping "eufar" is provided in :download:`../../../elasticsearch/mapping/index_settings.json`

.. option:: es-index-settings [path to index settings]

    **Note:** This is an advanced option for Elasticsearch. The defaults provided
    in ``ceda-di`` should be appropriate for most uses.

    The path to the settings JSON file for the Elasticsearch index.
    This includes any custom analyzers, tokenizers and so on.

    The default index settings are provided in :download:`../../../elasticsearch/mapping/index_settings.json`

    For further reference, please read `the Elasticsearch docs <http://www.elasticsearch.org/guide/en/elasticsearch/reference/1.3/index.html>`_.

.. option:: max-results [number of results]

    The maximum number of results to return per search request.

.. option:: output-path [output directory]

    The directory to place all output files (JSON, log files, etc).

.. option:: log-path [log directory]

    The directory (as a subdirectory of `output-path`) to place all log files in.

.. option:: json-path [JSON directory]

    The directory (as a subdirectory of `output-path` to place all JSON output in.
    
.. option:: input-path [input directory]

    The directory to scan for files and extract metadata from.

.. option:: num-cores [number of cores]

    The number of processes to run in parallel to extract metadata. Usually
    best suited to 1-2 processors below the number of cores in your machine.

    For example, if `di extract` is run on a machine with 24 cores, it's best
    to set `num-cores` to between 20 and 22.

.. option:: logging [object containing logging info]

    Options for the Python `logging` module.
    The default options will log to a file with the format specified in the
    configuration file. This is mostly for development and should not be edited.

.. option:: handlers [object containing file handlers]

    An object containing filename pattern regular expressions as keys, and a
    handler class and priority as values.

    For example, if I have a class to handle JPEG files in the ``ceda_di.JPEG``
    namespace, and I want to process metadata from all files ending with `.jpg`,
    I would write a configuration option like this:

    .. code-block:: javascript

        "handlers": {
            "\.jpg$": {
                "class": "ceda_di.JPEG",
                "priority": 1
            }
        }

    And this would allow ``ceda_di`` to recognise all JPG files and extract
    metadata from them.
