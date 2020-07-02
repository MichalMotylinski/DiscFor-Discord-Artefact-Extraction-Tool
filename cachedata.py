class Cache:
    def __init__(self, filename, url, range_url, content_type, content_size, last_accessed_time, entry_created_time,
                 last_modified_time, expiry_time, response_time, timezone, entry_location, url_location,
                 response_location, content_location, content_encoding, etag, max_age, server_response, server_name,
                 server_ip, url_length, range_url_length, md5, sha1, sha256):
        self.filename = filename
        self.url = url
        self.range_url = range_url
        self.content_type = content_type
        self.content_size = content_size
        self.last_accessed_time = last_accessed_time
        self.entry_created_time = entry_created_time
        self.last_modified_time = last_modified_time
        self.expiry_time = expiry_time
        self.response_time = response_time
        self.timezone = timezone
        self.entry_location = entry_location
        self.url_location = url_location
        self.response_location = response_location
        self.content_location = content_location
        self.content_encoding = content_encoding
        self.etag = etag
        self.max_age = max_age
        self.server_response = server_response
        self.server_name = server_name
        self.server_ip = server_ip
        self.url_length = url_length
        self.range_url_length = range_url_length
        self.md5 = md5
        self.sha1 = sha1
        self.sha256 = sha256
