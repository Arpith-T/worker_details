import subprocess
import os
import dotenv

dotenv.load_dotenv(".env")

PASSWORD = os.environ["PASSWORD"]


def aciat001_oauth_token():
    login = subprocess.run(f'cf login -a https://api.cf.sap.hana.ondemand.com -o "CPI-Global-Canary_aciat001"  -s prov_eu10_aciat001 -u prism@global.corp.sap -p {PASSWORD}')
    # print(login)

    oauth_token = subprocess.run("cf oauth-token", stdout=subprocess.PIPE)

    oauth_token_string = str(oauth_token.stdout)

    return oauth_token_string[2:-3]

    # print(type(oauth_token_string[2:-3]))


print(aciat001_oauth_token())

#please note - this has a bytecode issue. hence , this first  needs to be converted into a string and certain non wanted characters needs to be removed as below

"""output_in_string =str(output.stdout)# prints the standard output of the guid

test = output_in_string


print(test[2:-3])"""
