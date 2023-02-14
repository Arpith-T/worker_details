import json
import requests
import re
import time

start_time = time.time()
system_id = "ziat001"
#
# worker_list = ['itw-katest-77tqy-perf-0-8', 'itw-perfscale-ngmse-8-0-75', 'itw-jittest-g5187-perf-0-19',
#                'itw-jittest-jllug-perf-0-18', 'itw-perfscale-ngmse-4-0-76', 'itw-katest-0k7tk-perf-0-38',
#                'itw-perfscale-8w38m-14-0-17', 'itw-katest-ucwvp-perf-0-43', 'itw-jittest-6qahf-perf-0-18',
#                'itw-jittest-9t6wd-perf-0-18', 'itw-katest-z0kyp-perf-0-37', 'itw-jittest-e2wd4-perf-0-19',
#                'itw-katest-e1nwf-perf-0-36', 'itw-katest-0e16n-perf-0-38', 'itw-katest-sxyah-perf-0-38',
#                'itw-katest-5iit8-perf-0-36', 'itw-perfscale-lel9q-19-0-73', 'itw-jittest-p0171-perf-0-21',
#                'itw-katest-yanmw-perf-0-41', 'itw-perfscale-lel9q-19-0-76']

app = "itw-co-validation-07-voihx-0-0-23"


def read_config():
    with open('config.json') as f:
        conf = json.load(f)
    return conf


config = read_config()

cf_oauth_url = json.dumps(config[system_id]['cf_oauth_url']).strip('\"')
user = json.dumps(config[system_id]['user']).strip('\"')
cf_base_url = json.dumps(config[system_id]['cf_base_url']).strip('\"')
space_id = json.dumps(config[system_id]['space_id']).strip('\"')
trm_url = json.dumps(config[system_id]['trm_url']).strip('\"')
trm_oauth_url = json.dumps(config[system_id]['trm_oauth_url']).strip('\"')
trm_basic_auth = json.dumps(config[system_id]['trm_basic_auth']).strip('\"')
password = json.dumps(config[system_id]['password']).strip('\"')


def cf_oauth_token():
    url = f"{cf_oauth_url}/oauth/token"

    payload = f"grant_type=password&client_id=cf&client_secret=&username={user}&password={password}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=FPtRDK1dM3D1lD56pq9oAq9mvHn19ohxqXjClhqrbLI%3D; JSESSIONID=MzllOWRjMmMtZTFjNC00OTJiLTk2NDctMDFmMzQ2MjhiMzgz; __VCAP_ID__=5d5db63a-a273-474d-42af-3ebbfa1ae677'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    access_token = json.loads(response.text)["access_token"]

    return access_token


token = cf_oauth_token()

url = f"{cf_base_url}/v3/apps?page=1&per_page=2000&space_guids={space_id}"
payload = {}
headers = {
    'Authorization': f'Bearer {token}'
}

response = requests.request("GET", url, headers=headers, data=payload)

# convert the string received from above to a dictionary

response_dict = json.loads(response.text)
resources = response_dict["resources"]

len_of_resources = len(response_dict["resources"])

print(f"length of resources - {len_of_resources}")

# list all the apps

string_of_apps = []
for app in range(0, len_of_resources):
    string_of_apps.append(resources[app]["name"])

# out of the apps collected list the apps starting with itw- and sore it in a list - by matching substring -


worker_list_cf = []
for item in string_of_apps:
    if "itw-" in item:
        worker_list_cf.append(item)

print(worker_list_cf)
no_of_workers = len(worker_list_cf)
print(f"Total no. of workers found here is -  {no_of_workers} in CF")


def trm_token():
    url = f"{trm_oauth_url}/oauth/token?grant_type=client_credentials"

    payload = {}
    headers = {
        'Authorization': f'Basic {trm_basic_auth}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)
    # print("\n")
    # print(type(response.text))
    res_in_dict = json.loads(response.text)
    return res_in_dict["access_token"]


def get_tenant_names():
    all_tenant_list = []
    url = f"{trm_url}/api/trm/v1/tenants/subscription"

    payload = {}
    headers = {
        'Authorization': f'Bearer {trm_token()}',
        'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    all_tenant_names = json.loads(response.text)
    print(len(all_tenant_names))

    for tenant in range(0, len(all_tenant_names)):
        # print(all_tenant_names[tenant]["subscribedTenantName"])
        all_tenant_list.append(all_tenant_names[tenant]["subscribedTenantName"])

    return all_tenant_list


tenant_list = get_tenant_names()

print(f"Total no. of tenants: {len(tenant_list)}\n")

print(tenant_list)


def get_app_guid(token, app):
    try:
        url = f"{cf_base_url}/v3/apps?page=1&per_page=3000&space_guids={space_id}&names={app}"

        payload = {}
        headers = {
            'Authorization': f'Bearer {token}'
            # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=FPtRDK1dM3D1lD56pq9oAq9mvHn19ohxqXjClhqrbLI%3D'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        guid = json.loads(response.text)["resources"][0]["guid"]

        return guid
    except:
        print(f"\n unable to fetch guid for {app}. There might couple of reasons for this - \n"
              f"1. Software Update might be in progress Or\n"
              f"2. There might be some deployment issue due to which there might be some duplication of applications.\n"
              f"3. Application name might be incorrect\n"
              f"Please contact Infra team to understand the root cause and resolution for the same"
              )


# app_guid = get_app_guid(token, app)


def get_app_env(token, app_guid):
    url = f"{cf_base_url}/v3/apps/{app_guid}/env"

    payload = {}
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # response = requests.request("GET", url, headers=headers, data=payload)

    # return response

    env_vars = requests.request("GET", url, headers=headers, data=payload).json()["environment_variables"]

    JBP_CONFIG_JAVA_OPTS = env_vars["JBP_CONFIG_JAVA_OPTS"]

    # print(type(data))
    # print(env_vars)

    options = re.findall("-D(.*?)=(.*?)\s", JBP_CONFIG_JAVA_OPTS)

    db_hikari_minimum_idle = next((value for key, value in options if key == "DB_HIKARI_MINIMUM_IDLE"), None)
    db_hikari_maximum_pool_size = next((value for key, value in options if key == "DB_HIKARI_MAXIMUM_POOL_SIZE"), None)

    memory_calculator_v1 = env_vars.get("MEMORY_CALCULATOR_V1", None)
    memory_weights = env_vars.get("JBP_CONFIG_SAPJVM_MEMORY_WEIGHTS", None)
    poll_timeout = env_vars.get("NZDM_POLL_TIMEOUT_IN_MIN", None)
    runtime_location = env_vars.get("RUNTIME_LOCATION_ID", None)
    print(
        f"memory_calculator: {memory_calculator_v1}\nmemory_weights: {memory_weights}\npoll_timeout: {poll_timeout}\nruntime_location: {runtime_location}")
    print("minimum_idle:", db_hikari_minimum_idle)
    print("maximum_pool_size:", db_hikari_maximum_pool_size)


tenant_list_without_worker = []
worker_list_trm = []
# app_env_data = get_app_env(token, app_guid)
print("\n")
numbered_list_of_tenants = list(enumerate(tenant_list, 1))
for number, tenantname in numbered_list_of_tenants:

    url = f"{trm_url}/api/trm/v1/tenants/{tenantname}/" \
          f"workersets/itw-{tenantname}-0"

    payload = {}
    headers = {
        'Authorization': f'Bearer {trm_token()}',
        # 'Cookie': 'JTENANTSESSIONID_kr19bxkapa=hXwfyso6e1%2FiD%2BzG%2FmTvccGsC%2F0%2F2O89fpaXQYYhBOU%3D'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    try:
        tenant_info = json.loads(response.text)
        # print(tenant_info)
    except:
        print(f"{number}: WARNING - unable to get the details for tenant - {tenantname}")
        # create a list of tenants for which we are not able to get the details
        tenant_list_without_worker.append(tenantname)

    else:

        worker = tenant_info["workerApps"][0]["name"]
        print(f"{number}: worker name: {worker}")
        # collect all the worker names in a list
        worker_list_trm.append(worker)
print("\n")
print(f"Total no. of tenants for which we are not able to get the details: {len(tenant_list_without_worker)}")
print(f"List of tenants for which we are not able to get the details: {tenant_list_without_worker}")
print("\n")
print(f"TRM worker list: {worker_list_trm}")

# compare the list of workers from TRM and CF
print("\n")
print(f"Total no. of workers in TRM: {len(worker_list_trm)}")
print(f"Total no. of workers in CF: {len(worker_list_cf)}")
print("\n")
# workers in cf but not in trm
print(f"Workers in CF but not in TRM: {list(set(worker_list_cf) - set(worker_list_trm))}")
print("the length of the list of worker in CF but not maintained by TRM is: ",
      len(list(set(worker_list_cf) - set(worker_list_trm))))
print("\n")
# send this list to a function which deletes the list of workers from CF which is not in trm
# delete_workers_from_cf(token, worker_list_cf, worker_list_trm)


workers_not_in_trm = list(set(worker_list_cf) - set(worker_list_trm))

# if the length of the list is 0, then there is no need to delete the workers from CF
if len(workers_not_in_trm) == 0:
    print("There are no workers in CF which are not maintained by TRM")
else:
    print("There are workers in CF which are not maintained by TRM")
    print("the list of workers in CF which are not maintained by TRM is: ", workers_not_in_trm)


# pass workers_not_in_trm to a function which gets the guid of each worker and creates the list of guid's
# get the guid of each worker and create a list of guid's
def get_guid_of_workers(token, workers_not_in_trm):
    guid_list = []
    for worker in workers_not_in_trm:
        guid = get_app_guid(token, worker)
        guid_list.append(guid)
    return guid_list


guid_list = get_guid_of_workers(token, workers_not_in_trm)
print(f"guid list: {guid_list}")


# pass the guid list to a function which deletes the workers from CF
def delete_workers_from_cf(token, guid_list):
    for guid in guid_list:
        url = f"{cf_base_url}/v3/apps/{guid}"

        payload = {}
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)

        print(response.text)
        print(f"for {guid} deletion: {response.status_code}")
        if response.status_code == 202:
            print(f"worker {guid} deleted successfully")
        elif response.status_code == 404:
            print(f"worker {guid} not found")
        else:
            print(f"unable to delete the worker {guid}")

# delete_workers_from_cf(token, guid_list)


end_time = time.time()

time_taken = end_time - start_time
time_taken_minutes = time_taken / 60
print("\n")
print(f"Time taken: {time_taken_minutes:.2f} minutes")


