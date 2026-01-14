# Zebra AI Sample Python Client
# This sample client demonstrates how to use the Zebra AI API with MSAL and a broker
# Sample version 1.2.3.1

# make sure to install a broker
# pip install "msal[broker]>=1.20,<2"


import requests
import json
import logging
from msal import PublicClientApplication
from process_response import extract_all_questions

EXPERIMENT_ID = 'b36535ca-2bfa-41f5-99a2-4db38ea639c9'
API_URL = 'https://zebra-ai-api-prd.azurewebsites.net/'  # prod
CLIENT_ID = 'ef17d154-cefa-4bb9-8d0e-6127c992f7ce'
AUTHORITY = 'https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47'
SCOPE = ['api://9021b3a5-1f0d-4fb7-ad3f-d6989f0432d8/.default']

def get_access_token():
    app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        enable_broker_on_windows=True
    )
    result = app.acquire_token_interactive(scopes=SCOPE, parent_window_handle=app.CONSOLE_WINDOW_HANDLE)
    if 'access_token' in result:
        return result['access_token']
    raise Exception('Failed to get access token')

def call_version_api(access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(f'{API_URL}version', headers=headers)
    response.raise_for_status()
    return response.json()

def call_whoami_api(access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(f'{API_URL}test/whoami', headers=headers)
    response.raise_for_status()
    return response.json()

def call_experiment_api(access_token, experiment_id=EXPERIMENT_ID, filter_str="SAPFullPath eq 'Azure/DDOS Protection/Configuration and setup'", max_rows=10):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    run_model = {
        "DataSearchOptions": {
            "Search": "*",
            "Filter": filter_str,
        },
        "MaxNumberOfRows": max_rows
    }

    # Set up logging
    logging.basicConfig(filename="zebra_ai_api.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("API Request: URL=%s, Headers=%s, Payload=%s", f'{API_URL}experiment/{experiment_id}', headers, json.dumps(run_model))

    response = requests.post(f'{API_URL}experiment/{experiment_id}', headers=headers, data=json.dumps(run_model))
    logging.info("API Response: Status=%s, Content=%s", response.status_code, response.text)
    response.raise_for_status()
    data = response.json()
    questions = extract_all_questions(data)
    return {"response": data, "questions": questions}

def pretty_print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

# Example usage as a callable module:
def run_zebra_ai_client(sap_full_path="Azure/DDOS Protection/Configuration and setup", number_of_cases=3):
   # import urllib.parse
    print('Zebra AI Sample Python Client')
    access_token = get_access_token()
    version_info = call_version_api(access_token)
    whoami_info = call_whoami_api(access_token)
    #encoded_sap_full_path = urllib.parse.quote(sap_full_path, safe="")
    filter_str = f"SAPFullPath eq '{sap_full_path}'"
    experiment_result = call_experiment_api(access_token, filter_str=filter_str, max_rows=number_of_cases)
    #print("API Version Info:")
    #pretty_print_json(version_info)
    #print("\nWhoAmI Info:")
    #pretty_print_json(whoami_info)
    #print("\nExtracted Questions:")
    #for q in experiment_result["questions"]:
    #    print("-", q)
    # Optionally, print full experiment response:
    # pretty_print_json(experiment_result["response"])
    return experiment_result["questions"]  # <-- Return the list of questions

# To use from another Python file:
# from auth_mi import run_zebra_ai_client
# run_zebra_ai_client(sap_full_path="Azure/DDOS Protection/Configuration and setup", number_of_cases=5)
