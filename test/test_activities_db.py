"""Test activities db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


import unittest
import logging

from test_db_base import TestDBBase
import GarminDB
import Fit
from import_garmin_activities import GarminActivitiesFitData, GarminTcxData, GarminJsonSummaryData, GarminJsonDetailsData
import garmin_db_config_manager as GarminDBConfigManager


root_logger = logging.getLogger()
root_logger.addHandler(logging.FileHandler('activities_db.log', 'w'))
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

do_single_import_tests = True


class TestActivitiesDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.garmin_act_db = GarminDB.ActivitiesDB(GarminDBConfigManager.get_db_params())
        table_dict = {
            'activities_table' : GarminDB.Activities,
            'activity_laps_table' : GarminDB.ActivityLaps,
            'activity_records_table' : GarminDB.ActivityRecords,
            'run_activities_table' : GarminDB.StepsActivities,
            'paddle_activities_table' : GarminDB.PaddleActivities,
            'cycle_activities_table' : GarminDB.CycleActivities,
            'elliptical_activities_table' : GarminDB.EllipticalActivities
        }
        super().setUpClass(cls.garmin_act_db, table_dict, {GarminDB.Activities : [GarminDB.Activities.name]})
        cls.test_db_params = GarminDBConfigManager.get_db_params(test_db=True)
        cls.test_mon_db = GarminDB.GarminDB(cls.test_db_params)
        cls.test_act_db = GarminDB.ActivitiesDB(cls.test_db_params)
        cls.measurement_system = Fit.field_enums.DisplayMeasure.statute

    def test_garmin_act_db_tables_exists(self):
        self.assertGreater(GarminDB.Activities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityLaps.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.ActivityRecords.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.StepsActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.PaddleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.CycleActivities.row_count(self.garmin_act_db), 0)
        self.assertGreater(GarminDB.EllipticalActivities.row_count(self.garmin_act_db), 0)

    def check_activities_fields(self, fields_list):
        self.check_not_none_cols(self.test_act_db, {GarminDB.Activities : fields_list})

    def __fit_file_import(self):
        gfd = GarminActivitiesFitData('test_files/fit/activity', latest=False, measurement_system=self.measurement_system, debug=2)
        self.gfd_file_count = gfd.file_count()
        if gfd.file_count() > 0:
            gfd.process_files(self.test_db_params)

    def fit_file_import(self):
        self.profile_function('fit_activities_import', self.__fit_file_import)
        self.check_db_tables_exists(self.test_mon_db, {'device_table' : GarminDB.Device})
        self.check_db_tables_exists(self.test_mon_db, {'file_table' : GarminDB.File, 'device_info_table' : GarminDB.DeviceInfo}, self.gfd_file_count)

    @unittest.skipIf(not do_single_import_tests, "Skipping single import test")
    def test_fit_file_import(self):
        self.fit_file_import()
        self.check_activities_fields([GarminDB.Activities.start_time, GarminDB.Activities.stop_time, GarminDB.Activities.elapsed_time])

    def tcx_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        gtd = GarminTcxData('test_files/tcx', latest=False, measurement_system=self.measurement_system, debug=2)
        if gtd.file_count() > 0:
            gtd.process_files(self.test_db_params)

    @unittest.skipIf(not do_single_import_tests, "Skipping single import test")
    def test_tcx_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.tcx_file_import()
        self.check_activities_fields([GarminDB.Activities.sport, GarminDB.Activities.laps])

    def summary_json_file_import(self):
        gjsd = GarminJsonSummaryData(self.test_db_params, 'test_files/json/activity/summary', latest=False, measurement_system=self.measurement_system, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()

    @unittest.skipIf(not do_single_import_tests, "Skipping single import test")
    def test_summary_json_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.summary_json_file_import()
        self.check_activities_fields([GarminDB.Activities.name, GarminDB.Activities.type, GarminDB.Activities.sport, GarminDB.Activities.sub_sport])

    def details_json_file_import(self, delete_db=True):
        gjsd = GarminJsonDetailsData(self.test_db_params, 'test_files/json/activity/details', latest=False, measurement_system=self.measurement_system, debug=2)
        if gjsd.file_count() > 0:
            gjsd.process()

    @unittest.skipIf(not do_single_import_tests, "Skipping single import test")
    def test_details_json_file_import(self):
        GarminDB.ActivitiesDB.delete_db(self.test_db_params)
        self.details_json_file_import()

    def test_file_import(self):
        root_logger.info("test_file_import: %r", self.test_db_params)
        self.summary_json_file_import()
        self.details_json_file_import()
        self.tcx_file_import()
        self.fit_file_import()


if __name__ == '__main__':
    unittest.main(verbosity=2)
