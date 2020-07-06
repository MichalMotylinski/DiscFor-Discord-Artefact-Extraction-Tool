# List of standard library imports
from os import SEEK_SET
from os.path import join, exists

# List of local imports
from common import get_filename, content_to_file, read_http_response, hex_time_convert, get_data
from cachedata import Cache

# This script contains functions used only for data recovery from Chromium Disk Cache structure
# Functions shared with other scripts can be found in common.py


# Main class for Disk Cache structure reading data from cache entries
def read_cache_entry(discord_path, dump_dir):
    cache_list = []
    cache_temp_list1 = []
    cache_temp_list2 = []

    reconstructed = 0
    recovered = 0
    cache_dir = join(discord_path, "Cache")
    ranking_list = read_rankings(cache_dir)
    all_entries = len(ranking_list)

    with open(join(cache_dir, "data_1"), "rb") as data_1:
        for entry in ranking_list:
            block_offset = entry[0][1]
            cache_entry = Cache()

            # Find out if the entry is full or partial
            data_1.seek(block_offset + 72, SEEK_SET)
            cache_content_part = int(data_1.read(1).hex(), 16)

            if cache_content_part == 2:
                data_1.seek(block_offset + 24, SEEK_SET)
                partial_entry_created_time = hex_time_convert(int(data_1.read(8)[::-1].hex(), 16))

                data_1.seek(block_offset + 32, SEEK_SET)
                range_url_length = int(data_1.read(4)[::-1].hex(), 16)

                data_1.seek(block_offset + 48, SEEK_SET)
                content_size = int(data_1.read(4)[::-1].hex(), 16)

                data_1.seek(block_offset + 60, SEEK_SET)
                content_location = read_entry(data_1.read(4)[::-1].hex())

                data_1.seek(block_offset + 96, SEEK_SET)
                range_url_data = data_1.read(range_url_length).decode("ascii")

                if range_url_data.endswith("0") and content_size != 0:
                    cache_entry.partial_entry_created_time = partial_entry_created_time
                    cache_entry.range_url = range_url_data
                    cache_entry.range_url_length = range_url_length
                    cache_entry.range_url_location = ("data_1", block_offset + 96)
                    cache_entry.content_location = content_location
                    cache_entry.content_size = content_size
                    cache_temp_list2.append(cache_entry)
                    reconstructed += 1
                continue

            data_1.seek(block_offset + 24, SEEK_SET)
            cache_entry.entry_created_time = hex_time_convert(int(data_1.read(8)[::-1].hex(), 16))

            data_1.seek(block_offset + 32, SEEK_SET)
            cache_entry.url_length = int(data_1.read(4)[::-1].hex(), 16)
            long_url_location = read_entry(data_1.read(4)[::-1].hex())
            cache_entry.response_size = int(data_1.read(4)[::-1].hex(), 16)
            cache_entry.content_size = int(data_1.read(4)[::-1].hex(), 16)

            data_1.seek(block_offset + 56, SEEK_SET)
            cache_entry.response_location = read_entry(data_1.read(4)[::-1].hex())
            cache_entry.content_location = read_entry(data_1.read(4)[::-1].hex())

            if long_url_location:
                # Longer entries might exist in different block files thus reading option for all
                cache_entry.url = get_data(cache_dir, long_url_location, cache_entry.url_length).decode("ascii")
                cache_entry.url_location = long_url_location
            else:
                data_1.seek(block_offset + 96, SEEK_SET)
                cache_entry.url = data_1.read(cache_entry.url_length).decode("ascii")
                cache_entry.url_location = ("data_1", block_offset + 96)

            if cache_content_part == 0 and cache_entry.content_size != 0:
                cache_list.append(cache_entry)
            elif cache_content_part == 1:
                cache_temp_list1.append(cache_entry)

            # Fetch appropriate data from server HTTP response
            response_data = get_data(cache_dir, cache_entry.response_location, cache_entry.response_size)
            read_http_response(str(response_data), cache_entry)

            cache_entry.entry_location = entry[0]
            cache_entry.last_accessed_time = entry[1]
            cache_entry.last_modified_time = entry[2]
            cache_entry.rankings_location = entry[3]

    for i in cache_temp_list2:
        for j in cache_temp_list1:
            if j.url in i.range_url:
                j.partial_entry_created_time = i.partial_entry_created_time
                j.range_url = i.range_url
                j.range_url_length = i.range_url_length
                j.range_url_location = i.range_url_location
                j.content_size = i.content_size
                j.content_location = i.content_location
                cache_list.append(j)
                break

    cache_temp_list1.clear()
    cache_temp_list2.clear()

    for entry in cache_list:
        filename, extension = get_filename(entry.content_type, entry.url)
        content = get_data(cache_dir, entry.content_location, entry.content_size)
        content_to_file(content, filename, extension, dump_dir, entry)

        if content is not None:
            recovered += 1

    empty_entries = all_entries - recovered
    return cache_list, all_entries, recovered, empty_entries, reconstructed


# Read all cache addresses and control data from the rankings file
def read_rankings(cache_dir):
    ranking_list = []

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
                entry_created_time = hex_time_convert(int(entry[8:15][::-1].hex(), 16))
                address = read_entry(entry[24:28][::-1].hex())
                objects = (address, last_access_time, entry_created_time, ("data_0", offset))
                ranking_list.append(objects)
                i += 1
            offset += 36
    return ranking_list


def read_entry(content_address):
    resource_location = ()

    # Find and fetch data from appropriate location
    if content_address[0] == "a":
        block_num = int(content_address[4:8], 16)
        block_offset = 8192 + (block_num * 256)
        resource_location = ("data_1", block_offset)
    elif content_address[0] == "b":
        block_num = int(content_address[4:8], 16)
        block_offset = 8192 + (block_num * 1024)
        resource_location = ("data_2", block_offset)
    elif content_address[0] == "c":
        block_num = int(content_address[4:8], 16)
        block_offset = 8192 + (block_num * 4096)
        resource_location = ("data_3", block_offset)
    elif content_address[0] == "8":
        resource_location = ("f_" + content_address[2:8], 0)
    return resource_location
