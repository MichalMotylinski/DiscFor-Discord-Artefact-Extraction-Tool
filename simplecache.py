from os.path import join, exists
from os import listdir, SEEK_SET, SEEK_CUR
from re import search

from common import get_filename, read_http_response, content_to_file, hex_time_convert


# This script contains functions used only for data recovery from Chromium Simple Cache
# Functions shared with other scripts can be found in common.py


def read_simple_cache(dump_dir):
    cache_dict = {}
    cache_data_list = []
    empty_entries = 0
    range_files = 0
    recovered = 0
    all_entries = 0

    for cache_name in listdir(join(dump_dir, "Dumps", "Cache")):
        range_url_data = ""
        range_url_length = 0
        if "_0" in cache_name:
            all_entries += 1
            # Read content of a cache file
            with open(join(dump_dir, "Dumps", "Cache", cache_name), "rb") as cache_file:
                eof1 = search(b"\xd8\x41\x0d\x97\x45\x6f\xfa\xf4\x01", cache_file.read())
                cache_file.seek(eof1.end() + 7, SEEK_SET)
                file_size = int(cache_file.read(4)[::-1].hex(), 16)

                cache_file.seek(0, SEEK_SET)
                eof3 = search(b"\xd8\x41\x0d\x97\x45\x6f\xfa\xf4\x03", cache_file.read())
                cache_file.seek(eof3.end() + 7, SEEK_SET)
                response_size = int(cache_file.read(4)[::-1].hex(), 16)

                cache_file.seek(12, SEEK_SET)
                url_length = int(cache_file.read(4)[::-1].hex(), 16)
                cache_file.seek(24, SEEK_SET)
                url_data = cache_file.read(url_length).decode("ascii")

                # Get name of a cache file that contains resource data
                if file_size == 0:
                    range_file = cache_name[0:16] + "_s"
                    range_url_data, range_url_length, file_size, resource_data = read_range_file(range_file, dump_dir)
                    file_name = range_file
                    range_files += 1
                else:
                    file_offset = cache_file.seek(24 + url_length, SEEK_SET)
                    resource_data = cache_file.read(file_size)
                    file_name = cache_name

                response_offset = cache_file.seek(eof1.end() + 43, SEEK_SET)
                response_data = str(cache_file.read(response_size))

                server_response, content_type, etag, response_time, last_modified, max_age, server_name, expire_time, \
                    timezone, content_encoding, server_ip = read_http_response(response_data)
                filename, file_extension = get_filename(content_type, file_size, url_data)

                # Save information to dictionary for further use
            if not file_size == 0:
                # Extract files found within cache and calculate their hashes
                recovered += 1
                filename, md5, sha1, sha256 = content_to_file(resource_data, filename, file_extension, dump_dir,
                                                              content_encoding, url_data, content_type
                                                              )
                cache_dict["Filename"] = filename
                cache_dict["URL"] = url_data
                cache_dict["Range URL"] = range_url_data
                cache_dict["Content Type"] = content_type
                cache_dict["File Size"] = file_size
                cache_dict["Last Accessed"] = ""
                cache_dict["Cache Entry Created"] = ""
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
            else:
                empty_entries += 1

    # Read real index file containing all cache entry addresses
    cache_address_array = read_real_index(dump_dir)

    for cache_address in cache_address_array:
        for entry in cache_data_list:
            try:
                if cache_address[0] == entry["File Location"][0:16]:
                    entry["Last Accessed"] = cache_address[1]
                    entry["Cache Entry Created"] = cache_address[1]
                    break
            except ValueError:
                entry["Last Accessed"] = ""
                entry["Cache Entry Created"] = ""

    reconstructed = range_files - empty_entries
    return cache_data_list, all_entries, recovered, empty_entries, reconstructed


def read_real_index(dump_dir):
    # Read index file containing names of all cache files
    temp_array = []
    cache_address_array = []
    with open(join(dump_dir, "Dumps", "Cache", "index-dir", "the-real-index"), "rb") as index_file:
        index_file.seek(20, SEEK_SET)
        entry_count = int(index_file.read(8)[::-1].hex(), 16)
        i = 0
        offset = 40

        while i < entry_count:
            index_file.seek(offset, SEEK_SET)
            cache_name = str(index_file.read(8)[::-1].hex())
            last_accessed = hex_time_convert(int(index_file.read(8)[::-1].hex(), 16))
            temp_array.extend((cache_name, last_accessed))
            cache_address_array.append(temp_array)
            temp_array = []
            i += 1
            offset += 24
    return cache_address_array


def read_range_file(range_name, dump_dir):
    # Get resource data when it is saved outside main cache file
    range_url_data = ""
    range_url_length = 0
    file_size = 0
    resource_data = b""
    if exists(join(dump_dir, "Dumps", "Cache", range_name)):
        with open(join(dump_dir, "Dumps", "Cache", range_name), "rb") as range_file:
            range_file.seek(12, SEEK_SET)
            range_url_length = int(range_file.read(4)[::-1].hex(), 16)
            range_file.seek(24, SEEK_SET)
            range_url_data = range_file.read(range_url_length).decode("ascii")

            range_file.seek(16, SEEK_CUR)
            file_size = int(range_file.read(8)[::-1].hex(), 16)

            range_file.seek(8, SEEK_CUR)
            resource_data = range_file.read(file_size)
    return range_url_data, range_url_length, file_size, resource_data
