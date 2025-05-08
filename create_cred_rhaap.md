curl -k -X POST \
  -H "Authorization: Bearer $AAP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rhel9-stig-key",
    "description": "PEM key for RHEL 9 STIG scan",
    "organization": 1,
    "credential_type": 1,
    "inputs": {
      "username": "ec2-user",
      "ssh_key_data": "'"$PEM_KEY"'"
    }
  }' \
  https://mysite.io/api/controller/v2/credentials/


Notes:

    "credential_type": 1 = built-in SSH/Machine credential

    "organization": 1 = your org ID (usually 1, but confirm via /api/controller/v2/organizations/)

    "username" = the remote login username (e.g., ec2-user, admin, etc.)


# get  org id

curl -k -H "Authorization: Bearer $AAP_TOKEN" \
     -H "Accept: application/json" \
     "https://mysite.io/api/controller/v2/job_templates/?name=rhel9-stig-template"
curl -k -H "Authorization: Bearer $AAP_TOKEN" \
     -H "Accept: application/json" \
     "https://mysite.io/api/controller/v2/job_templates/?name=rhel9-stig-template"


# associte with job id

curl -k -X POST \
  -H "Authorization: Bearer $AAP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": 17}' \
  https://mysite.io/api/controller/v2/job_templates/42/credentials/


