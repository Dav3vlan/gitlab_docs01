provisioner "shell" {
    inline = [
      "if command -v yum &> /dev/null; then",
      "  sudo yum update -y",
      "  sudo yum install -y python3-pip",
      "elif command -v apt-get &> /dev/null; then",
      "  sudo apt-get update",
      "  sudo apt-get install -y python3-pip",
      "else",
      "  echo 'Unable to install pip: No supported package manager found'",
      "  exit 1",
      "fi",
      "sudo pip3 install jmespath"
    ]
  }

