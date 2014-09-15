# Guide to This Directory

* "ansible" - Ansible playbook for deploying ElasticSearch on a (set of) RHEL machine(s).
* "mapping" - Index mapping for ElasticSearch, along with JSON schema for EUFAR metadata
* "sample-queries" - Sample queries for ElasticSearch containing the EUFAR metadata
    * Submit with ```curl -XPOST -d @sample_query_filename``` (the @ symbol tells CURL to get data from a file)
* "scripts" - Useful BASH scripts for various elasticsearch-related tasks (index creation, queries, etc)
