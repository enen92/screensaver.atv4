"""
   Copyright (C) 2017- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.

   Note: This is a standalone script to update the offline video entries and
   their checksums. Extra modes allow for Apple JSON download and simple
   printing of the different locations available in the JSON.
"""
import hashlib
import json
import os
import sys
import tarfile
from urllib import request

apple_local_feed = os.path.join("resources", "entries.json")
tmp_folder = "tmpvideos"
# A new resources file exists as of 2023-09-29, but only has 4K SDR 240FPS links
# http://sylvan.apple.com/itunes-assets/Aerials126/v4/82/2e/34/822e344c-f5d2-878c-3d56-508d5b09ed61/resources-14-0-10.tar
apple_resources_tar = "https://sylvan.apple.com/Aerials/resources-15.tar"
local_tar = "resources.tar"


# Fetch the TAR file containing the latest entries.json and overwrite the local copy
def get_latest_entries_from_apple():
    print("Downloading the Apple Aerials resources.tar to disk")

    request.urlretrieve(apple_resources_tar, local_tar)
    # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
    apple_tar = tarfile.open(local_tar)
    print("Extracting entries.json from resources.tar and placing in ./resources")
    apple_tar.extract("entries.json", "resources")
    apple_tar.close()
    os.remove(local_tar)


def generate_entries_and_checksums():
    with open(apple_local_feed) as feed_file:

        print("Starting checksum generator...")
        # Create the local directory we'll temporarily store videos for checksumming
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        # Dictionary to store the filenames and checksum for each
        checksums = {}
        # Dictionary to store the quality levels and the size in megabytes for each
        # Within each scene, there may be: H264/HEVC, 1080p/4K, SDR/HDR
        quality_total_size_megabytes = {"url-1080-H264": 0,
                                        "url-1080-SDR": 0,
                                        "url-1080-HDR": 0,
                                        "url-4K-SDR-240FPS": 0,
                                        "url-4K-HDR": 0}
        quality_total_video_count = {"url-1080-H264": 0,
                                        "url-1080-SDR": 0,
                                        "url-1080-HDR": 0,
                                        "url-4K-SDR-240FPS": 0,
                                        "url-4K-HDR": 0}

        # Define the locations as a set so we get deduping
        locations = set()

        top_level = json.load(feed_file)
        # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
        for block in top_level["assets"]:
            # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
            current_scene = block["accessibilityLabel"]
            print("Processing videos for scene:", current_scene)
            locations.add(current_scene)

            # https://realpython.com/iterate-through-dictionary-python/#iterating-through-keys
            for video_version in quality_total_size_megabytes.keys():
                try:
                    # Try to look up the URL, but catch the KeyError and continue if it wasn't available
                    asset_url = block[video_version]

                    # If the URL contains HTTPS, we need revert to HTTP to avoid bad SSL cert
                    # NOTE: Old Apple URLs were HTTP, new URLs are HTTPS with a bad cert
                    if "https" in asset_url:
                        asset_url = asset_url.replace("https://", "http://")

                    print("Downloading video:", asset_url)

                    # Construct the name and path of the local file
                    local_file_name = asset_url.split("/")[-1]
                    local_file_path = os.path.join(tmp_folder, local_file_name)

                    # Download the file to local storage
                    request.urlretrieve(asset_url, local_file_path)

                    # Get the size of the file in bytes and add it to an overall size counter
                    quality_total_size_megabytes[video_version] += os.path.getsize(local_file_path) / 1000 / 1000
                    # We found a valid file for the given version, update the count
                    quality_total_video_count[video_version] += 1

                    # Try to open the file
                    with open(local_file_path, "rb") as f:
                        # Compute the checksum
                        checksum = hashlib.md5(f.read()).hexdigest()
                        # Add the checksum to the dict of checksums we're keeping
                        checksums[local_file_name] = checksum

                    # Delete the local copy of the file
                    os.remove(local_file_path)
                    print("File processed. Checksum:", checksum)
                except KeyError:
                    print("Can't find URL for asset type:", video_version)

        # Now that we've processed all videos, delete the temp directory
        os.rmdir(tmp_folder)

        # Then write the checksums to file
        with open(os.path.join("resources", "checksums.json"), "w") as f:
            print("Writing checksums to disk")
            f.write(json.dumps(checksums))

        print("Total Megabytes of all video files, per quality:")
        print(quality_total_size_megabytes)
        print("Total count of all video files, per quality:")
        print(quality_total_video_count)
        print("Locations seen:")
        print(locations)
        print("Stopping checksum generator...")


def get_locations():
    with open(apple_local_feed) as feed_file:
        # Define the locations as a set so we get deduping
        locations = set()

        top_level = json.load(feed_file)
        # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
        for block in top_level["assets"]:
            # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
            locations.add(block["accessibilityLabel"])
        # Now that all locations are added, sort in place and print
        print("Locations seen:")
        print(sorted(locations))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            generate_entries_and_checksums()
        elif sys.argv[1] == "2":
            get_latest_entries_from_apple()
        elif sys.argv[1] == "3":
            get_locations()
    else:
        print("Please specify option:\n "
              "1) Update checksums based on existing entries.json \n "
              "2) Update entries.json from Apple \n "
              "3) Print all locations in entries.json")
