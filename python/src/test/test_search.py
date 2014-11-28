import copy
import unittest
from elasticsearch import ConnectionError
from hamcrest import assert_that, is_, not_
from mock import MagicMock
import sys
from ceda_di.search import Searcher, JsonQueryBuilder


class TestJsonQueryBuilder(unittest.TestCase):
    """
    Test the ceda_di.search.JsonQueryBuilder class
    """

    def test_GIVEN_valid_temporal_extents_string_WHEN_build_THEN_correct_JSON_returned(self):
        query_builder = JsonQueryBuilder()
        start = "2010-04-19T13:39:54"
        end = "2010-04-19T15:12:40"
        query_string = "t=[%s,%s]" % (start, end)
        query = query_builder.build(query_string)
        assert_that(query, is_({
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [{
                                "range": {
                                    "eufar.temporal.start_time": {
                                        "lte": end
                                    }
                                }
                            }, {
                                "range": {
                                    "eufar.temporal.end_time": {
                                        "gte": start
                                    }
                                }
                            }],
                            "should": [],
                            "must_not": []
                        }
                    }
                }
            },
            "size": 10
        }))

    def test_GIVEN_extents_are_None_WHEN_build_THEN_correct_JSON_returned(self):
        query_builder = JsonQueryBuilder()
        query_string = None
        query = query_builder.build(query_string)
        assert_that(query, is_({
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [],
                            "should": [],
                            "must_not": []
                        }
                    }
                }
            },
            "size": 10
        }))

    def test_GIVEN_invalid_timestamp_WHEN_build_THEN_ValueError_raised(self):
        query_builder = JsonQueryBuilder()
        start = "2010/04/191 233:39:54"
        end = "2010-04-19T15:12:40"
        query_string = "t=[%s,%s]" % (start, end)
        with self.assertRaises(ValueError):
            query_builder.build(query_string)

    def test_GIVEN_two_partial_timestamps_WHEN_build_THEN_stamps_given_start_end_defaults(self):
        query_builder = JsonQueryBuilder()
        start = "2009"
        end = "2010"
        query_string = "t=[%s,%s]" % (start, end)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        assert_that(must[0]['range']['eufar.temporal.start_time']['lte'], is_('2010-12-31T23:59:59'))
        assert_that(must[1]['range']['eufar.temporal.end_time']['gte'], is_('2009-01-01T00:00:00'))

    def test_GIVEN_one_partial_timestamp_WHEN_build_THEN_start_and_end_timestamps_are_extremes_in_range(self):
        query_builder = JsonQueryBuilder()
        date = "2009"
        query_string = "t=[%s]" % date
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        assert_that(must[0]['range']['eufar.temporal.start_time']['lte'], is_('2009-12-31T23:59:59'))
        assert_that(must[1]['range']['eufar.temporal.end_time']['gte'], is_('2009-01-01T00:00:00'))

    def test_GIVEN_non_iso_timestamp_WHEN_build_THEN_raises_ValueError(self):
        query_builder = JsonQueryBuilder()
        start = "2010/04/19 23:39:54"
        end = "2010/04/19 15:12:40"
        query_string = "t=[%s,%s]" % (start, end)
        with self.assertRaises(ValueError):
            query_builder.build(query_string)

    def test_GIVEN_lat_range_WHEN_build_THEN_lat_bounds_in_json(self):
        query_builder = JsonQueryBuilder()
        ymin, ymax = 40, 60
        query_string = "y=[%s,%s]" % (ymin, ymax)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[-180, ymax], [180, ymin]]))

    def test_GIVEN_single_lat_WHEN_build_THEN_lat_bounds_in_json(self):
        query_builder = JsonQueryBuilder()
        lat = 55
        query_string = "y=[%s]" % lat
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[-180, lat], [180, lat]]))

    def test_GIVEN_invalid_lat_WHEN_build_THEN_raises_ValueError(self):
        query_builder = JsonQueryBuilder()
        query_string = "y=[51N, 55N]"
        with self.assertRaises(ValueError):
            query_builder.build(query_string)

    def test_GIVEN_lat_out_of_range_WHEN_build_THEN_raises_ValueError(self):
        query_builder = JsonQueryBuilder()
        query_string = "y=[100]"
        with self.assertRaises(ValueError):
            query_builder.build(query_string)
        query_string = "y=[-91]"
        with self.assertRaises(ValueError):
            query_builder.build(query_string)

    def test_GIVEN_lon_range_WHEN_build_THEN_lon_bounds_in_json(self):
        query_builder = JsonQueryBuilder()
        xmin, xmax = -140, 160
        query_string = "x=[%s,%s]" % (xmin, xmax)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[xmin, 90], [xmax, -90]]))

    def test_GIVEN_single_lon_WHEN_build_THEN_lat_bounds_in_json(self):
        query_builder = JsonQueryBuilder()
        lon = 120
        query_string = "x=[%s]" % lon
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[lon, 90], [lon, -90]]))

    def test_GIVEN_invalid_lon_WHEN_build_THEN_ValueError(self):
        query_builder = JsonQueryBuilder()
        query_string = "x=[90E]"
        with self.assertRaises(ValueError):
            query_builder.build(query_string)

    def test_GIVEN_single_lon_less_than_minus_180_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        lon = -190
        query_string = "x=[%s]" % lon
        wrapped_lon = 170
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_lon, 90], [wrapped_lon, -90]]))

    def test_GIVEN_lon_range_less_than_minus_180_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        start, end = -190, 10
        wrapped_start, wrapped_end = 170, 10
        query_string = "x=[%s,%s]" % (start, end)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_start, 90], [wrapped_end, -90]]))

    def test_GIVEN_single_lon_greater_than_180_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        lon = 200
        wrapped_lon = -160
        query_string = "x=[%s]" % lon
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_lon, 90], [wrapped_lon, -90]]))

    def test_GIVEN_single_lon_greater_than_360_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        lon = 370
        wrapped_lon = 10
        query_string = "x=[%s]" % lon
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_lon, 90], [wrapped_lon, -90]]))

    def test_GIVEN_lon_range_greater_than_180_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        start, end = 0, 270
        wrapped_start, wrapped_end = 0, -90
        query_string = "x=[%s,%s]" % (start, end)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_start, 90], [wrapped_end, -90]]))

    def test_GIVEN_lon_range_greater_than_360_WHEN_build_THEN_wraps_around(self):
        query_builder = JsonQueryBuilder()
        start, end = - 150, 730
        wrapped_start, wrapped_end = -150, 10
        query_string = "x=[%s,%s]" % (start, end)
        query = query_builder.build(query_string)
        must = query['query']['filtered']['filter']['bool']['must']
        shape = must[0]['geo_shape']['eufar.spatial.geometries.bbox']['shape']
        assert_that(shape['type'], is_('envelope'))
        assert_that(shape['coordinates'], is_([[wrapped_start, 90], [wrapped_end, -90]]))


class TestSearcher(unittest.TestCase):
    """
    Test the ceda_di.search.Searcher class
    """

    def setUp(self):
        sys.stdout = MagicMock()  # Mock stdout so we can capture printed output

    results_template = {
        u'_shards': {u'successful': 5, u'failed': 0, u'total': 5},
        u'timed_out': False,
        u'took': 2,
        u'hits': {u'max_score': 1.0, u'total': 0, u'hits': []}
    }

    def test_GIVEN_results_found_WHEN_run_THEN_results_printed(self):
        results = self.make_two_results()
        client_factory = self.make_mock_client_factory(results)
        config = {'extents': "t=[2010-04-19T13:39:54,2010-04-19T15:12:40]"}
        searcher = Searcher(config, elastic_search_client_factory=client_factory)
        try:
            searcher.run()
        except SystemExit:
            pass
        assert_that(sys.stdout.write.call_count, is_(2 * 2))
        assert_that(sys.stdout.write.call_args_list[0][0][0], is_('/badc/eufar/data/projects/eyjafjallajokull/'
                                                                  'nerc_arsf/core-cloud-phy_arsf_dornier_20100419'
                                                                  '_v500_r0_arsf109bpart1-10.nc'))
        assert_that(sys.stdout.write.call_args_list[1][0][0], is_('\n'))
        assert_that(sys.stdout.write.call_args_list[2][0][0], is_('/badc/eufar/data/projects/eyjafjallajokull/'
                                                                  'nerc_arsf/core-cloud-phy_arsf_dornier_20100419'
                                                                  '_v500_r1_arsf109bpart1-10_densitymineraldust.nc'))
        assert_that(sys.stdout.write.call_args_list[3][0][0], is_('\n'))

    def test_GIVEN_results_found_WHEN_run_THEN_SystemExit_with_code_zero(self):
        results = self.make_two_results()
        client_factory = self.make_mock_client_factory(results)
        config = {'extents': "t=[2010-04-19T13:39:54,2010-04-19T15:12:40]"}
        searcher = Searcher(config, elastic_search_client_factory=client_factory)
        with self.assertRaises(SystemExit) as ex:
            searcher.run()
        assert_that(ex.exception.code, is_(0))

    def test_GIVEN_no_results_found_WHEN_run_THEN_nothing_printed(self):
        client_factory = self.make_mock_client_factory(self.results_template)
        config = {'extents': "t=[2010-04-19T13:39:54,2010-04-19T15:12:40]"}
        searcher = Searcher(config, elastic_search_client_factory=client_factory)
        try:
            searcher.run()
        except SystemExit:
            pass
        assert_that(sys.stdout.write.call_count, is_(0))

    def test_GIVEN_no_results_found_WHEN_run_THEN_SystemExit_with_code_zero(self):
        client_factory = self.make_mock_client_factory(self.results_template)
        config = {'extents': "t=[2010-04-19T13:39:54,2010-04-19T15:12:40]"}
        searcher = Searcher(config, elastic_search_client_factory=client_factory)
        with self.assertRaises(SystemExit) as ex:
            searcher.run()
        assert_that(ex.exception.code, is_(0))

    def test_GIVEN_connection_error_occurs_WHEN_run_THEN_SystemExit_with_non_zero_code(self):
        client_factory = self.make_mock_client_factory_with_bad_connection()
        config = {'extents': "t=[2010-04-19T13:39:54,2010-04-19T15:12:40]"}
        searcher = Searcher(config, elastic_search_client_factory=client_factory)
        with self.assertRaises(SystemExit) as ex:
            searcher.run()
        assert_that(ex.exception.code, not_(0))

    def make_mock_client_factory_with_bad_connection(self):
        es_client = MagicMock()
        es_client.search = MagicMock(side_effect=ConnectionError("Exception message"))
        client_factory = MagicMock()
        client_factory.get_client = MagicMock(return_value=es_client)
        return client_factory

    def make_mock_client_factory(self, results):
        es_client = MagicMock()
        es_client.search = MagicMock(return_value=results)
        client_factory = MagicMock()
        client_factory.get_client = MagicMock(return_value=es_client)
        return client_factory

    def make_two_results(self):
        results = copy.deepcopy(self.results_template)
        results['hits']['hits'].append({
            u'_id': u'8a0b3fbf45bb60996a21834db9ae16e0d5074d2a',
            u'_index': u'badc',
            u'_score': 1.0,
            u'_type': u'eufar',
            u'_source': {
                u'file': {
                    u'path': u'/badc/eufar/data/projects/eyjafjallajokull/nerc_arsf/'
                             u'core-cloud-phy_arsf_dornier_20100419_v500_r0_arsf109bpart1-10.nc'
                }
            }
        })
        results['hits']['hits'].append({
            u'_id': u'e8b819a11819d45835282971bac489baec7562b9',
            u'_index': u'badc',
            u'_score': 1.0,
            u'_type': u'eufar',
            u'_source': {
                u'file': {
                    u'path': u'/badc/eufar/data/projects/eyjafjallajokull/nerc_arsf/'
                             u'core-cloud-phy_arsf_dornier_20100419_v500_r1_arsf109bpart1-10_densitymineraldust.nc'
                }
            }
        })
        results['hits']['total'] = 2
        return results

if __name__ == '__main__':
    unittest.main()