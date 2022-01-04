import json

import requests




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
    print(len(all_tenant_names))

    for tenant in range(0, len(all_tenant_names)):
        # print(all_tenant_names[tenant]["subscribedTenantName"])
        all_tenant_list.append(all_tenant_names[tenant]["subscribedTenantName"])

    return all_tenant_list


tenant_list = get_tenant_names()

