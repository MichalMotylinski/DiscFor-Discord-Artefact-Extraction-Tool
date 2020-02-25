import gzip
import hashlib
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from os.path import splitext, basename

content_type_list = []
extension_list = []
cache = []


def read_extensions():
    # Read file containing supported extensions
    with open("Extensions.txt") as ext_file:
        for line in ext_file:
            if not line.startswith("#"):
                row = line.split()
                content_type_list.append(row[0])
                extension_list.append(row[-1])


def hex_time_convert(time_in_microseconds):
    epoch = datetime(1601, 1, 1)
    dirty_time = epoch + timedelta(microseconds=time_in_microseconds)
    date, hmr = str(dirty_time).split(" ", 1)
    date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    hmr = hmr.split(".", 1)[0]
    clean_time = date + " " + hmr
    return clean_time


def get_filename(content_type, resource_content_size, url_data, cache_data_list):
    filename = ""
    file_extension = ""
    if not resource_content_size == 0:
        for e in content_type_list:
            if content_type == e:
                file_extension = extension_list[content_type_list.index(e)]
        dis = urlparse(url_data)
        name, ext = splitext(basename(dis.path))

        count = sum(name in x.get("Filename") for x in cache_data_list)
        if count == 0:
            filename = name + file_extension
        else:
            filename = name + " (" + str(count) + ")" + file_extension
    return filename


def read_http_response(http_response_data):
    server_response = ""
    status = ""
    content_type = ""
    etag = ""
    response_time = ""
    last_modified = ""
    max_age = ""
    server_name = ""
    expire_time = ""
    content_encoding = ""
    server_ip = ""
    timezone = ""

    if http_response_data:
        string_start = http_response_data.lower().find("http")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            server_response = http_response_data[string_start:string_end]

        string_start = http_response_data.lower().find("status:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            status = http_response_data[string_start:string_end].split(":", 1)[1]

        string_start = http_response_data.lower().find("content-type:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            content_type = http_response_data[string_start:string_end].split(":", 1)[1]
            if ";" in content_type:
                content_type = content_type.split(";", 1)[0]

        string_start = http_response_data.lower().find("etag:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            etag = http_response_data[string_start:string_end].split(":", 1)[1]

        string_start = http_response_data.lower().find("date:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            response_time = http_response_data[string_start:string_end].split(":", 1)[1].strip()
            if not response_time == "":
                response_time, timezone = time_convert(response_time, timezone)

        string_start = http_response_data.lower().find("last-modified:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            last_modified = http_response_data[string_start:string_end].split(":", 1)[1].strip()
            if not last_modified == "":
                last_modified, timezone = time_convert(last_modified, timezone)

        string_start = http_response_data.lower().find("max-age=")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            max_age = http_response_data[string_start:string_end].split("=", 1)[1].split(",", 1)[0]

        string_start = http_response_data.lower().find("server:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            server_name = http_response_data[string_start:string_end].split(":", 1)[1]

        string_start = http_response_data.lower().find("expires:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            expire_time = http_response_data[string_start:string_end].split(":", 1)[1].strip()
            if not expire_time == "":
                expire_time, timezone = time_convert(expire_time, timezone)

        string_start = http_response_data.lower().find("content-encoding:")
        if not string_start == -1:
            string_end = http_response_data.find("\\x00", string_start)
            content_encoding = http_response_data[string_start:string_end].split(":", 1)[1]

        server_ip = re.findall(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}", http_response_data)[0]

    return server_response, status, content_type, etag, response_time, last_modified, max_age, server_name, \
           expire_time, timezone, content_encoding, server_ip


def month_convert(month):
    month_num = ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i in months:
        if month == i:
            if months.index(i) + 1 < 10:
                month_num = "0" + str(months.index(i) + 1)
            else:
                month_num = str(months.index(i) + 1)
    return month_num


def time_convert(time, timezone):
    old_time = time.split(" ")
    if len(old_time) < 5:
        new_time = ""
    else:
        date = old_time[1] + "/" + month_convert(old_time[2]) + "/" + old_time[3]
        new_time = date + " " + old_time[4]
        if timezone == "":
            timezone = old_time[5]
    return new_time, timezone


def extract_file(resource_data, filename, output_dir, content_encoding):
    extracted_dir = output_dir + "/Extracted/"

    if content_encoding == "gzip":
        resource_data = gzip.decompress(resource_data)
    # Brotli is not supported by python3. Use separate script to decode file encoded in brotli
    """elif content_encoding == "br":
        resource_data = brotli.decompress(resource_data)"""

    with open(extracted_dir + filename, "w+b") as carve:
        carve.write(resource_data)

    blocksize = 65536
    md5_hasher = hashlib.md5()
    sha1_hasher = hashlib.sha1()
    sha256_hasher = hashlib.sha256()
    with open(extracted_dir + filename, "rb") as calc:
        buf = calc.read(blocksize)
        while len(buf) > 0:
            md5_hasher.update(buf)
            sha1_hasher.update(buf)
            sha256_hasher.update(buf)
            buf = calc.read(blocksize)
    md5 = md5_hasher.hexdigest()
    sha1 = sha1_hasher.hexdigest()
    sha256 = sha256_hasher.hexdigest()
    return md5, sha1, sha256
