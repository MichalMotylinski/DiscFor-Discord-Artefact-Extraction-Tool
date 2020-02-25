import os

import common

# This script contains functions used only for data recovery from Chromium main cache
# Functions shared with other scripts can be found in common.py

data_1 = None
data_2 = None
data_3 = None


def read_cache_entry(dump_dir):
    # Main class for old chrome cache structure reading data from cache entries
    global data_1, data_2, data_3
    temp_range_data = []
    temp_data_list = []
    cache_dict = {}
    cache_data_list = []
    url_data = ""

    cache_address_array = read_index(dump_dir)
    data_1 = open(dump_dir + "/Dumps/Cache/data_1", "rb")
    data_2 = open(dump_dir + "/Dumps/Cache/data_2", "rb")
    data_3 = open(dump_dir + "/Dumps/Cache/data_3", "rb")

    for cache_address in cache_address_array:
        # Read information for current entry
        block_num = cache_address[0]
        block_offset = 8192 + (block_num * 256)
        entry_location = "data_1" + " [" + str(block_offset) + "]"

        data_1.seek(block_offset + 32, os.SEEK_SET)
        url_data_size = int(data_1.read(4)[::-1].hex(), 16)
        long_url_address = data_1.read(4)
        http_response_size = int(data_1.read(4)[::-1].hex(), 16)
        resource_content_size = int(data_1.read(4)[::-1].hex(), 16)

        data_1.seek(block_offset + 56, os.SEEK_SET)
        http_response_address = data_1.read(4)[::-1].hex()
        resource_content_address = data_1.read(4)[::-1].hex()

        data_1.seek(block_offset + 72, os.SEEK_SET)
        cache_content_part = int(data_1.read(1).hex(), 16)

        range_url_data = ""
        range_url_data_size = 0

        if long_url_address == b'\x00\x00\x00\x00':
            # Pattern deviation included (some files have 2 cache entries)
            if cache_content_part == 2:
                data_1.seek(block_offset + 96, os.SEEK_SET)
                range_url_data = data_1.read(url_data_size).decode("ascii")
                range_url_data_size = len(range_url_data)
                if range_url_data.endswith("0") and not resource_content_size == 0:
                    temp_range_data.extend((range_url_data, range_url_data_size, resource_content_address,
                                            resource_content_size))
                    temp_data_list.append(temp_range_data)
                    temp_range_data = []
                continue
            else:
                data_1.seek(block_offset + 96, os.SEEK_SET)
                url_data = data_1.read(url_data_size).decode("ascii")
        else:
            if long_url_address[::-1].hex()[0] == "a":
                block_num = int(long_url_address[:2][::-1].hex(), 16)
                block_offset = 8192 + (block_num * 256)
                data_1.seek(block_offset, os.SEEK_SET)
                url_data = data_1.read(url_data_size).decode("ascii")
            elif long_url_address[::-1].hex()[0] == "b":
                block_num = int(long_url_address[:2][::-1].hex(), 16)
                block_offset = 8192 + (block_num * 1024)
                data_2.seek(block_offset, os.SEEK_SET)
                url_data = data_2.read(url_data_size).decode("ascii")
            elif long_url_address[::-1].hex()[0] == "c":
                block_num = int(long_url_address[:2][::-1].hex(), 16)
                block_offset = 8192 + (block_num * 4096)
                data_3.seek(block_offset, os.SEEK_SET)
                url_data = data_3.read(url_data_size).decode("ascii")

        response_data, response_location = get_http_response(http_response_size, http_response_address)
        server_response, status, content_type, etag, response_time, last_modified, max_age, server_name, expire_time, \
        timezone, content_encoding, server_ip = common.read_http_response(response_data)

        # Save information to dictionary for further use
        if not http_response_size == 0:
            cache_dict["Filename"] = ""
            cache_dict["URL"] = url_data
            cache_dict["Range URL"] = range_url_data
            cache_dict["Content Type"] = content_type
            cache_dict["File Size"] = resource_content_size
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

            cache_data_list.append(cache_dict)
            cache_dict = {}

    # Append range url and content address to the cache data list
    for i in temp_data_list:
        for j in cache_data_list:
            if j["URL"] in i[0]:
                j["Range URL"] = i[0]
                j["Range URL Length"] = i[1]
                j["File Location"] = i[2]
                j["File Size"] = i[3]

    # Remove empty files from the list
    cache_data_list[:] = [x for x in cache_data_list if not x["File Size"] == 0]
    temp_data_list.clear()

    # Extract files found within cache and calculate their hashes
    for i in cache_data_list:
        i["Filename"] = common.get_filename(i["Content Type"], i["File Size"], i["URL"], cache_data_list)
        resource_data, i["File Location"] = read_resource_content(i["File Size"], i["File Location"], dump_dir)
        i["MD5"], i["SHA1"], i["SHA256"] = common.extract_file(resource_data, i["Filename"], dump_dir,
                                                               i["Content Encoding"])
    return cache_data_list


def read_index(output_dir):
    # Read all cache entries from the records file
    index_file = open(output_dir + "/Dumps/Cache/data_0", "rb")
    entry_array = []
    index_file.seek(16, os.SEEK_SET)
    entry_count = int(index_file.read(4)[:2][::-1].hex(), 16)
    cache_address_array = []
    i = 0
    offset = 8188

    # Get address, last access time and creation time of cache entry
    while i < entry_count:
        index_file.seek(offset, os.SEEK_SET)
        entry = index_file.read(36)
        if not entry[28:32] == b'\x00\x00\x00\x00':
            last_access_time = common.hex_time_convert(int(entry[4:11][::-1].hex(), 16))
            entry_creation_time = common.hex_time_convert(int(entry[12:19][::-1].hex(), 16))
            address = int(entry[28:32][:2][::-1].hex(), 16)
            entry_array.extend((address, last_access_time, entry_creation_time))
            cache_address_array.append(entry_array)
            entry_array = []
            i += 1
        offset += 36
    return cache_address_array


def get_http_response(http_response_size, http_response_address):
    http_response_data = ""
    response_location = ""

    # Read HTTP response which contains information about the file
    if not http_response_size == 0 and not http_response_address == "\\x00\\x00\\x00\\x00":
        if http_response_address[0] == "a":
            block_num = int(http_response_address[4:8], 16)
            block_offset = 8192 + (block_num * 256)
            data_1.seek(block_offset, os.SEEK_SET)
            http_response_data = str(data_1.read(http_response_size))
            response_location = "data_1" + " [" + str(block_offset) + "]"
        elif http_response_address[0] == "b":
            block_num = int(http_response_address[4:8], 16)
            block_offset = 8192 + (block_num * 1024)
            data_2.seek(block_offset, os.SEEK_SET)
            http_response_data = str(data_2.read(http_response_size))
            response_location = "data_2" + " [" + str(block_offset) + "]"
        elif http_response_address[0] == "c":
            block_num = int(http_response_address[4:8], 16)
            block_offset = 8192 + (block_num * 4096)
            data_3.seek(block_offset, os.SEEK_SET)
            http_response_data = str(data_3.read(http_response_size))
            response_location = "data_3" + " [" + str(block_offset) + "]"
    return http_response_data, response_location


def read_resource_content(resource_content_size, resource_content_address, output_dir):
    file_location = ""

    # Read resource content which will be later used to reconstruct a file
    resource_data = None
    if not resource_content_size == 0:
        if not resource_content_address == "":
            if resource_content_address[0] == "a":
                block_num = int(resource_content_address[4:8], 16)
                block_offset = 8192 + (block_num * 256)
                data_1.seek(block_offset, os.SEEK_SET)
                resource_data = data_1.read(resource_content_size)
                file_location = "data_1" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "b":
                block_num = int(resource_content_address[4:8], 16)
                block_offset = 8192 + (block_num * 1024)
                data_2.seek(block_offset, os.SEEK_SET)
                resource_data = data_2.read(resource_content_size)
                file_location = "data_2" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "c":
                block_num = int(resource_content_address[4:8], 16)
                block_offset = 8192 + (block_num * 4096)
                data_3.seek(block_offset, os.SEEK_SET)
                resource_data = data_3.read(resource_content_size)
                file_location = "data_3" + " [" + str(block_offset) + "]"
            elif resource_content_address[0] == "8":
                file_location = "f_" + resource_content_address[2:8]
                for root, dirs, files in os.walk(output_dir + "/Dumps"):
                    for i in files:
                        if file_location in i:
                            ext_file = open(os.path.join(root, i), "rb")
                            resource_data = ext_file.read()

    return resource_data, file_location
