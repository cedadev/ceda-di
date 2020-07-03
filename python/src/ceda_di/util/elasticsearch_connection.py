# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '03 Jul 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from ceda_elasticsearch_tools.elasticsearch import CEDAElasticsearchClient


def get_elasticsearch_client(**kwargs):
    return CEDAElasticsearchClient(**kwargs)