import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import re

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)



# ==== CONFIGURATION ====
CSV_FILE = "report1746679951782in.csv"  # Path to your CSV


SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
SF_USERNAME = os.getenv("SF_USERNAME")
SF_PASSWORD = os.getenv("SF_PASSWORD")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN")  # Optional, only if needed

# ==== STEP 1: Authenticate to Salesforce ====
auth_url = "https://lendlease--uat.sandbox.my.salesforce.com/services/oauth2/token"
# auth_url = "https://test.salesforce.com/services/oauth2/token"

auth_payload = {
    "grant_type": "password",
    "client_id": SF_CLIENT_ID,
    "client_secret": SF_CLIENT_SECRET,
    "username": SF_USERNAME, 
    "password": SF_PASSWORD + SF_SECURITY_TOKEN 
}


auth_response = requests.post(auth_url, data=auth_payload).json()
print(f" Auth response: {auth_response}")


if "access_token" not in auth_response:
    raise Exception(f"Auth failed: {auth_response}")

access_token = auth_response["access_token"]
instance_url = auth_response["instance_url"]
headers = {"Authorization": f"Bearer {access_token}"}

# ==== STEP 2: Use a specific project name ====
project_name = "Melbourne Quarter R1"  # Replace with your actual project name
print(f"📝 Using specific project: {project_name}")



# ==== STEP 3: Prepare Timestamped Download Folder ====
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
base_dir = os.getcwd()  # Gets current working directory on Windows or any OS
base_download_dir = os.path.join(base_dir, "salesforce_document_folder_downloads", f"SalesForceProjectsDownload_{timestamp}")
os.makedirs(base_download_dir, exist_ok=True)

# ==== STEP 4: Loop through Projects and Download Files ====

print(f"\n📁 Project: {project_name}  ")

# Get Gates for this Project
gate_query = f"SELECT Id, Name FROM LLCompass_Gate__c WHERE Project__r.Name = '{project_name}'"
gates = requests.get(f"{instance_url}/services/data/v63.0/query",headers=headers, params={"q": gate_query}).json()

print("Gates API response:", gates)
print("\n")

query = "SELECT QualifiedApiName FROM EntityDefinition WHERE QualifiedApiName LIKE '%Gate%'"
response = requests.get(f"{instance_url}/services/data/v63.0/query", headers=headers, params={"q": query})
print(response.json())





for gate in gates["records"]:
    gate_id = gate["Id"]
    gate_name = gate["Name"]
    print(f"  🔹 Gate: {gate_name} ({gate_id})")

    # Get Documents linked to the Gate
    doclink_query = f"SELECT ContentDocumentId FROM ContentDocumentLink WHERE LinkedEntityId = '{gate_id}'"
    doclinks = requests.get(f"{instance_url}/services/data/v63.0/query",
                            headers=headers, params={"q": doclink_query}).json()

    for link in doclinks["records"]:
        doc_id = link["ContentDocumentId"]

        # Get Latest ContentVersion
        version_query = f"SELECT Id, Title, VersionData FROM ContentVersion WHERE ContentDocumentId = '{doc_id}' ORDER BY CreatedDate DESC LIMIT 1"
        version = requests.get(f"{instance_url}/services/data/v63.0/query",
                               headers=headers, params={"q": version_query}).json()

        if not version["records"]:
            continue

        file_id = version["records"][0]["Id"]
        file_name = version["records"][0]["Title"]
        file_url = f"{instance_url}/services/data/v63.0/sobjects/ContentVersion/{file_id}/VersionData"

        # Prepare full file path


        safe_project_name = sanitize_filename(project_name)
        safe_gate_name = sanitize_filename(gate_name)

        save_dir = os.path.join(base_download_dir, safe_project_name, safe_gate_name)
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, file_name)


        # Download the file
        file_data = requests.get(file_url, headers=headers).content
        with open(save_path, "wb") as f:
            f.write(file_data)

        print(f"    ✅ Downloaded: {file_name}")
