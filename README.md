# castorapi
Python API wrapper for Castor EDC to fetch data from you clinical study.

## Install
It is recommended to use anaconda.

Using conda and the conda-forge channel:

    conda install -c conda-forge castorapi

But, you can also install using pip (https://pypi.org/project/castorapi/):

    pip install castorapi

## Usage
First, make sure that save the client and secret from your Castor account in 
seperate *client* and *secret* files (without line endings) in a private 
folder on your PC. Do not share these files with anyone.    

See also https://data.castoredc.com/api and https://helpdesk.castoredc.com/article/124-application-programming-interface-api

## Example code
    import castorapi as ca
    c = ca.CastorApi('/path/to/folder/with/secret_client')
    c.select_study_by_name('<CASTOR_STUDY_NAME>') # all following commands use this study selection
    stats = c.request_statistics()
    print(stats)
    df_study, df_structure_study, df_report, df_structure_report, df_optiongroups_structure = c.records_reports_all()
    users_in_study = c.request_studyuser()
    print(users_in_study)
    
## NOTE
I am not affiliated with Castor EDC in any way. Use this software at your own risk.
