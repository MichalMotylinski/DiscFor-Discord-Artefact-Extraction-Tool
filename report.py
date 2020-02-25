import csv
import json


def write(cache_data_list, output_dir):
    # Produce report in json and csv formats
    with open("data.json", "w") as f:
        json.dump(cache_data_list, f)

    with open("data.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "URL", "Range URL", "Content Type", "File Size", "Last Accessed",
                         "Cache Entry Created", "Last Modified", "Expire Time", "Response Time", "User Timezone",
                         "Cache Entry Location", "Response Location", "File Location", "Content Encoding", "ETag",
                         "Max Age", "Server Response", "Server Name", "Server IP", "URL Length", "Range URL Length",
                         "MD5", "SHA1", "SHA256"])
        for x in cache_data_list:
            writer.writerow([x["Filename"], x["URL"], x["Range URL"], x["Content Type"], x["File Size"],
                             x["Last Accessed"], x["Cache Entry Created"], x["Last Modified"], x["Expire Time"],
                             x["Response Time"], x["User Timezone"], x["Cache Entry Location"], x["Response Location"],
                             x["File Location"], x["Content Encoding"], x["ETag"], x["Max Age"], x["Server Response"],
                             x["Server Name"], x["Server IP"], x["URL Length"], x["Range URL Length"], x["MD5"],
                             x["SHA1"],  x["SHA256"]])
