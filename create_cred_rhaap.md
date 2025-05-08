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
