# castor-python
Python API client to fetch data from Castor EDC

### Usage
First, make sure that save the client and secret from your Castor account in seperate files (without line endings) in a private folder on your PC. Do not share these files with anyone.    

See also https://data.castoredc.com/api

### Example code
    from castor_api import Castor_api
    c = Castor_api('/path/to/folder/with/secret_client')
    
    studies = c.request_study() # get al list of studies
    c.select_study_by_name('castor_name_of_your_study')
    
    data = c.request_study_export_data() # export data
    data = c.records_reports_all() # export data method 2 (if you get a error 500, use this one)

### NOTE
I am not affiliated with Castor EDC in any way. Use this software at your own risk.

## TODO
- implement POST endpoints of the api
- add more documentation
