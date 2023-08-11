import io
import json
import os.path
import pandas as pd
import requests
import progressbar
import logging


def process_table(txt):
    f_handler = io.StringIO(txt)  # created to enable use of read_table
    data = pd.read_table(f_handler, sep=';', quotechar='\"', header=0,
                         dtype='str')
    f_handler.close()
    return data


class CastorApi:
    """CastorApi class
    USAGE:
    from castorapi import CastorApi
    c = CastorApi('/path/to/folder/with/secret_client')
    result = c.request('request type','additional options')

    NOTE:
    # DO NOT SAVE THE CASTOR CLIENT_ID & SECRET IN A PUBLIC SCRIPT OR PUBLIC
      FOLDER (i.e. github)
    # KEEP YOUR CASTOR LOGIN AND CASTOR SECRET secret!

    TODO: Only request endpoints are implemented. Add more if you like :)

    See also https://data.castoredc.com/api

    Author: Wouter Potters, Amsterdam UMC
    Date: March, 2020
    I am not affiliated with Castor EDC in any way
    """
    # FIXME: ADD POST METHODS and POST API ENDPOINTS
    # FIXME: ADD PATCH METHODS and PATCH API ENDPOINTS
    # FIXME: ENABLE MULTIPLE FIELD UPDATES FOR POST API ENDPOINTS

    # define URLs for API
    _base_url = 'https://data.castoredc.com'
    _token_path = '/oauth/token'
    _api_request_path = '/api'

    _token = None

    # make it more convenient for the user by saving the last used ID's within
    # the class instance
    __study_id_saved = None

    # set to True when debugging and limiting the # records fetched to 25
    # (for Castor_api.records_reports_all())
    debug_mode = False

    def __init__(self, folder_with_client_and_secret=None,
                 client_id=None,
                 client_secret=None):
        if folder_with_client_and_secret is not None:
            if os.path.isdir(folder_with_client_and_secret):
                # load client id & secret for current user from folder
                def find_file(name):
                    return [file for file in os.listdir(
                        folder_with_client_and_secret) if name in file][0]
                with open(os.path.join(folder_with_client_and_secret,
                                       find_file('client')), 'r') as file:
                    client_id = file.read().rstrip()
                with open(os.path.join(folder_with_client_and_secret,
                                       find_file('secret')), 'r') as file:
                    client_secret = file.read().rstrip()
        if client_id is not None and client_secret is not None:
            # using the client and secret, get an access token
            # this castor api token can usually be used for up to 18000
            # seconds, after which it stops working (and could theoretically
            # be refreshed, but this is not documented in the Castor api:
            # data.castoredc.com/api)
            response_token = requests.post(self._base_url+self._token_path,
                                           data={'client_id':
                                                 client_id,
                                                 'client_secret':
                                                     client_secret,
                                                 'grant_type':
                                                     'client_credentials'})
            rd = json.loads(response_token.text)
            # throw error if an error occurs.
            if 'error' in rd:
                raise NameError('error ' + rd['error'] + '\n'
                                + rd['error_description'])
            self._token = rd['access_token']
        else:
            raise NameError(
                'castor_api expects either 1 input argument; a folder with'
                + ' a \'secret\' and a \'client\' file containing the client '
                + 'and secret as defined in your castor profile on '
                + 'https://data.castoredc.com/. '
                + 'Or use these 2 input arguments: '
                + 'client_id and client_secret')

    def __request_get(self, request):
        assert(type(request) == str)
        request_uri = self._base_url + self._api_request_path + request
        try:
            response = requests.get(request_uri,
                                    headers={'Authorization': 'Bearer ' +
                                             self._token})
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.warning("Http Error:", errh)
            # 500: timeout when too much data is requested with export fnc
            # 404: data not available for request
        except requests.exceptions.ConnectionError as errc:
            logging.warning("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            logging.warning("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            logging.warning("Oops: Something Else", err)
        if response:
            return response
        else:
            raise NameError('error with api request (' +
                            request+'): ' + response.text)

    def __request_post(self, request, dict_body):
        assert(type(request) == str)
        assert(type(dict_body) == dict)
        request_uri = self._base_url + self._api_request_path + request
        try:
            response = requests.post(request_uri,
                                     headers={'Authorization': 'Bearer ' +
                                              self._token,
                                              'content-type': 'application/json'},
                                     data=json.dumps(dict_body))
            response.raise_for_status()
            if response.status_code == 201:
                logging.info('Field value successfully created')
            elif response.status_code == 400:
                raise NameError('Invalid input - '
                                + response.content)
            elif response.status_code == 401:
                raise NameError('The given Record or Field does not exist - '
                                + response.content)
            elif response.status_code == 422:
                raise NameError('Unprocessable entity - '
                                + response.content)
            else:
                raise NameError('Unexpected error - '
                                + response.content)
        except requests.exceptions.HTTPError as errh:
            logging.warning("Http Error:", errh)
            # 500: timeout when too much data is requested with export fnc
            # 404: data not available for request
        except requests.exceptions.ConnectionError as errc:
            logging.warning("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            logging.warning("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            logging.warning("Oops: Something Else", err)
        if response:
            return response
        else:
            raise NameError('error with api request (' + request +
                            ') and body (' + json.dumps(dict_body) + '): ' +
                            response.text)

    def __request_json_get(self, request):
        response = self.__request_get(request)
        rd = response.json()
        # pagination: sometimes multiple entries are found; combine these
        if 'page' in rd and '_embedded' in rd:
            rd2 = rd
            while rd2['page'] < rd2['page_count']:
                request_uri = rd2['_links']['next']['href']
                response = requests.get(request_uri,
                                        headers={'Authorization': 'Bearer ' +
                                                 self._token})
                rd2 = response.json()
                for key in rd2['_embedded'].keys():
                    rd['_embedded'][key] += \
                        rd2['_embedded'][key]
        return rd

    def __request_json_post(self, request, body):
        response = self.__request_post(request, body)
        rd = response.json()
        # pagination: sometimes multiple entries are found; combine these
        if 'page' in rd and '_embedded' in rd:
            raise NameError('Did not expect pagination for result of POST.')
            # rd2 = rd
            # while rd2['page'] < rd2['page_count']:
            #     request_uri = rd2['_links']['next']['href']
            #     response = requests.get(request_uri,
            #                             headers={'Authorization': 'Bearer ' +
            #                                      self._token})
            #     rd2 = response.json()
            #     for key in rd2['_embedded'].keys():
            #         rd['_embedded'][key] += \
            #             rd2['_embedded'][key]
        return rd

    def __study_id_saveload(self, study_id_input):
        # study_id is either set by the user or loaded from study_id_saved.
        # if it is (re)set by the user, it is saved again.
        if not study_id_input:  # loaded from class instance
            study_id_output = self.__study_id_saved
            if not study_id_output:
                raise NameError('study_id not set. Use \'select_study_by_na',
                                'me (study_name)\' or \'request_study(study_',
                                'id)\' to set the study_id')
        else:  # set by user
            study_id_output = study_id_input
            if self.__study_id_saved != study_id_output and \
                    type(study_id_output) == str:
                self.__study_id_saved = study_id_output
                logging.info('study_id \''+study_id_output +
                             '\' was saved in castor_api class instance')
        return study_id_output

    # %% country
    def request_country(self, country_id=None):
        # API docs seem incorrect for this endpoint.
        # The return type is not a HAIJSON object.
        if country_id:
            rd = self.__request_json_get('/country/'+country_id)
            return rd
        else:
            rd = self.__request_json_get('/country')
            if 'results' in rd:
                return rd['results']
            else:
                return rd

    # %% data-point-collection
    def request_datapointcollection(self, study_id=None, request_type='study',
                                    record_id=None, report_instance_id=None,
                                    survey_instance_id=None,
                                    survey_package_instance_id=None,
                                    field_id=None,
                                    field_value=None,
                                    instance_id=None,
                                    change_reason_specific=None,
                                    confirmed_changes_specific=False,
                                    request_method='GET'):
        # request_type: GET  -> get request
        #               POST -> post request, requires field_id and field_value
        study_id = self.__study_id_saveload(study_id)

        if request_method == 'POST':
            if field_id is not None and field_value is not None:
                body = {
                    'field_id': field_id,
                    'field_value': field_value
                }

            else:
                raise NameError('Use as least study_id, record_id, '
                                + 'field_id and field_value as inputs.')

        rd = None
        if request_type == 'study':
            if record_id:
                request_url = \
                    '/study/'+study_id +\
                    '/record/'+record_id +\
                    '/data-point-collection/study'

                if request_method == 'POST':
                    if change_reason_specific is not None:
                        body['change_reason'] = change_reason_specific

                    if confirmed_changes_specific is not None:
                        body['confirmed_changes'] = confirmed_changes_specific

                    body = {
                        'common': {
                            'change_reason': 'Update using API',
                            'confirmed_changes': True
                            },
                        'data': [body]
                    }

            else:
                raise Exception('Record ID required for endpoint \'study\'')

        elif request_type == 'report-instance':
            if record_id:
                if report_instance_id:
                    request_url = \
                        '/study/'+study_id +\
                        '/record/'+record_id +\
                        '/data-point-collection/report-instance/' +\
                        report_instance_id

                    if request_method == 'POST':
                        if change_reason_specific is not None:
                            body['change_reason'] = change_reason_specific

                        if confirmed_changes_specific is not None:
                            body['confirmed_changes'] = confirmed_changes_specific

                        body = {
                            'common': {
                                'change_reason': 'Update using API',
                                'confirmed_changes': True
                                },
                            'data': [body]
                        }
                else:
                    request_url = \
                        '/study/'+study_id +\
                        '/record/'+record_id +\
                        '/data-point-collection/report-instance'

            else:
                if report_instance_id:
                    request_url = \
                        '/study/'+study_id +\
                        '/data-point-collection/report-instance/' +\
                        report_instance_id
                else:
                    request_url = \
                        '/study/'+study_id +\
                        '/data-point-collection/report-instance'

        elif request_type == 'survey-instance':
            if record_id:
                if survey_instance_id:
                    request_url = \
                        '/study/'+study_id +\
                        '/record/'+record_id +\
                        '/data-point-collection/survey-instance'
                else:
                    request_url = \
                        '/study/'+study_id +\
                        '/record/'+record_id +\
                        '/data-point-collection/survey-instance/' +\
                        survey_instance_id

                    if request_method == 'POST':
                        if instance_id is not None:
                            body['instance_id'] = instance_id

                        body = {'data': [body]}

            else:
                if survey_instance_id:
                    request_url = \
                        '/study/'+study_id +\
                        '/data-point-collection/survey-instance'
                else:
                    request_url = \
                        '/study/'+study_id +\
                        '/data-point-collection' +\
                        '/survey-instance/'+survey_instance_id

        elif request_type == 'survey-package-instance':
            if survey_package_instance_id:
                if record_id:
                    request_url = \
                        '/study/'+study_id+'/record/'+record_id +\
                        '/data-point-collection/' +\
                        'survey-package-instance/'+survey_package_instance_id
                else:
                    request_url = \
                        '/study/'+study_id +\
                        '/data-point-collection' +\
                        '/survey-package-instance/' +\
                        survey_package_instance_id

        if request_method == 'GET':
            rd = self.__request_json_get(request_url)
        elif request_method == 'POST':
            rd = self.__request_json_post(request_url, body)

        if '_embedded' in rd and 'items' in rd['_embedded']:
            return rd['_embedded']['items']
        else:
            return rd

    # %% export
    def request_study_export_structure(self, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        response = self.__request_get('/study/'+study_id+'/export/structure')
        data = process_table(response.text)
        return data

    def request_study_export_data(self, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        response = self.__request_get('/study/'+study_id+'/export/data')
        data = process_table(response.text)
        return data

    def request_study_export_optiongroups(self, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        response = self.__request_get('/study/'+study_id+'/export/optiongroups')
        data = process_table(response.text)
        return data

    # %% field-optiongroup
    def request_fieldoptiongroup(self, study_id=None, optiongroup_id=None):
        study_id = self.__study_id_saveload(study_id)
        if optiongroup_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-optiongroup/'+optiongroup_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-optiongroup')

        if '_embedded' in rd and 'fieldOptionGroups' in \
                rd['_embedded']:
            return rd['_embedded']['fieldOptionGroups']
        else:
            return rd

    # %% field
    def request_field(self, study_id=None, field_id=None, include=None):
        """


        Parameters
        ----------
        study_id : TYPE, optional
            DESCRIPTION. The default is None.
        field_id : TYPE, optional
            DESCRIPTION. The default is None.
        include : TYPE, optional
            The extra properties to include in the Field array. Currently it
            supports "metadata","validations", "optiongroup", "dependencies".
            List separated by "|".  Use like: metadata|validations|optiongroup



        """
        study_id = self.__study_id_saveload(study_id)
        additional_args = ''
        if include:
            additional_args += '?include='+include
        if field_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field/'+field_id+additional_args)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field'+additional_args)

        if '_embedded' in rd and 'fields' in \
                rd['_embedded']:
            return rd['_embedded']['fields']
        else:
            return rd

    # %% field-dependency
    def request_fielddependency(self, study_id=None, fielddependency_id=None):
        study_id = self.__study_id_saveload(study_id)
        if fielddependency_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-dependency/'+fielddependency_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-dependency')

        if '_embedded' in rd and 'steps' in \
                rd['_embedded']:
            return rd['_embedded']['steps']
        else:
            return rd

    # %% field-validation
    def request_fieldvalidation(self, study_id=None, fieldvalidation_id=None):
        study_id = self.__study_id_saveload(study_id)
        if fieldvalidation_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-validation/'+fieldvalidation_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/field-validation')

        if '_embedded' in rd and 'fieldValidations' in \
                rd['_embedded']:
            return rd['_embedded']['fieldOptionGroups']
        else:
            return rd

    # %% institute
    def request_institutes(self, study_id=None, institute_id=None):
        study_id = self.__study_id_saveload(study_id)
        if institute_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/institute/'+institute_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/institute')

        if '_embedded' in rd and 'institutes' in \
                rd['_embedded']:
            return rd['_embedded']['institutes']
        else:
            return rd

    # %% metadata
    def request_metadata(self, study_id=None, metadata_id=None):
        study_id = self.__study_id_saveload(study_id)
        if metadata_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/metadata/'+metadata_id)
        else:
            rd = self.__request_json_get('/study/' + study_id +
                                         '/metadata')

        if '_embedded' in rd and 'steps' in \
                rd['_embedded']:
            return rd['_embedded']['steps']
        else:
            return rd

    # %% metadatatype
    def request_metadatatype(self, study_id=None, metadatatype_id=None):
        study_id = self.__study_id_saveload(study_id)
        if metadatatype_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/metadatatype/'+metadatatype_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/metadatatype')

        if '_embedded' in rd and 'steps' in \
                rd['_embedded']:
            return rd['_embedded']['steps']
        else:
            return rd

    # %% phase
    def request_phase(self, study_id=None, phase_id=None):
        study_id = self.__study_id_saveload(study_id)
        if phase_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/phase/'+phase_id)
        else:
            rd = self.__request_json_get('/study/' + study_id +
                                         '/phase')

        if '_embedded' in rd and 'phases' in \
                rd['_embedded']:
            return rd['_embedded']['phases']
        else:
            return rd

    # %% query
    def request_query(self, study_id=None, query_id=None):
        study_id = self.__study_id_saveload(study_id)
        if query_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/query/'+query_id)
        else:
            rd = self.__request_json_get('/study/' + study_id +
                                         '/query')

        if '_embedded' in rd and 'queries' in \
                rd['_embedded']:
            return rd['_embedded']['queries']
        else:
            return rd

    # %% record
    def request_study_records(self, study_id=None, archived=0,
                              institute_id=None, record_id=None,
                              ccr_patient_id=None, email_address=None,
                              request_method='GET'):
        study_id = self.__study_id_saveload(study_id)
        additional_parameters = '?archived='+str(archived)
        if institute_id:
            additional_parameters += '&institute='+str(institute_id)
        if record_id:
            record_id_param = '/'+record_id
        else:
            record_id_param = ''

        if request_method == 'GET':
            rd = self.__request_json_get('/study/'+study_id+'/record' +
                                         record_id_param +
                                         additional_parameters)
        elif request_method == 'POST':
            body_dict = {
                'institute_id': institute_id
                }

            if record_id is not None:
                body_dict['record_id'] = record_id

            if ccr_patient_id is not None:
                body_dict['ccr_patient_id'] = ccr_patient_id

            if email_address is not None:
                body_dict['email_address'] = email_address

            rd = self.__request_json_post('/study/'+study_id+'/record',
                                          body_dict)

        if '_embedded' in rd and 'records' in rd['_embedded']:
            rd = rd['_embedded']['records']
            return rd
        else:
            return rd

    # %% record-progress
    def request_recordprogress(self, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        rd = self.__request_json_get(
            '/study/'+study_id+'/record-progress/steps')

        if '_embedded' in rd and 'records' in \
                rd['_embedded']:
            return rd['_embedded']['records']
        else:
            return rd

    # %% report
    def request_report(self, study_id=None, report_id=None):
        study_id = self.__study_id_saveload(study_id)
        if report_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/report/'+report_id)
        else:
            rd = self.__request_json_get('/study/'+study_id+'/report')

        if '_embedded' in rd and 'reports' in \
                rd['_embedded']:
            return rd['_embedded']['reports']
        else:
            return rd

    # %% report-instance
    def request_reportinstance(self, study_id=None, record_id=None,
                               reportinstance_id=None):
        study_id = self.__study_id_saveload(study_id)
        if record_id:
            if reportinstance_id:
                rd = self.__request_json_get(
                    '/study/'+study_id+'/record/'+record_id +
                    '/report-instance/'+reportinstance_id)
            else:
                rd = self.__request_json_get(
                    '/study/'+study_id+'/record/'+record_id +
                    '/report-instance')
        else:
            if reportinstance_id:
                rd = self.__request_json_get(
                    '/study/'+study_id+'/report-instance/'+reportinstance_id)
            else:
                rd = self.__request_json_get(
                    '/study/'+study_id+'/report-instance')

        if '_embedded' in rd and 'reportInstances' in \
                rd['_embedded']:
            return rd['_embedded']['reportInstances']
        else:
            return rd

    # %% report-data-entry
    def request_reportdataentry(self, study_id=None, record_id=None,
                                reportinstance_id=None, field_id=None,
                                validations='0'):
        study_id = self.__study_id_saveload(study_id)
        if not record_id:
            raise NameError('Provide a record_id for request_reportdataentry')
        if not reportinstance_id:
            raise NameError(
                'Provide a reportinstance_id for request_reportdataentry')

        if field_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/data-point/' +
                'report/'+reportinstance_id+'/'+field_id +
                '?validations='+validations)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/data-point/report' +
                '?validations='+validations)

        if '_embedded' in rd and 'ReportDataPoints' in \
                rd['_embedded']:
            return rd['_embedded']['ReportDataPoints']
        else:
            return rd

    # %% report-step
    def request_reportstep(self, study_id=None, report_id=None,
                           reportstep_id=None):
        study_id = self.__study_id_saveload(study_id)
        if not report_id:
            raise NameError('Provide a report_id for request_reportstep')
        if reportstep_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/report/'+report_id+'/report-step/' +
                reportstep_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/report/'+report_id+'/report-step/')

        if '_embedded' in rd and 'report_steps' in \
                rd['_embedded']:
            return rd['_embedded']['report_steps']
        else:
            return rd

    # %% step
    def request_step(self, study_id=None, step_id=None):
        study_id = self.__study_id_saveload(study_id)
        if step_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/step/'+step_id)
        else:
            rd = self.__request_json_get('/study/'+study_id+'/step')

        if '_embedded' in rd and 'steps' in \
                rd['_embedded']:
            return rd['_embedded']['steps']
        else:
            return rd

    # %% study
    def request_study(self, study_id=None):
        """


        Parameters
        ----------
        study_id : STR, optional
            Study_ID from Castor EDC. When STR is provided, only 1 study is
            selected.

        Returns
        -------
        Dict
            containing study information for 1 or more studies.

        NOTE: 'request_study' stores latest study_id in class instance
        variable study_id_saved. If only 1 study_id was selected, this is
        saved as study_id for future function calls of the class instance.
        -------


        """
        if study_id:
            rd = self.__request_json_get('/study/'+study_id)
        else:
            rd = self.__request_json_get('/study')
        if '_embedded' in rd and 'study' in rd['_embedded']:
            studies = rd['_embedded']['study']
            if len(studies) == 1 and 'study_id' in studies[0]:
                self.__study_id_saveload(studies[0]['study_id'])
            return rd['_embedded']['study']
        else:
            self.__study_id_saveload(rd['study_id'])
            return rd

    def request_studyuser(self, study_id=None, user_id=None):
        study_id = self.__study_id_saveload(study_id)
        # API docs seem incorrect for this endpoint.
        # The return type is not a HAIJSON object...
        if user_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/user/'+user_id)
        else:
            rd = self.__request_json_get('/study/'+study_id+'/user')
        return rd

    # %% study-data-entry - naming is weird; make 2 functions to avoid issues
    def request_studydatapoints(self, study_id=None, record_id=None,
                                field_id=None, validations='0'):
        return self.request_studydataentry(study_id=study_id,
                                           record_id=record_id,
                                           field_id=field_id,
                                           validations=validations)

    def request_studydataentry(self, study_id=None, record_id=None,
                               field_id=None, validations='0'):
        study_id = self.__study_id_saveload(study_id)
        if not record_id:
            raise NameError('Provide a record_id for request_studydataentry')
        if field_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/study-data-point/' +
                field_id+'?validations='+validations)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/data-point/study' +
                '?validations='+validations)
        if '_embedded' in rd and 'StudyDataPoints' in rd['_embedded']:
            return rd['_embedded']['StudyDataPoints']
        else:
            return rd

    # %% study-statistics
    def request_statistics(self, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        rd = self.__request_json_get('/study/'+study_id+'/statistics')
        return rd

    # %% survey
    def request_survey(self, study_id=None, survey_id=None, include=None):
        study_id = self.__study_id_saveload(study_id)
        add_args = ''
        if include:
            add_args += '?' + include
        if survey_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/survey/'+survey_id+add_args)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/survey'+add_args)
        if '_embedded' in rd and 'surveys' in rd['_embedded']:
            return rd['_embedded']['surveys']
        else:
            return rd

    def request_surveypackage(self, study_id=None, surveypackage_id=None):
        study_id = self.__study_id_saveload(study_id)
        if surveypackage_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/surveypackage/'+surveypackage_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/surveypackage')
        if '_embedded' in rd and 'survey_packages' in rd['_embedded']:
            return rd['_embedded']['survey_packages']
        else:
            return rd

    def request_surveypackageinstance(self, study_id=None,
                                      surveypackageinstance_id=None,
                                      record_id=None, ccr_patient_id=None):
        study_id = self.__study_id_saveload(study_id)
        if record_id and ccr_patient_id:
            raise NameError('do not use record_id & ccr_patient_id together')
        add_args = ''
        if record_id:
            add_args += '?record_id=' + record_id
        if ccr_patient_id:
            add_args += '?ccr_patient_id=' + ccr_patient_id
        if surveypackageinstance_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/surveypackageinstance/' +
                surveypackageinstance_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/surveypackageinstance'+add_args)
        if '_embedded' in rd and 'surveypackageinstance' in rd['_embedded']:
            return rd['_embedded']['surveypackageinstance']
        else:
            return rd

    # %% survey-data-entry
    def request_surveydataentry(self, study_id=None, record_id=None,
                                survey_instance_id=None, field_id=None):
        study_id = self.__study_id_saveload(study_id)
        if not record_id:
            raise NameError('Provide a record_id for request_surveydataentry')
        if not survey_instance_id:
            raise NameError(
                'Provide a survey_instance_id for request_surveydataentry')
        if field_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/data-point/survey/' +
                survey_instance_id+'/'+field_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/record/'+record_id+'/data-point/survey/' +
                survey_instance_id+'')
        if '_embedded' in rd and 'SurveyDataPoints' in rd['_embedded']:
            return rd['_embedded']['SurveyDataPoints']
        else:
            return rd

    # %% survey-step
    def request_surveystep(self, study_id=None, survey_id=None,
                           surveystep_id=None):
        study_id = self.__study_id_saveload(study_id)
        if not survey_id:
            raise NameError('Provide a survey_id for request_surveystep')
        if surveystep_id:
            rd = self.__request_json_get(
                '/study/'+study_id+'/survey/'+survey_id +
                '/survey_step/'+surveystep_id)
        else:
            rd = self.__request_json_get(
                '/study/'+study_id+'/survey/'+survey_id+'/survey_step')
        if '_embedded' in rd and 'survey_steps' in rd['_embedded']:
            return rd['_embedded']['survey_steps']
        else:
            return rd

    # %% user
    def request_user(self, user_id=None):
        if user_id:
            rd = self.__request_json_get('/user/'+user_id)
        else:
            rd = self.__request_json_get('/user')
        if '_embedded' in rd and 'users' in rd['_embedded']:
            return rd['_embedded']['users']
        else:
            return rd

    # %% ADDITIONAL FUNCTIONS FOR CONVENIENCE
    def select_study_by_name(self, study_name_input=''):
        rd = self.request_study()
        study_id = [s['study_id'] for s in rd if str.lower(
            study_name_input) in str.lower(s['name'])]
        if len(study_id) == 1:
            self.__study_id_saveload(study_id[0])
            return study_id[0]
        elif len(study_id) == 0:
            logging.warning(str(len(study_id))+' studies found containing ' +
                            '\'' + study_name_input + '\' Try again using ' +
                            'a different query or check your castor study ' +
                            'access rights. These studies are available for' +
                            ' you:')
            [logging.warning(' > ' + r['name']) for r in rd]
        else:
            logging.warning(str(len(study_id))+' studies found containing ' +
                            '\'' + study_name_input + '\', try to specify ' +
                            'your query further.')
            [logging.warning(' > ' + s['name'])
             for s in rd if study_name_input in s['name']]
            return None

    def records_reports_all(self, study_id=None, report_names=[],
                            add_including_center=False, include_columns_without_data=False):
        study_id = self.__study_id_saveload(study_id)

        logging.info('Fetching all data from study id (' + study_id +
                     '). This takes some time... be patient.')

        # get study and report structure
        # sort on form collection order and field order
        # (this matches how data is filled)
        structure_filtered = self.request_study_export_structure() \
            .sort_values(['Form Order', 'Form Collection Name',
                          'Form Collection Order', 'Field Order'])

        structure_filtered = structure_filtered[~(
            structure_filtered['Field Variable Name'].isna())]
        df_structure_study = structure_filtered[
            structure_filtered['Form Type'].isin(['Study'])]
        df_structure_report = structure_filtered[
            structure_filtered['Form Type'].isin(['Report'])]

        # get option groups
        df_optiongroups_structure = pd.DataFrame(
            self.request_study_export_optiongroups())

        # GET ALL STUDY RECORDS
        records = self.request_study_records(study_id)

        if self.debug_mode:  # set to True when debugging.
            records = records[0:25]  # test data
            logging.warning('DEBUG MODE ACTIVE. ONLY PROCESSING ' +
                            str(len(records))+' RECORDS')

        # GET ALL STUDY AND REPORT VALUES FOR STUDY RECORDS - no data: None
        study_data = []
        report_data = []
        hospitals = {r['id']: r['_embedded']['institute']['name']
                     for r in records}
        for record in progressbar.progressbar(records,
                                              prefix='Retrieving records: '):
            study_data += self.request_datapointcollection(
                record_id=record['record_id'])
            report_data += self.request_datapointcollection(
                request_type='report-instance',
                record_id=record['record_id'])
        df_study = pd.pivot(pd.DataFrame(study_data),
                            values='field_value', index='record_id',
                            columns='field_id')
        if add_including_center:
            df_study['hospital'] = df_study.index
            df_study['hospital'] = df_study['hospital'].replace(hospitals)

        # field_id -> field_variable_name
        fields = self.request_field(include='optiongroup')
        field_dict = {f['field_id']: f['field_variable_name'] for f in fields}
        df_study.rename(columns=field_dict, inplace=True)

        # Some columns do not have any data entries; add them and fill them with NaN
        if include_columns_without_data:
            for nc in [f['field_variable_name'] for f in fields]:
                if nc not in df_study.columns:
                     df_study[nc] = float('nan')
                                
        df_study.reset_index(level=0, inplace=True)

        df_report = pd.DataFrame(report_data)
        if not df_report.empty:
            # aggfunc is ', '.join, but no duplicate entries are expected
            # when indexing on report_instance_id.
            df_report = pd.pivot_table(df_report,
                                       index=['record_id',
                                              'report_instance_id'],
                                       values='field_value',
                                       columns='field_id', aggfunc=', '.join)
            df_report.rename(columns=field_dict, inplace=True)
            df_report.reset_index(level=0, inplace=True)
        else:
            logging.warning('No reports found; df_report is empty.')

        # for some reason the names of some variables are different in the
        # export format, rename them
        rename_cols = {"study_id": "Study ID", "record_id": "Record Id",
                       "form_type": "Form Type", "form_instance id":
                       "Form Instance ID", "form_instance_name":
                       "Form Instance Name", "field_id": "Field ID",
                       "value": "Value", "date": "Date", "user_id": "User ID"}
        if not df_report.empty:
            df_report.rename(columns=rename_cols, inplace=True)
        df_study.rename(columns=rename_cols, inplace=True)

        # return data
        return df_study, df_structure_study, df_report, \
            df_structure_report, df_optiongroups_structure

    def field_optiongroup_by_variable_name(self, field_name, study_id=None):
        study_id = self.__study_id_saveload(study_id)
        fields = [f for f in self.request_field(
            include='optiongroup') if f['field_variable_name'] == field_name]
        if len(fields) == 1 and 'option_group' in fields[0]:
            field_optiongroup_id = fields[0]['option_group']['id']
            return field_optiongroup_id
        else:
            return None

    def __studydataentry_or_none(self, study_id=None, record_id=None,
                                 field_id=None):
        study_id = self.__study_id_saveload(study_id)
        try:
            field = self.request_studydataentry(
                study_id=study_id, record_id=record_id, field_id=field_id)
            if field['value'] and len(field['value']) > 0:
                value = field['value']
            else:
                value = None
        except NameError:
            value = None
        return value

    def field_values_by_variable_name(self, field_name, study_id=None,
                                      records=None):
        study_id = self.__study_id_saveload(study_id)

        # find field_id from field_name
        fields = [f for f in self.request_field(
        ) if f['field_variable_name'] == field_name]
        if fields:
            field_id = fields[0]['field_id']
        else:
            return None

        # collect or use input records
        if records is None:
            logging.warning(
                'no records provided, getting data for ALL records')
            records = self.request_study_records()

        if type(records) is str:
            records = [self.request_study_records(record_id=records)]

        if type(records) == dict:
            records = [records]

        # get value or set None if no data was found
        if records:
            assert(type(records) == list)
            field_values = [self.__studydataentry_or_none(
                record_id=record['record_id'], field_id=field_id)
                for record in records]
            return field_values
        else:
            return None


if __name__ == "__main__":
    print('\n# USAGE of CastorApi:\n')
    print('import castorapi as ca')
    print('c = ca.CastorApi(\'/path/to/folder/with/secret_client\')')
    print('c.select_study_by_name(\'<CASTOR_STUDY_NAME>\') # all ' +
          'following commands use this study selection')
    print('stats = c.request_statistics()')
    print('print(stats)')
    print('df_study, df_structure_study, df_report, df_structure_report, ' +
          'df_optiongroups_structure = c.records_reports_all()')
    print('users_in_study = c.request_studyuser()')
    print('print(users_in_study)')
    print('\n# See also: https://data.castoredc.com/api\n')
