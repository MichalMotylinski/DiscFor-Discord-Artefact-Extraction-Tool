import os
import re

import common

# This script contains functions used only for data recovery from Chromium simplecache
# Functions shared with other scripts can be found in common.py


def read_simple_cache(dump_dir):
    cache_dict = {}
    cache_data_list = []

    # Read real index file containing all cache entry addresses
    real_index = open(dump_dir + "/Dumps/Cache/index-dir/the-real-index", "rb")
    cache_address_array = read_real_index(real_index)

    for cache_address in cache_address_array:
        cache_name = cache_address[0] + "_0"
        for root, dirs, files in os.walk(dump_dir + "/Dumps"):
            for i in files:
                if cache_name in i:
                    range_url_data = ""
                    range_url_length = 0

                    # Read content of a cache file
                    with open(os.path.join(root, i), "rb") as cache_file:
                        eof1 = re.search(b'\xd8\x41\x0d\x97\x45\x6f\xfa\xf4\x01', cache_file.read())

                        cache_file.seek(eof1.end() + 7, os.SEEK_SET)
                        file_size = int(cache_file.read(4)[::-1].hex(), 16)

                        cache_file.seek(0, os.SEEK_SET)
                        eof3 = re.search(b'\xd8\x41\x0d\x97\x45\x6f\xfa\xf4\x03', cache_file.read())

                        cache_file.seek(eof3.end() + 7, os.SEEK_SET)
                        response_size = int(cache_file.read(4)[::-1].hex(), 16)

                        cache_file.seek(12, os.SEEK_SET)
                        url_length = int(cache_file.read(4)[::-1].hex(), 16)
                        cache_file.seek(24, os.SEEK_SET)
                        url_data = cache_file.read(url_length).decode("ascii")

                        # Get name of a cache file that contains resource data
                        if file_size == 0:
                            range_file = cache_address[0] + "_s"
                            range_url_data, range_url_length, file_size, resource_data = read_range_file(range_file,
                                                                                                         dump_dir)
                            file_name = range_file
                        else:
                            file_offset = cache_file.seek(24 + url_length, os.SEEK_SET)
                            resource_data = cache_file.read(file_size)
                            file_name = cache_name

                        response_offset = cache_file.seek(eof1.end() + 43, os.SEEK_SET)
                        response_data = str(cache_file.read(response_size))

                        server_response, status, content_type, etag, response_time, last_modified, max_age, \
                        server_name, expire_time, timezone, content_encoding, server_ip = common.read_http_response(response_data)
                        filename = common.get_filename(content_type, file_size, url_data, cache_data_list)

                        # Save information to dictionary for further use
                        if not file_size == 0:
                            # Extract files found within cache and calculate their hashes
                            md5, sha1, sha256 = common.extract_file(resource_data, filename, dump_dir,
                                                                    content_encoding)
                            cache_dict["Filename"] = filename
                            cache_dict["URL"] = url_data
                            cache_dict["Range URL"] = range_url_data
                            cache_dict["Content Type"] = content_type
                            cache_dict["File Size"] = file_size
                            cache_dict["Last Accessed"] = cache_address[1]
                            cache_dict["Cache Entry Created"] = cache_address[1]
                            cache_dict["Last Modified"] = last_modified
                            cache_dict["Expire Time"] = expire_time
                            cache_dict["Response Time"] = response_time
                            cache_dict["User Timezone"] = timezone
                            cache_dict["Cache Entry Location"] = cache_name
                            cache_dict["Response Location"] = cache_name + " [" + str(response_offset) + "]"
                            cache_dict["File Location"] = file_name + " [" + str(file_offset) + "]"
                            cache_dict["Content Encoding"] = content_encoding
                            cache_dict["ETag"] = etag
                            cache_dict["Max Age"] = max_age
                            cache_dict["Server Response"] = server_response
                            cache_dict["Server Name"] = server_name
                            cache_dict["Server IP"] = server_ip
                            cache_dict["URL Length"] = url_length
                            cache_dict["Range URL Length"] = range_url_length
                            cache_dict["MD5"] = md5
                            cache_dict["SHA1"] = sha1
                            cache_dict["SHA256"] = sha256

                            cache_data_list.append(cache_dict)
                            cache_dict = {}
    return cache_data_list


def read_real_index(index_file):
    # Read index file containing names of all cache files
    index_file.seek(20, os.SEEK_SET)
    entry_count = int(index_file.read(8)[::-1].hex(), 16)
    temp_array = []
    cache_address_array = []
    i = 0
    offset = 40
    while i < entry_count:
        index_file.seek(offset, os.SEEK_SET)
        cache_name = str(index_file.read(8)[::-1].hex())
        last_accessed = common.hex_time_convert(int(index_file.read(8)[::-1].hex(), 16))
        temp_array.extend((cache_name, last_accessed))
        cache_address_array.append(temp_array)
        temp_array = []
        i += 1
        offset += 24
    return cache_address_array


def read_range_file(range_name, output_dir):
    # Get resource data when it is saved outside main cache file
    range_url_data = ""
    range_url_length = 0
    file_size = 0
    resource_data = b''
    for root, dirs, files in os.walk(output_dir + "/Dumps"):
        for e in files:
            if range_name in e:
                with open(os.path.join(root, e), "rb") as range_file:
                    range_file.seek(12, os.SEEK_SET)
                    range_url_length = int(range_file.read(4)[::-1].hex(), 16)
                    range_file.seek(24, os.SEEK_SET)
                    range_url_data = range_file.read(range_url_length).decode("ascii")

                    range_file.seek(16, os.SEEK_CUR)
                    file_size = int(range_file.read(8)[::-1].hex(), 16)

                    range_file.seek(8, os.SEEK_CUR)
                    resource_data = range_file.read(file_size)
                break
    return range_url_data, range_url_length, file_size, resource_data
