#!/usr/bin/env python

from __future__ import print_function
import argparse
import json
import logging
import os
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import ssl
import subprocess
import sys
import time
try:
    from httplib import HTTPSConnection
    from httplib import HTTPConnection
except ImportError:
    from http.client import HTTPSConnection
    from http.client import HTTPConnection
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# Argument Parser

def parse_args():
    parser = argparse.ArgumentParser(description="Upload images")

    parser.add_argument(
        "--url",
        required=True,
        help="Path to image (e.g. /path/to/image.raw). "
            "Supported formats: raw, qcow2, iso.")
    parser.add_argument(
        "--username",
        required=True,
        help="Admin RHV-M username")
    parser.add_argument(
        "--password",
        required=True,
        help="Admin RHV-M password")
    parser.add_argument(
        "--sdname",
        required=True,
        help="Name of the storage domain.")
    parser.add_argument(
        "--filepath",
        required=True,
        help="Path to image (e.g. /path/to/image.raw). "
             "Supported formats: raw, qcow2, iso.")
    parser.add_argument(
        "--direct",
        dest="direct",
        default=False,
        action="store_true")
    return parser.parse_args()

args = parse_args()

# This seems to give the best throughput when uploading from my laptop
# SSD to a server that drop the data. You may need to tune this on your
# setup.
BUF_SIZE = 128 * 1024
logging.basicConfig(level=logging.DEBUG, filename='example.log')
direct_upload = False

image_size = os.path.getsize(args.filepath)
# Get image info using qemu-img
print("Checking image...", args.filepath)
out = subprocess.check_output(
    ["qemu-img", "info", "--output", "json", args.filepath])
image_info = json.loads(out)
if image_info["format"] not in ("qcow2", "raw"):
    raise RuntimeError("Unsupported image format %(format)s" % image_info)
print("Disk format: %s" % image_info["format"])

content_type = types.DiskContentType.DATA
if image_info["format"] == "raw":
    with open(args.filepath, "rb") as f:
        f.seek(0x8000)
        primary_volume_descriptor = f.read(8)
    if primary_volume_descriptor == b"\x01CD001\x01\x00":
        content_type = types.DiskContentType.ISO
print("Disk content type: %s" % content_type)
# This example will connect to the server and create a new `floating`
# disk, one that isn't attached to any virtual machine.
# Then using transfer service it will transfer disk data from local
# qcow2 disk to the newly created disk in server.
# Create the connection to the server:
print("Connecting...")
connection = sdk.Connection(url=args.url, username=args.username, password=args.password, insecure=True)

# Get the reference to the root service:
system_service = connection.system_service()

print("Creating disk...")
if image_info["format"] == "qcow2":
    disk_format = types.DiskFormat.COW
else:
    disk_format = types.DiskFormat.RAW
disks_service = connection.system_service().disks_service()
disk = disks_service.add(
    disk=types.Disk(
        name=os.path.basename(args.filepath),
        content_type=content_type,
        description='Trilio Vault',
        format=disk_format,
        initial_size=image_size,
        provisioned_size=image_info["virtual-size"],
        sparse=disk_format == types.DiskFormat.COW,
        storage_domains=[
            types.StorageDomain(
                name=args.sdname
            )
        ]
    )
)
# Wait till the disk is up, as the transfer can't start if the
# disk is locked:
disk_service = disks_service.disk_service(disk.id)
while True:
    time.sleep(5)
    disk = disk_service.get()
    if disk.status == types.DiskStatus.OK:
        break
print("Creating transfer session...")
# Get a reference to the service that manages the image
# transfer that was added in the previous step:
transfers_service = system_service.image_transfers_service()
# Add a new image transfer:
transfer = transfers_service.add(
    types.ImageTransfer(
        image=types.Image(
            id=disk.id
        )
     )
)
# Get reference to the created transfer service:
transfer_service = transfers_service.image_transfer_service(transfer.id)
# After adding a new transfer for the disk, the transfer's status will be INITIALIZING.
# Wait until the init phase is over. The actual transfer can start when its status is "Transferring".
while transfer.phase == types.ImageTransferPhase.INITIALIZING:
    time.sleep(1)
    transfer = transfer_service.get()
print("Uploading image...")
# At this stage, the SDK granted the permission to start transferring the disk, and the
# user should choose its preferred tool for doing it - regardless of the SDK.
# In this example, we will use Python's httplib.HTTPSConnection for transferring the data.
# import pdb; pdb.set_trace()
if args.direct:
    if transfer.transfer_url is not None:
        destination_url = urlparse(transfer.transfer_url)
    else:
        print("Direct upload to host not supported (requires ovirt-engine 4.2 or above).")
        sys.exit(1)
else:
    destination_url = urlparse(transfer.proxy_url)
#context = ssl.create_default_context()
# import ssl
context = ssl._create_unverified_context()
# Note that ovirt-imageio-proxy by default checks the certificates, so if you don't have
# your CA certificate of the engine in the system, you need to pass it to HTTPSConnection.
#context.load_verify_locations(cafile='ca.pem')
proxy_connection = HTTPSConnection(
    destination_url.hostname,
    destination_url.port,
    context=context,
)
print(destination_url.hostname)
print(destination_url.port)

proxy_connection.putrequest("PUT", destination_url.path)
proxy_connection.putheader('Content-Length', "%d" % (image_size,))
proxy_connection.endheaders()
# Send the request body.
# Note that we must send the number of bytes we promised in the
# Content-Range header.
start = last_progress = time.time()
with open(args.filepath, "rb") as disk:
    pos = 0
    while pos < image_size:
        print(pos, image_size)
        # Send the next chunk to the proxy.
        to_read = min(image_size - pos, BUF_SIZE)
        chunk = disk.read(to_read)
        if not chunk:
            transfer_service.pause()
            raise RuntimeError("Unexpected end of file at pos=%d" % pos)
        proxy_connection.send(chunk)
        pos += len(chunk)
        now = time.time()
        # Report progress every 10 seconds.
        if now - last_progress > 10:
            print("Uploaded %.2f%%" % (float(pos) / image_size * 100))
            last_progress = now
# Get the response
response = proxy_connection.getresponse()
if response.status != 200:
    transfer_service.pause()
    print("Upload failed: %s %s" % (response.status, response.reason))
    sys.exit(1)
elapsed = time.time() - start
print("Uploaded %.2fg in %.2f seconds (%.2fm/s)" % (
      image_size / float(1024**3), elapsed, image_size / 1024**2 / elapsed))
print("Finalizing transfer session...")
# Successful cleanup
transfer_service.finalize()
connection.close()
proxy_connection.close()
print("Upload completed successfully")
