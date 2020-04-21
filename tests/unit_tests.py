import os
import unittest
import castorapi as ca


class TestCastorApi(unittest.TestCase):
    '''Testing the CastorApi'''

    # define variables that are linked to the castor test account being used
    studyid = '027D80CF-0E9C-44F2-B7C2-AC981BDD380E'
    userfullname = 'Test Account'
    testinstid = '08330FF3-D467-46DF-8AD4-C3321E1B5E03'

    def setUp(self):
        # this test is using dummy credentials for a fake study
        # with a fake account.
        # The secret and client id are stored in github secrets
        client_id = os.getenv('castor_clientid')
        client_secret = os.getenv('castor_secret')
        self.c = ca.CastorApi(client_id=client_id,
                              client_secret=client_secret)

    def test_CastorApiType(self):
        # This test checks if the type of CastorApi instance is correct
        self.assertTrue((type(self.c) is ca.CastorApi))

    def test_CastorApiSelectStudy(self):
        # Check if the test study can be selected
        studyid = self.c.select_study_by_name('test')
        self.assertEqual(studyid, self.studyid)

    def test_CastorApi_getUser(self):
        self.assertEqual(
            self.c.request_user()['_embedded']['user'][0]['full_name'],
            self.userfullname)

    def test_CastorApi_getInstitute(self):
        inst = self.c.request_institutes(
            study_id=self.studyid)
        self.assertEqual(inst[0]['id'], self.testinstid)

    def test_CastorApi_exportData(self):
        # select study
        self.c.request_study_export_structure(self.studyid)

        # first method for quickly exporting data
        # only works for small studies
        data = self.c.request_study_export_data()
        data_columns = ['Study ID', 'Record ID', 'Form Type',
                        'Form Instance ID', 'Form Instance Name',
                        'Field ID', 'Value', 'Date', 'User ID']
        self.assertTrue(all([d in data.columns.to_list()
                             for d in data_columns]))
        self.assertTrue(all([d in data_columns
                             for d in data.columns.to_list()]))

        # second method for exporting data
        data2 = self.c.records_reports_all()

        self.assertTrue(
            all([d in data2[0].columns.to_list()
                for d in ['Record Id', 'pat_height', 'base_dbp', 'his_cvd',
                          'base_hr', 'fu_bmi', 'ic_language', 'pat_birth_year',
                          'base_date', 'inc_ic', 'unscheduled', 'pat_race',
                          'inc_dx', 'inc_criteria', 'his_diabetes',
                          'his_family', 'fu_sbp', 'ic_main_version',
                          'ic_versions', 'his_smoke', 'inc_trials', 'ic_date',
                          'fu_dbp', 'base_sbp', 'fu_weight', 'pat_sex',
                          'fu_hr', 'fu_date', 'inc_age', 'base_bmi',
                          'base_weight', 'conc_med']]))

        self.assertTrue(
            all([d in data2[1].columns.to_list()
                for d in ['Study ID', 'Form Type', 'Form Collection ID',
                          'Form Collection Name', 'Form Collection Order',
                          'Form ID', 'Form Name', 'Form Order', 'Field ID',
                          'Field Variable Name', 'Field Label', 'Field Type',
                          'Field Order', 'Field Required',
                          'Calculation Template', 'Field Option Group']]))

        self.assertTrue(
            all([d in data2[2].columns.to_list()
                for d in ['Record Id', 'med_name', 'med_stop', 'med_start',
                          'med_units', 'med_dose']]))

        self.assertTrue(
            all([d in data2[3].columns.to_list()
                for d in ['Study ID', 'Form Type', 'Form Collection ID',
                          'Form Collection Name', 'Form Collection Order',
                          'Form ID', 'Form Name', 'Form Order', 'Field ID',
                          'Field Variable Name', 'Field Label', 'Field Type',
                          'Field Order', 'Field Required',
                          'Calculation Template', 'Field Option Group']]))

        self.assertTrue(
            all([d in data2[4].columns.to_list()
                for d in ['Study ID', 'Option Group Id', 'Option Group Name',
                          'Option Id', 'Option Name', 'Option Value']]))

    def test_CastorApi_statistics0(self):
        self.c.request_study_export_structure(self.studyid)
        # expect to find 0 results for test study with no entries
        self.assertEqual(self.c.request_statistics()['records']['total_count'],
                         0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
