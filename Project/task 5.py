from hl7apy.core import Message, Segment
import json
from pathlib import Path
from datetime import datetime
import requests

# Constants
SNOMED_HERMES_URL = "http://159.65.173.51:8080/v1/snomed/concepts"

# File paths
data_dir = Path("data")
patient_file = data_dir / "patient_details_payload.json"
condition_file = data_dir / "parent_condition_payload.json"
output_file = data_dir / "hl7_patient.txt"

# Load patient and condition data
with open(patient_file, "r") as f:
    patient_data = json.load(f)

with open(condition_file, "r") as f:
    condition_data = json.load(f)

# Extract patient details
patient_id = patient_data["identifier"][0]["value"]
name_info = patient_data["name"][0]
full_name = f"{name_info.get('family', '')}^{name_info.get('given', [''])[0]}"

# Extract gender, handle if it's a list or string and convert 'MALE' or 'FEMALE' to 'M' or 'F'
gender = patient_data.get("gender", "")
if isinstance(gender, list):
    gender = gender[0].upper() if gender else ""
else:
    gender = gender.upper()

# Map full gender descriptions to single letters
if gender == "MALE":
    gender = "M"
elif gender == "FEMALE":
    gender = "F"

birthdate = patient_data.get("birthDate", "").replace("-", "")
address_info = patient_data.get("address", [{}])[0]
address_line = address_info.get("line", [""])[0]
city = address_info.get("city", "")
state = address_info.get("state", "")
postal_code = address_info.get("postalCode", "")

# Extract condition data
condition_code = condition_data["code"]["coding"][0]["code"]
condition_display = condition_data["code"]["coding"][0]["display"]

# Fetch ICD-10 mapping
map_url = f"http://159.65.173.51:8080/v1/snomed/concepts/{condition_code}/map/447562003"
map_response = requests.get(map_url)
mapping_data = map_response.json()

if not mapping_data:
    raise ValueError(f"No ICD-10 mapping found for SNOMED code {condition_code}")

first_entry = mapping_data[0]
icd_code = first_entry.get("mapTarget")
if not icd_code:
    raise KeyError(f"Missing expected 'mapTarget' in mapping data. Available keys: {list(first_entry.keys())}")
icd_display = condition_display  # Use SNOMED description if ICD display is not available

# Get timestamp
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Create HL7 ADT_A01 message
msg = Message("ADT_A01")

# MSH Segment
msg.msh.msh_1 = "|"
msg.msh.msh_2 = "^~\\&"
msg.msh.msh_3 = "OpenEMR_FHIR"           # Sending Application (source system)
msg.msh.msh_4 = "OpenEMR_Facility"        # Sending Facility
msg.msh.msh_5 = "PrimaryCare_EHR"         # Receiving Application (target system)
msg.msh.msh_6 = "PrimaryCare_Facility"    # Receiving Facility
msg.msh.msh_7 = timestamp
msg.msh.msh_9 = "ADT^A01"
msg.msh.msh_10 = "MSG00001"
msg.msh.msh_11 = "P"
msg.msh.msh_12 = "2.5"

# PID Segment
pid = Segment("PID")
pid.pid_3 = patient_id
pid.pid_5 = full_name
pid.pid_7 = birthdate
pid.pid_8 = gender
pid.pid_11 = f"{address_line}^^{city}^{state}^{postal_code}"
msg.add(pid)

# PV1 Segment
pv1 = Segment("PV1")
pv1.pv1_2 = "O"  # Outpatient
pv1.pv1_44 = timestamp
msg.add(pv1)

# DG1 Segment
dg1 = Segment("DG1")
dg1.dg1_1 = "1"
dg1.dg1_3 = f"{icd_code}^{icd_display}^ICD-10"
dg1.dg1_4 = condition_display
dg1.dg1_6 = "F"
msg.add(dg1)

# Save HL7 message to file
with open(output_file, "w") as f:
    f.write(msg.to_er7())

print(f"HL7 ADT message saved to: {output_file}")