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
    import castorapi
    c = CastorApi("/path/to/folder/with/secret_client")
    c.select_study_by_name("<castor_name_of_your_study>")
    
    # export data - fast method for small studies.
    data = c.request_study_export_data() 
    
    # export data - slow method, but required for large studies with many records.
    # (or if you start getting a error 500)
    data = c.records_reports_all()

## NOTE
I am not affiliated with Castor EDC in any way. Use this software at your own risk.
