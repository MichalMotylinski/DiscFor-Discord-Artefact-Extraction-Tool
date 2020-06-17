# List of standard library imports
from csv import writer
from json import dump, load
from os import listdir
from os.path import join, exists


# This script contains functions responsible for creation of reports


# Create reports for data recovered from cache
def report_cache(cache_data_list, output_dir):
    # Produce report in json format
    with open(join(output_dir, "Reports", "cache_data.json"), "w") as f:
        dump(cache_data_list, f)

    # Produce report in csv format
    with open(join(output_dir, "Reports", "cache_data.csv"), "w", newline="") as f:
        write_data = writer(f)
        write_data.writerow(["Filename", "URL", "Range URL", "Content Type", "File Size", "Last Accessed",
                             "Cache Entry Created", "Last Modified", "Expire Time", "Response Time", "User Timezone",
                             "Cache Entry Location", "Response Location", "File Location", "Content Encoding", "ETag",
                             "Max Age", "Server Response", "Server Name", "Server IP", "URL Length", "Range URL Length",
                             "MD5", "SHA1", "SHA256"])
        for e in cache_data_list:
            write_data.writerow([e["Filename"], e["URL"], e["Range URL"], e["Content Type"], e["File Size"],
                                 e["Last Accessed"], e["Cache Entry Created"], e["Last Modified"], e["Expire Time"],
                                 e["Response Time"], e["User Timezone"], e["Cache Entry Location"],
                                 e["Response Location"], e["File Location"], e["Content Encoding"], e["ETag"],
                                 e["Max Age"], e["Server Response"], e["Server Name"], e["Server IP"], e["URL Length"],
                                 e["Range URL Length"], e["MD5"], e["SHA1"], e["SHA256"]])


# Create report for data recovered from activity log
def report_activity(servers, channels, mails, output_dir):
    elements = max(len(servers), len(channels), len(mails))
    # Fill lists with dashes to avoid index errors
    for i in range(0, elements):
        if len(servers) < elements:
            servers.append("-")
        if len(channels) < elements:
            channels.append("-")
        if len(mails) < elements:
            mails.append("-")
        i += 1
    if elements:
        with open(join(output_dir, "Reports", "activity_data.csv"), "w", newline="") as f:
            write_data = writer(f)
            write_data.writerow(["Servers", "Channels", "Mails"])
            x = 0
            while x < elements:
                write_data.writerow([servers[x], channels[x], mails[x]])
                x += 1


# Create chat log reports in form of HTML files
def chat_to_html(cache_data_list, output_dir):
    logs_dir = join(output_dir, "Extracted", "Chat_logs")
    chat_list = listdir(logs_dir)
    chat_list.sort()

    # Check if chat log contains more than one conversation.
    for file in chat_list:
        with open(join(logs_dir, file), "r") as f:
            data = load(f)
        if "messages" in data:
            # If more than one conversation found, move them to separate files
            for e in data["messages"]:
                i = 0
                if exists(join(logs_dir, f"{e[0]['channel_id']}.json")):
                    while exists(join(logs_dir, f"{e[0]['channel_id']} ({i}).json")):
                        i += 1
                    with open(join(logs_dir, f"{e[0]['channel_id']} ({i}).json"), "w") as f2:
                        dump(e, f2)
                else:
                    with open(join(logs_dir, f"{e[0]['channel_id']}.json"), "w") as f2:
                        dump(e, f2)
    # Recover messages from chat logs and create conversation reports
    for file in chat_list:
        messages = ""
        avatar_path = ""
        url = ""
        att_path = ""
        img_url = ""
        filename = file.split(".", 1)[0]
        # Create structure of HTML file
        # Indentation rule is broken here to save space in the final reports
        html_struct = f"""<!DOCTYPE html>
<html>
<head>
<style>
table, th, td{{border: 1px solid black;}}
</style>
</head>
<body>
<h1>Channel Id: {filename}</h1>
%s
</body>
</html>
"""
        with open(join(logs_dir, file), "r") as f:
            data = load(f)
        # Reading elements of a message
        if any("channel_id" in s for s in data):
            for e in data:
                avatar = e["author"]["avatar"]
                if avatar is not None:
                    if exists(join(output_dir, "Extracted", "Images", f"{avatar}.webp")):
                        avatar_path = join(output_dir, "Extracted", "Images", f"{avatar}.webp")
                date = e["timestamp"].split("T", 1)[0]
                time = e["timestamp"].split("T", 1)[1].split(".", 1)[0]
                timestamp = date + " " + time

                if len(e["attachments"]) > 0:
                    url = e["attachments"][0]["url"].split("attachments", 1)[1]
                    for key in cache_data_list:
                        if url in key["URL"]:
                            att_file = key["Filename"]
                            img_url = key["URL"]
                            if exists(join(output_dir, "Extracted", "Images", att_file)):
                                att_path = join(output_dir, "Extracted", "Images", att_file)
                                break
                # Filling structure of a message with recovered data
                message = f"""<table width="100%">
<tr><th width="30%" align="center">Message Id</th><td>{e["id"]}</td><th>Time</th><td width="30%">{timestamp}</td></tr>
<tr><th rowspan="3">Author</th>
<th>Id</th><td>{e["author"]["id"]}</td>
<td rowspan="3"><img src="{avatar_path}" alt="{e["author"]["avatar"]}" width="50px" height="50px"></td></tr>
<tr><th>Username</th><td>{e["author"]["username"]}</td></tr>
<tr><th>Discriminator</th><td>{e["author"]["discriminator"]}</td></tr>
<tr width="100%"><th>Content</th><td colspan="3">{e["content"]}</td></tr>
<tr><td colspan="4" align="center"><img src="{att_path}" alt="{url}" class="center"></td></tr>
<tr><td colspan="4" align="center">{img_url}</td></tr>
</table>
<br/>
"""
                # Reconstruction of conversation by adding single messages together
                messages = messages + message
        if not messages == "":
            # Pasting conversation into HTML report structure and saving all in a new file
            html_file = html_struct % messages
            with open(join(output_dir, "Reports", "Chat_logs", filename + ".html"), "w", encoding="utf-8") as report:
                report.write(html_file)
