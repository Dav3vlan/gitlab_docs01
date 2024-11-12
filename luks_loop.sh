#!/bin/bash

LUKS_PARTITION="/dev/sdX"
LUKS_NAME="encrypted_volume"
MOUNT_POINT="/home/$USER/Desktop/secure"
PASSWORD_FILE="pass.txt"

# Ensure mount point directory exists
if [ ! -d "$MOUNT_POINT" ]; then
  echo "Creating mount point at $MOUNT_POINT..."
  sudo mkdir -p "$MOUNT_POINT"
fi

# Check if password file exists
if [ ! -f "$PASSWORD_FILE" ]; then
  echo "Password file not found: $PASSWORD_FILE"
  exit 1
fi

# Loop through each password in the file and try to unlock
while IFS= read -r PASSWORD; do
  echo "Trying password: $PASSWORD"
  echo "$PASSWORD" | sudo cryptsetup open "$LUKS_PARTITION" "$LUKS_NAME" --key-file=-

  # Check if unlocking was successful
  if [ $? -eq 0 ]; then
    echo "Successfully unlocked LUKS partition with password."
    PASSWORD_FOUND=1
    break
  else
    echo "Failed to unlock with this password."
  fi
done < "$PASSWORD_FILE"

# If no password worked, exit with an error
if [ -z "$PASSWORD_FOUND" ]; then
  echo "All passwords failed. Could not unlock LUKS partition."
  exit 1
fi

# Mount the unlocked LUKS partition
echo "Mounting decrypted partition..."
sudo mount "/dev/mapper/$LUKS_NAME" "$MOUNT_POINT"

# Check if mount was successful
if [ $? -eq 0 ]; then
  echo "Partition mounted successfully at $MOUNT_POINT."
else
  echo "Failed to mount the decrypted partition."
  sudo cryptsetup close "$LUKS_NAME"
fi
