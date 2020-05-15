from os.path import join, exists
from os import SEEK_SET

from common import get_filename, content_to_file, read_http_response, hex_time_convert


# This script contains functions used only for data recovery from Chromium main cache
# Functions shared with other scripts can be found in common.py


def read_cache_entry(dump_dir):
    # Main class for old chrome cache structure reading data from cache entries
    temp_data = []
    temp_data_list = []
    cache_dict = {}
    cache_data_dict = []
    url_data = ""
    reconstructed = 0
    recovered = 0
    cache_dir = join(dump_dir, "Dumps", "Cache")
    cache_address_array = read_index(cache_dir)
    all_entries = len(cache_address_array)

    for cache_address in cache_address_array:
        # Read information for current entry
        with open(join(cache_dir, "data_1"), "rb") as data_1:
            block_num = cache_address[0]
            block_offset = 8192 + (block_num * 256)
            entry_location = "data_1" + " [" + str(block_offset) + "]"

            data_1.seek(block_offset + 32, SEEK_SET)
            url_data_size = int(data_1.read(4)[::-1].hex(), 16)
            long_url_address = data_1.read(4)
            http_response_size = int(data_1.read(4)[::-1].hex(), 16)
            content_size = int(data_1.read(4)[::-1].hex(), 16)

            data_1.seek(block_offset + 56, SEEK_SET)
            http_response_address = data_1.read(4)[::-1].hex()
            resource_content_address = data_1.read(4)[::-1].hex()

            data_1.seek(block_offset + 72, SEEK_SET)
            cache_content_part = int(data_1.read(1).hex(), 16)

            range_url_data = ""
            range_url_data_size = 0

            if long_url_address == b"\x00\x00\x00\x00":
                # Pattern deviation included (some files have 2 cache entries)
                if cache_content_part == 2:
                    data_1.seek(block_offset + 96, SEEK_SET)
                    range_url_data = data_1.read(url_data_size).decode("ascii")
                    range_url_data_size = len(range_url_data)
                    if range_url_data.endswith("0") and not content_size == 0:
                        temp_data.extend((range_url_data, range_url_data_size, resource_content_address, content_size))
                        temp_data_list.append(temp_data)
                        reconstructed += 1
                        temp_data = []
                    continue
                else:
                    data_1.seek(block_offset + 96, SEEK_SET)
                    url_data = data_1.read(url_data_size).decode("ascii")
            else:
                if long_url_address[::-1].hex()[0] == "a":
                    block_num = int(long_url_address[:2][::-1].hex(), 16)
                    block_offset = 8192 + (block_num * 256)
                    data_1.seek(block_offset, SEEK_SET)
                    url_data = data_1.read(url_data_size).decode("ascii")
                elif long_url_address[::-1].hex()[0] == "b":
                    with open(join(cache_dir, "data_2"), "rb") as data_2:
                        block_num = int(long_url_address[:2][::-1].hex(), 16)
                        block_offset = 8192 + (block_num * 1024)
                        data_2.seek(block_offset, SEEK_SET)
                        url_data = data_2.read(url_data_size).decode("ascii")
                elif long_url_address[::-1].hex()[0] == "c":
                    with open(join(cache_dir, "data_3"), "rb") as data_3:
                        block_num = int(long_url_address[:2][::-1].hex(), 16)
                        block_offset = 8192 + (block_num * 4096)
                        data_3.seek(block_offset, SEEK_SET)
                        url_data = data_3.read(url_data_size).decode("ascii")

            response_data, response_location = get_http_response(cache_dir, http_response_size, http_response_address)
            server_response, content_type, etag, response_time, last_modified, max_age, server_name, expire_time, \
                timezone, content_encoding, server_ip = read_http_response(response_data)

            # Save information to dictionary for further use
            if not http_response_size == 0:
                cache_dict["Filename"] = ""
                cache_dict["URL"] = url_data
                cache_dict["Range URL"] = range_url_data
                cache_dict["Content Type"] = content_type
                cache_dict["File Size"] = content_size
                cache_dict["Last Accessed"] = cache_address[1]
                cache_dict["Cache Entry Created"] = cache_address[2]
                cache_dict["Last Modified"] = last_modified
                cache_dict["Expire Time"] = expire_time
                cache_dict["Response Time"] = response_time
                cache_dict["User Timezone"] = timezone
                cache_dict["Cache Entry Location"] = entry_location
                cache_dict["Response Location"] = response_location
                cache_dict["File Location"] = resource_content_address
                cache_dict["Content Encoding"] = content_encoding
                cache_dict["ETag"] = etag
                cache_dict["Max Age"] = max_age
                cache_dict["Server Response"] = server_response
                cache_dict["Server Name"] = server_name
                cache_dict["Server IP"] = server_ip
                cache_dict["URL Length"] = url_data_size
                cache_dict["Range URL Length"] = range_url_data_size
                cache_dict["MD5"] = ""
                cache_dict["SHA1"] = ""
                cache_dict["SHA256"] = ""
                cache_data_dict.append(cache_dict)
                cache_dict = {}

    # Append range url and content address to the cache data list
    for i in temp_data_list:
        for j in cache_data_dict:
            if j["URL"] in i[0]:
                j["Range URL"] = i[0]
                j["Range URL Length"] = i[1]
                j["File Location"] = i[2]
                j["File Size"] = i[3]
                break
    temp_data_list.clear()

    # Remove empty files from the list
    cache_data_dict[:] = [x for x in cache_data_dict if not x["File Size"] == 0]

    # Extract files found within cache and calculate their hashes
    for i in cache_data_dict:
        filename, file_extension = get_filename(i["Content Type"], i["File Size"], i["URL"])
        i["Filename"] = filename, file_extension
        resource_data, i["File Location"] = read_resource_content(cache_dir, i["File Size"], i["File Location"])
        i["Filename"], i["MD5"], i["SHA1"], i["SHA256"] = content_to_file(resource_data, filename, file_extension,
                                                                          dump_dir, i["Content Encoding"], i["URL"],
                                                                          i["Content Type"])
        if resource_data is not None:
            recovered += 1

    empty_entries = all_entries - recovered
    return cache_data_dict, all_entries, recovered, empty_entries, reconstructed


def read_index(cache_dir):
    # Read all cache entries from the records file
    entry_array = []
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
                last_access_time = hex_time_convert(int(entry[0:7][::-1].hex(), 16))
                entry_creation_time = hex_time_convert(int(entry[8:15][::-1].hex(), 16))
                address = int(entry[24:27][:2][::-1].hex(), 16)
                entry_array.extend((address, last_access_time, entry_creation_time))
                cache_address_array.append(entry_array)
                entry_array = []
                i += 1
            offset += 36
    return cache_address_array


def get_http_response(cache_dir, http_response_size, http_response_address):
    http_response_data = ""
    response_location = ""

    # Read HTTP response which contains information about the file
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


def read_resource_content(cache_dir, resource_content_size, resource_content_address):
    file_location = ""

    # Read resource content which will be later used to reconstruct a file
    resource_data = None
    if not resource_content_size == 0:
        if not resource_content_address == "":
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
                    ext_file = open(join(cache_dir, file_location), "rb")
                    resource_data = ext_file.read()

    return resource_data, file_location
