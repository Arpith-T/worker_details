import json
import subprocess
import os
import dotenv
import requests as requests
from influxdb import InfluxDBClient


dotenv.load_dotenv(".env")

PASSWORD = os.environ["PASSWORD"]

infra_client = InfluxDBClient('hci-rit-prism-sel.cpis.c.eu-de-2.cloud.sap', 8086, 'arpdb')

infra_client.switch_database('arpdb')

def aciat001_oauth_token():
    login = subprocess.run(
        f'cf login -a https://api.cf.sap.hana.ondemand.com -o "CPI-Global-Canary_aciat001"  -s prov_eu10_aciat001 -u prism@global.corp.sap -p {PASSWORD}')
    # print(login)

    oauth_token = subprocess.run("cf oauth-token", stdout=subprocess.PIPE)

    oauth_token_string = str(oauth_token.stdout)

    return oauth_token_string[2:-3]

def aciat001_trm_token():
    url = "https://aciat001.authentication.sap.hana.ondemand.com/oauth/token?grant_type=client_credentials"

    payload = {}
    files = {}
    headers = {
        'Authorization': 'Basic c2ItaXQhYjc2NDg6ZmIyMGZmYzktMDFjNy00ZTY2LTk2ODAtMjk3YzU3ZWY0ZTYzJEduMEtEeFYtd2Q4NTNTWTNJVXBjeElOSWU3UzhpRjZhZ3Jsdll0aXdhTE09'
    }

    response = requests.request("GET", url, headers=headers, data=payload, files=files)

    # print(response.text)
    # print("\n")
    # print(type(response.text))
    res_in_dict = json.loads(response.text)
    return res_in_dict["access_token"]


base_url = "https://api.cf.sap.hana.ondemand.com/v3/apps"
space_guid = "2c92d3e7-a833-4fbf-89e2-917c07cea220"
token = f"{aciat001_oauth_token()}"


url = f"{base_url}?page=1&per_page=1000&space_guids={space_guid}"
payload = {}
headers = {
    'Authorization': token
}

response = requests.request("GET", url, headers=headers, data=payload)

# TODO convert the string received from above to a dictionary

response_dict = json.loads(response.text)
resources = response_dict["resources"]

len_of_resources = len(response_dict["resources"])

# TODO  list all the apps

string_of_apps = []
for app in range(0, len_of_resources):
    string_of_apps.append(resources[app]["name"])

# TODO out of the apps collected list the apps starting with itw- and sore it in a list - by matching substring -
#  https://stackoverflow.com/questions/3437059/does-python-have-a-string-contains-substring-method

worker_list = []
for item in string_of_apps:
    if "itw-" in item:
        worker_list.append(item)

print(worker_list)
no_of_workers = len(worker_list)
print(f"Total no. of workers found here is -  {no_of_workers}")


def get_tenant_names():
    all_tenant_list = []
    url = "https://it-aciat001-trm.cfapps.sap.hana.ondemand.com/api/trm/v1/tenants/subscription"

    payload = {}
    headers = {
        'Authorization': f'Bearer {aciat001_trm_token()}',
        'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    all_tenant_names = json.loads(response.text)
    # print(len(all_tenant_names))

    for tenant in range(0, len(all_tenant_names)):
        # print(all_tenant_names[tenant]["subscribedTenantName"])
        all_tenant_list.append(all_tenant_names[tenant]["subscribedTenantName"])

    return all_tenant_list


tenant_list = get_tenant_names()

print("\n")


# print(tenant_list)

def tenant_data():
    final_tenant_list = []
    for tenant in tenant_list:
        if tenant in str(worker_list):
            # print(tenant)
            final_tenant_list.append(tenant)
    return final_tenant_list


for tenantname in tenant_data():

    url = f"https://it-aciat001-trm.cfapps.sap.hana.ondemand.com/api/trm/v1/tenants/{tenantname}/" \
          f"workersets/itw-{tenantname}-0"

    payload = {}
    headers = {
        'Authorization': f'Bearer {aciat001_trm_token()}',
        'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    tenant_info = json.loads(response.text)

    worker = tenant_info["workerApps"][0]["name"]
    worker_version = tenant_info["workerApps"][0]["version"]

    # print(f"for {tenantname}, worker is {worker} with worker version - {worker_version}\n")

    worker_info = [
        {
            "measurement": "worker_info",
            "tags": {
                "alias": "IAT-AWS"
            },
            "fields": {
                "Tenant": tenantname,
                "Worker": worker,
                "Image_version": worker_version
            }
        }
    ]
    if infra_client.write_points(worker_info, protocol='json'):
        print(f"{tenantname} - Data Insertion success")
        pass
    else:
        print("Dev-Data Insertion Failed")



