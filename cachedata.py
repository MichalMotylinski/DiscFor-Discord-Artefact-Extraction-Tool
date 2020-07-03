class Cache:
    def __init__(self):
        # Name of the file
        self.__filename = ""

        # Cache entry location
        self.__entry_location = ""

        # URL data
        self.__url = ""
        self.__url_length = ""
        self.__url_location = ""
        self.__range_url = ""
        self.__range_url_length = ""
        self.__range_url_location = ""

        # Content data
        self.__content_size = ""
        self.__content_location = ""

        # Server HTTP response data
        self.__response_size = ""
        self.__response_location = ""

        # Time related data
        self.__last_accessed_time = ""
        self.__entry_created_time = ""
        self.__last_modified_time = ""
        self.__expiry_time = ""
        self.__response_time = ""
        self.__timezone = ""

        # Other data retrieved from server HTTP response
        self.__content_encoding = ""
        self.__etag = ""
        self.__max_age = ""
        self.__content_type = ""
        self.__server_name = ""
        self.__server_ip = ""

        # Hash values
        self.__md5 = ""
        self.__sha1 = ""
        self.__sha256 = ""

    # File name getter & setter
    @property
    def filename(self):
        return self.__filename

    @filename.setter
    def filename(self, filename):
        self.__filename = filename

    # Cache entry location getter & setter
    @property
    def entry_location(self):
        return self.__entry_location

    @entry_location.setter
    def entry_location(self, entry_location):
        self.__entry_location = entry_location

    # URL data getters & setters
    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url):
        self.__url = url

    @property
    def url_length(self):
        return self.__url_length

    @url_length.setter
    def url_length(self, url_length):
        self.__url_length = url_length

    @property
    def url_location(self):
        return self.__url_location

    @url_location.setter
    def url_location(self, url_location):
        self.__url_location = url_location

    @property
    def range_url(self):
        return self.__range_url

    @range_url.setter
    def range_url(self, range_url):
        self.__range_url = range_url

    @property
    def range_url_length(self):
        return self.__range_url_length

    @range_url_length.setter
    def range_url_length(self, range_url_length):
        self.__range_url_length = range_url_length

    @property
    def range_url_location(self):
        return self.__range_url_location

    @range_url_location.setter
    def range_url_location(self, range_url_location):
        self.__range_url_location = range_url_location

    # Content data getters and setters
    @property
    def content_size(self):
        return self.__content_size

    @content_size.setter
    def content_size(self, content_size):
        self.__content_size = content_size

    @property
    def content_location(self):
        return self.__content_location

    @content_location.setter
    def content_location(self, content_location):
        self.__content_location = content_location

    # Server HTTP response data getters and setters
    @property
    def response_size(self):
        return self.__response_size

    @response_size.setter
    def response_size(self, response_size):
        self.__response_size = response_size

    @property
    def response_location(self):
        return self.__response_location

    @response_location.setter
    def response_location(self, response_location):
        self.__response_location = response_location

    # Time related data getters and setters
    @property
    def last_accessed_time(self):
        return self.__last_accessed_time

    @last_accessed_time.setter
    def last_accessed_time(self, last_accessed_time):
        self.__last_accessed_time = last_accessed_time

    @property
    def entry_created_time(self):
        return self.__entry_created_time

    @entry_created_time.setter
    def entry_created_time(self, entry_created_time):
        self.__entry_created_time = entry_created_time

    @property
    def last_modified_time(self):
        return self.__last_modified_time

    @last_modified_time.setter
    def last_modified_time(self, last_modified_time):
        self.__last_modified_time = last_modified_time

    @property
    def expiry_time(self):
        return self.__expiry_time

    @expiry_time.setter
    def expiry_time(self, expiry_time):
        self.__expiry_time = expiry_time

    @property
    def response_time(self):
        return self.__response_time

    @response_time.setter
    def response_time(self, response_time):
        self.__response_time = response_time

    @property
    def timezone(self):
        return self.__timezone

    @timezone.setter
    def timezone(self, timezone):
        self.__timezone = timezone

    # Getters and setters for other data retrieved from server HTTP response
    @property
    def content_encoding(self):
        return self.__content_encoding

    @content_encoding.setter
    def content_encoding(self, content_encoding):
        self.__content_encoding = content_encoding

    @property
    def etag(self):
        return self.__etag

    @etag.setter
    def etag(self, etag):
        self.__etag = etag

    @property
    def max_age(self):
        return self.__max_age

    @max_age.setter
    def max_age(self, max_age):
        self.__max_age = max_age

    @property
    def content_type(self):
        return self.__content_type

    @content_type.setter
    def content_type(self, content_type):
        self.__content_type = content_type

    @property
    def server_name(self):
        return self.__server_name

    @server_name.setter
    def server_name(self, server_name):
        self.__server_name = server_name

    @property
    def server_ip(self):
        return self.__server_ip

    @server_ip.setter
    def server_ip(self, server_ip):
        self.__server_ip = server_ip

    # Hash values getters and setters
    @property
    def md5(self):
        return self.__md5

    @md5.setter
    def md5(self, md5):
        self.__md5 = md5

    @property
    def sha1(self):
        return self.__sha1

    @sha1.setter
    def sha1(self, sha1):
        self.__sha1 = sha1

    @property
    def sha256(self):
        return self.__sha256

    @sha256.setter
    def sha256(self, sha256):
        self.__sha256 = sha256
