# List of standard library imports
from os import SEEK_SET
from os.path import join, exists

# List of local imports
from common import get_filename, content_to_file, read_http_response, hex_time_convert


# This script contains functions used only for data recovery from Chromium Disk Cache structure
# Functions shared with other scripts can be found in common.py


# Main class for Disk Cache structure reading data from cache entries
def read_cache_entry(dump_dir):
    range_data = []
    cache_data_list = []
    url_data = ""
    reconstructed = 0
    recovered = 0
    cache_dir = join(dump_dir, "Dumps", "Cache")
    cache_address_array = read_rankings(cache_dir)
    all_entries = len(cache_address_array)

    # Begin extraction by iterating through all cache entries (based on addresses from rankings file)
    for cache_address in cache_address_array:
        # Read information for current entry
        with open(join(cache_dir, "data_1"), "rb") as data_1:
            block_num = cache_address[0]
            block_offset = 8192 + (block_num * 256)
            entry_location = "data_1" + " [" + str(block_offset) + "]"

            data_1.seek(block_offset + 32, SEEK_SET)
            url_length = int(data_1.read(4)[::-1].hex(), 16)
            long_url_address = data_1.read(4)
            http_response_size = int(data_1.read(4)[::-1].hex(), 16)
            content_size = int(data_1.read(4)[::-1].hex(), 16)

            data_1.seek(block_offset + 56, SEEK_SET)
            http_response_address = data_1.read(4)[::-1].hex()
            resource_content_address = data_1.read(4)[::-1].hex()

            data_1.seek(block_offset + 72, SEEK_SET)
            cache_content_part = int(data_1.read(1).hex(), 16)

            range_url_data = ""
            range_url_length = 0

            if long_url_address == b"\x00\x00\x00\x00":
                # Pattern deviation included (some files have 2 cache entries)
                # Separated parts are saved to a list for further reconstruction
                if cache_content_part == 2:
                    data_1.seek(block_offset + 96, SEEK_SET)
                    range_url_data = data_1.read(url_length).decode("ascii")
                    range_url_length = len(range_url_data)
                    if range_url_data.endswith("0") and not content_size == 0:
                        range_data.append([range_url_data, range_url_length, resource_content_address, content_size])
                        reconstructed += 1
                    continue
                else:
                    # Simple reading for URL located within current entry
                    data_1.seek(block_offset + 96, SEEK_SET)
                    url_data = data_1.read(url_length).decode("ascii")
            else:
                # Longer entries might exist in different block files thus reading option for all
                print(cache_address_array.index(cache_address), url_data)
                if long_url_address[::-1].hex()[0] == "a":
                    block_num = int(long_url_address[:2][::-1].hex(), 16)
                    block_offset = 8192 + (block_num * 256)
                    data_1.seek(block_offset, SEEK_SET)
                    url_data = data_1.read(url_length).decode("ascii")
                elif long_url_address[::-1].hex()[0] == "b":
                    with open(join(cache_dir, "data_2"), "rb") as data_2:
                        block_num = int(long_url_address[:2][::-1].hex(), 16)
                        block_offset = 8192 + (block_num * 1024)
                        data_2.seek(block_offset, SEEK_SET)
                        url_data = data_2.read(url_length).decode("ascii")
                elif long_url_address[::-1].hex()[0] == "c":
                    with open(join(cache_dir, "data_3"), "rb") as data_3:
                        block_num = int(long_url_address[:2][::-1].hex(), 16)
                        block_offset = 8192 + (block_num * 4096)
                        data_3.seek(block_offset, SEEK_SET)
                        url_data = data_3.read(url_length).decode("ascii")

            # Get server HTTP response
            response_data, response_location = get_http_response(cache_dir, http_response_size, http_response_address)
            # Fetch appropriate data from server HTTP response
            server_response, content_type, etag, response_time, last_modified, max_age, server_name, expire_time, \
                timezone, content_encoding, server_ip = read_http_response(response_data)

            # Save information to dictionary for further use
            if not http_response_size == 0:
                cache_dict = {"Filename": "", "URL": url_data, "Range URL": range_url_data,
                              "Content Type": content_type, "File Size": content_size,
                              "Last Accessed": cache_address[1], "Cache Entry Created": cache_address[2],
                              "Last Modified": last_modified, "Expire Time": expire_time,
                              "Response Time": response_time, "User Timezone": timezone,
                              "Cache Entry Location": entry_location, "Response Location": response_location,
                              "File Location": resource_content_address, "Content Encoding": content_encoding,
                              "ETag": etag, "Max Age": max_age, "Server Response": server_response,
                              "Server Name": server_name, "Server IP": server_ip, "URL Length": url_length,
                              "Range URL Length": range_url_length, "MD5": "", "SHA1": "", "SHA256": ""}
                # Append current dictionary values to a list of all entries
                cache_data_list.append(cache_dict)

    # Reconstruct entries by joining items from range_list with their other parts in main list
    for i in range_data:
        for j in cache_data_list:
            if j["URL"] in i[0]:
                j["Range URL"] = i[0]
                j["Range URL Length"] = i[1]
                j["File Location"] = i[2]
                j["File Size"] = i[3]
                break
    range_data.clear()

    # Remove empty files from the list
    cache_data_list[:] = [x for x in cache_data_list if not x["File Size"] == 0]

    # Extract files found within cache and calculate their hashes
    for i in cache_data_list:
        filename, file_extension = get_filename(i["Content Type"], i["File Size"], i["URL"])
        i["Filename"] = filename, file_extension
        resource_data, i["File Location"] = read_resource_content(cache_dir, i["File Size"], i["File Location"])
        i["Filename"], i["MD5"], i["SHA1"], i["SHA256"] = content_to_file(resource_data, filename, file_extension,
                                                                          dump_dir, i["Content Encoding"], i["URL"],
                                                                          i["Content Type"])
        if resource_data is not None:
            recovered += 1

    empty_entries = all_entries - recovered
    return cache_data_list, all_entries, recovered, empty_entries, reconstructed


# Read all cache addresses and control data from the rankings file
def read_rankings(cache_dir):
    cache_address_array = []
    with open(join(cache_dir, "data_0"), "rb") as index_file:
        index_file.seek(16, SEEK_SET)
        entry_count = int(index_file.read(4)[:2][::-1].hex(), 16)
        i = 0
        offset = 8192

        # Get address, last access time and creation time of cache entry
        while i < entry_count:
            index_file.seek(offset, SEEK_SET)
            entry = index_file.read(36)
            if not entry[24:28] == b"\x00\x00\x00\x00":
                # Hexadecimal date values get converted into readable format
                last_access_time = hex_time_convert(int(entry[0:7][::-1].hex(), 16))
                entry_creation_time = hex_time_convert(int(entry[8:15][::-1].hex(), 16))
                address = int(entry[24:27][:2][::-1].hex(), 16)
                cache_address_array.append([address, last_access_time, entry_creation_time])
                i += 1
            offset += 36
    return cache_address_array


def get_http_response(cache_dir, http_response_size, http_response_address):
    http_response_data = ""
    response_location = ""

    # Recover server HTTP response which contains information about the file
    # Support for all 3 block files that may contain response
    if not http_response_size == 0 and not http_response_address == "\\x00\\x00\\x00\\x00":
        if http_response_address[0] == "a":
            with open(join(cache_dir, "data_1"), "rb") as data_1:
                block_num = int(http_response_address[4:8], 16)
                block_offset = 8192 + (block_num * 256)
                data_1.seek(block_offset, SEEK_SET)
                http_response_data = str(data_1.read(http_response_size))
                response_location = "data_1" + " [" + str(block_offset) + "]"
        elif http_response_address[0] == "b":
            with open(join(cache_dir, "data_2"), "rb") as data_2:
                block_num = int(http_response_address[4:8], 16)
                block_offset = 8192 + (block_num * 1024)
                data_2.seek(block_offset, SEEK_SET)
                http_response_data = str(data_2.read(http_response_size))
                response_location = "data_2" + " [" + str(block_offset) + "]"
        elif http_response_address[0] == "c":
            with open(join(cache_dir, "data_3"), "rb") as data_3:
                block_num = int(http_response_address[4:8], 16)
                block_offset = 8192 + (block_num * 4096)
                data_3.seek(block_offset, SEEK_SET)
                http_response_data = str(data_3.read(http_response_size))
                response_location = "data_3" + " [" + str(block_offset) + "]"
    return http_response_data, response_location


# Read resource content which will be later used to reconstruct a file
def read_resource_content(cache_dir, resource_content_size, resource_content_address):
    file_location = ""
    resource_data = None
    if not resource_content_size == 0:
        if not resource_content_address == "":
            # Find and fetch data from appropriate location
            if resource_content_address[0] == "a":
                with open(join(cache_dir, "data_1"), "rb") as data_1:
                    block_num = int(resource_content_address[4:8], 16)
                    block_offset = 8192 + (block_num * 256)
                    data_1.seek(block_offset, SEEK_SET)
                    resource_data = data_1.read(resource_content_size)
                    file_location = "data_1" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "b":
                with open(join(cache_dir, "data_2"), "rb") as data_2:
                    block_num = int(resource_content_address[4:8], 16)
                    block_offset = 8192 + (block_num * 1024)
                    data_2.seek(block_offset, SEEK_SET)
                    resource_data = data_2.read(resource_content_size)
                    file_location = "data_2" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "c":
                with open(join(cache_dir, "data_3"), "rb") as data_3:
                    block_num = int(resource_content_address[4:8], 16)
                    block_offset = 8192 + (block_num * 4096)
                    data_3.seek(block_offset, SEEK_SET)
                    resource_data = data_3.read(resource_content_size)
                    file_location = "data_3" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "8":
                file_location = "f_" + resource_content_address[2:8]
                if exists(join(cache_dir, file_location)):
                    external_file = open(join(cache_dir, file_location), "rb")
                    resource_data = external_file.read()

    return resource_data, file_location
