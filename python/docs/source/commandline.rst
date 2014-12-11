Command-Line Interface
======================

Introduction
------------

``ceda-di``'s command-line interface provides a simple way of accessing the
basic functionality included in the ``ceda-di`` toolkit. The basic functions
accessible through the CLI are:

* Indexing JSON files stored on disk into an Elasticsearch deployment
* Extracting metadata from scientific data files, and:
    * Writing out the metadata as JSON files, and/or
    * Indexing into an Elasticsearch deployment
* Searching an Elasticsearch deployment populated with metadata, including:
    * Time/date ranges,
    * Geographical extent (geospatial search),
    * Full-text search over variables,
    * etc


Command-line Configuration Options
----------------------------------

.. option:: --config [path-to-config]

    The file path to the configuration file for ``ceda-di``. This defaults to
    the configuration file provided in the ``ceda-di`` repository (which
    should contain sensible defaults), but you may want to create your own
    customised configuration.

.. option:: --host [elasticsearch-host]

    The network path of your preferred Elasticsearch installation. This is
    where extracted JSON metadata will be stored and indexed if specified on
    the command-line.

.. option:: --port [elasticsearch-port]

    The port that your Elasticsearch service runs on. On **most** Elasticsearch
    installations this defaults to ``9200`` if you are unsure, try that
    first.

.. option:: --index [elasticsearch-index]

    This option specifies the Elasticsearch index to use when storing data.
    If it does not exist in the Elasticsearch installation at runtime, it will
    be created with the default settings specified in the :doc:`configuration`.

.. option:: --max-results [num]

    This option defines the maximum number of results available per search
    request by default. When providing search parameters and an Elasticsearch
    index, this option will restrict the size of the reply.


Optional Command-line Parameters
--------------------------------

.. option:: --send-to-index

    This option tells ``ceda-di`` to send any extracted metadata to the user's
    preferred Elasticsearch deployment. Any data discovered and extracted will
    be indexed and searchable shortly afterwards.

.. option:: --no-create-files

    This option tells ``ceda-di`` **not** to create any JSON files on the local
    machine. This is useful for environments with restricted disk space (for
    example, on a cloud platform or a shared space).

.. option:: --help

    Shows the help text.

.. option:: --version

    Shows the version.


Command-line Tasks (Commands)
---------------------------------

.. option:: index [options] <path-to-json-docs>

    This command tells ``ceda-di`` to read and parses JSON documents in the 
    "path-to-json-docs" directory, and send them to the specified Elasticsearch
    index. Essentially, this command is a convenient way of pushing JSON
    documents into an Elasticsearch instance.

    The Elasticsearch instance's configuration can either be specified in the
    :doc:`configuration` or via the Elastisearch command-line options specified
    above.

.. option:: search [options] <extents>

    This command tells ``ceda-di`` to search the defined Elasticsearch instance
    with the provided parameters and return ``--max-results``-element long list
    of results.

    There are three simple modes of restricting your search, and the syntax is
    based on the `JASMIN_CIS <http://jasmin-cis.readthedocs.org/en/latest/colocation_examples.html>`_
    syntax.

    Latitude and longitude is restricted like so:
    
    .. code-block:: bash

        # Syntax:
        di.py search x[lower_bound, upper_bound] y[lower_bound, upper_bound]

        # For example, this is a valid command:
        di.py search x[1.1111, 2.2222] y[3.3333, 4.4444]

    
    It is also possible to restrict your search temporally, like so:

    .. code-block:: bash
    
        # Syntax
        di.py search t[lower_bound, upper_bound]

        # Please note that timestamps MUST be in ISO8601 format.
        # For example, this is a valid command:
        di.py search t[2008-01-01, 2012-05-05]

.. option:: extract [options] <paths>

    This command is a little hard to describe with a paragraph of text, so read
    the provided examples below first.

    .. code-block:: bash

        # Extract metadata from <input-path>
        # Don't create any files on disk
        # Send all metadata to the Elasticsearch index
        di.py extract --no-create-files --send-to-index <input-path>

        # Extract metadata from <input-path>
        # Create JSON files on disk in <output-path>
        # Send all metadata to the Elasticsearch index
        di.py extract --send-to-index <input-path> <output-path>

        # Extract metadata from <input-path>
        # Create JSON files on disk in <output-path>
        # Don't send to index (note the absence of the `--send-to-index``option
        di.py extract <input-path> <output-path>

    Looking at the examples above, it is obvious that there are three options:
        * Send metadata to Elasticsearch (--send-to-index)
        * **Don't** create files locally (--no-create-files)
        * Or both

    ``ceda-di`` **will not** send metadata to Elasticsearch by default, but
    it **will** create JSON files locally by default.


Module Contents
================

.. toctree::
    modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
