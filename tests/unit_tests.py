import os
import unittest
import castorapi as ca


class TestCastorApi(unittest.TestCase):
    '''Testing the CastorApi'''

    # define variables that are linked to the castor test account being used
    studyid = 'B11B4404-00FF-44A4-9585-0D7D0BFE6955'
    userfullname = 'Wouter Potters'
    study_name = 'Castor API unit test study'
    patient_id = '110001'  # amcinstid patient

    # institute where records may be added
    testinstid = '4374EF5A-D446-4EEB-A662-72DF356A3E0A'
    # institute with 1 record only
    amcinstid = '90C6B59D-AB56-48D7-BBBF-F611F3094F77'

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
        studyid = self.c.select_study_by_name(self.study_name)
        self.assertEqual(studyid, self.studyid)

    def test_CastorApi_getUser(self):
        self.assertEqual(
            self.c.request_user()['_embedded']['user'][0]['full_name'],
            self.userfullname)

    def test_CastorApi_getInstitute(self):
        inst = self.c.request_institutes(
            study_id=self.studyid)
        self.assertEqual(inst[1]['id'], self.amcinstid)

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
                for d in ['Record Id', 'pat_birth_year', 'pat_height']]))

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
                for d in ['Record Id', 'pos_bp']]))

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
        self.c.select_study_by_name('test')
        # expect to find 0 results for test study with no entries
        self.assertEqual(self.c.request_statistics()['records']['institutes'][0]['record_count'],
                         1)

    def test_CastorApi_post(self):
        self.c.select_study_by_name(self.study_name)

        # get 1 patient record
        records = self.c.request_study_records(record_id=self.patient_id)

        # get current value of the field pat_height
        old_value = self.c.field_values_by_variable_name('pat_height', records=[records])  # age == dob

        # make sure the value is present
        self.assertTrue(old_value is not None)

        # change the value, taking into account the maximum and minimum value
        # for this field
        new_value = float(old_value[0]) + 1.
        if new_value > 200.:
            new_value = 100.

        # update the field using the updated value
        d = self.c.request_datapointcollection(
            request_type='study',
            record_id=records['id'],
            field_id='98BA8DDF-3E04-46A6-891A-0BDC555AE1A3',
            field_value=str(new_value),
            change_reason_specific='Testing post messages using api',
            confirmed_changes_specific=False,
            request_method='POST')
        # make sure the response gives a 201 success response
        self.assertTrue('success' in d)

        # export the value again
        new_value_validate = self.c.field_values_by_variable_name('pat_height', records=records)  # age == dob

        # and check that the value is equal to the intended value
        self.assertTrue(new_value_validate[0] == str(new_value))

    def test_CastorApi_create_duplicate_patient_should_fail(self):
        self.c.select_study_by_name(self.study_name)
        try:
            a = self.c.request_study_records(institute_id=self.testinstid,
                                             record_id='000011', ccr_patient_id=None,
                                             email_address=None, request_method='POST')
        except NameError:
            a = 'nameerror'
        self.assertTrue(a == 'nameerror')


if __name__ == '__main__':
    unittest.main(verbosity=2)
