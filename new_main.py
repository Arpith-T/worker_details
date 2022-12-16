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
cf_oauth_url = "https://uaa.cf.eu20.hana.ondemand.com"
user = "prism@global.corp.sap"
oauth_url = "https://ziat001.authentication.eu20.hana.ondemand.com/oauth/token"
trm_url = "https://it-ziat001-trm.cfapps.eu20.hana.ondemand.com"
trm_basic_auth = "c2ItaXQhYjIxMjoxMDA4YTY5Yy04ZjY4LTRmMmMtODhhNy0zMTI1ZTliZDBkOTEkTTYwNV9hTWdINGJvWmhIQ1hLZE5HRkNuV2tzRHNpN0ZTcmVzNUNwTk9Iaz0="
base_url = "https://api.cf.eu20.hana.ondemand.com/v3/apps"
space_guid = "e4451758-664a-4a4e-8edd-ceeef7204488"
IAAS = "IAT-AZURE"


def cf_oauth_token():
    url = f"{cf_oauth_url}/oauth/token"

    payload = f"grant_type=password&client_id=cf&client_secret=&username={user}&password={PASSWORD}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=FPtRDK1dM3D1lD56pq9oAq9mvHn19ohxqXjClhqrbLI%3D; JSESSIONID=MzllOWRjMmMtZTFjNC00OTJiLTk2NDctMDFmMzQ2MjhiMzgz; __VCAP_ID__=5d5db63a-a273-474d-42af-3ebbfa1ae677'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    access_token = json.loads(response.text)["access_token"]

    return access_token


def trm_token():
    url = f"{oauth_url}?grant_type=client_credentials"

    payload = {}
    files = {}
    headers = {
        "Authorization": f"Basic {trm_basic_auth}"
    }

    response = requests.request("GET", url, headers=headers, data=payload, files=files)

    res_in_dict = json.loads(response.text)
    return res_in_dict["access_token"]


token = cf_oauth_token()

url = f"{base_url}?page=1&per_page=1000&space_guids={space_guid}"
payload = {}
headers = {
    'Authorization': f'Bearer {token}'
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
    url = f"{trm_url}/api/trm/v1/tenants/subscription"

    payload = {}
    headers = {
        'Authorization': f'Bearer {trm_token()}',
        # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
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

print(f"The tenant list is - {tenant_list}")


def tenant_data():
    final_tenant_list = []
    for tenant in tenant_list:
        if tenant in str(worker_list):
            # print(tenant)
            final_tenant_list.append(tenant)
    return final_tenant_list


def tenant_token(tenantname):
    url = f"https://{tenantname}.authentication.eu20.hana.ondemand.com/oauth/token?grant_type=client_credentials"

    payload = {}
    headers = {
        'Authorization': 'Basic c2ItaXQhYjIxMjoxMDA4YTY5Yy04ZjY4LTRmMmMtODhhNy0zMTI1ZTliZDBkOTEkTTYwNV9hTWdINGJvWmhIQ1hLZE5HRkNuV2tzRHNpN0ZTcmVzNUNwTk9Iaz0='
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)

    res_in_dict = json.loads(response.text)
    return res_in_dict["access_token"]


for tenantname in tenant_data():

    url = f"{trm_url}/api/trm/v1/tenants/{tenantname}/" \
          f"workersets/itw-{tenantname}-0"

    payload = {}
    headers = {
        'Authorization': f'Bearer {trm_token()}',
        # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    tenant_info = json.loads(response.text)


    worker = tenant_info["workerApps"][0]["name"]
    worker_version = tenant_info["workerApps"][0]["version"]

    url = f"https://apm.cf.eu20.hana.ondemand.com/e/e24988d1-11a4-407c-abc9-03bca9eeacaa/api/v2/metrics/query" \
          f"?metricSelector=ext:cpi.it-ziat001.it-worker.InitialContentSyncTime&entitySelector=type(" \
          f"process_group_instance),entityName.equals(\"itw-{tenantname}-0\")&from=now-5m "

    payload = {}
    headers = {
        'Authorization': 'Api-Token dt0c01.IE5O4FI2QWZE523UQDWTWOQ7'
                         '.CAH4CXUGJHJRMELNUWDMRVX27PH5BLOXR47IEEHDO4YLNCF7CMGDFM4H2LO7L5KW',
        'Cookie': 'apmroute=ab3f83895184dcf8a1ee1318b987c21c'
    }

    response = requests.request("GET", url, headers=headers, data=payload).json()

    # print(json.dumps(response, indent=2))

    content_sync_time = []

    for count in range(0, int(response["totalCount"])):
        time = round((int(response["result"][0]["data"][count]["values"][0]) / 60000))
        content_sync_time.append(time)
    try:
        print(content_sync_time)

        content_sync_all_time = str(content_sync_time)
        print(max(content_sync_time))

        max_content_sync_time = max(content_sync_time)
    except:
        content_sync_all_time = "NA"
        max_content_sync_time = 0

    # print(f"for {tenantname}, worker is {worker} with worker version - {worker_version}\n")

    tenant_token_var = tenant_token(tenantname=tenantname)

    url = "https://it-ziat001-co.cfapps.eu20.hana.ondemand.com/api/co/v1/artifact-infos?count=true&artifactType=BUNDLE"

    payload = {}
    headers = {
        'support_tenant_name': tenantname,
        'Authorization': f'Bearer {tenant_token_var}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        # print(response.headers['Content-Type'])
        # print(response.headers)
        # print(response.content)
        header_data = response.headers

        try:
            print(header_data["x-total-count"])
            total_artifact_count = header_data["x-total-count"]
        except:
            total_artifact_count = "NA"

    worker_info = [
        {
            "measurement": "worker_info",
            "tags": {
                "alias": IAAS
            },
            "fields": {
                "Tenant": tenantname,
                "Worker": worker,
                "Image_version": worker_version,
                "content_sync_time_all": content_sync_all_time,
                "max_content_sync_time": max_content_sync_time,
                "total_artifact_count": total_artifact_count
            }
        }
    ]

    print(worker_info)
    if infra_client.write_points(worker_info, protocol='json'):
        print(f"{tenantname} - Data Insertion success")
        pass
    else:
        print("Dev-Data Insertion Failed")
