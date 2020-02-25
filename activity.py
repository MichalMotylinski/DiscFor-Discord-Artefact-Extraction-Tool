import os
import re


def find_mail(output_dir):
    # Read data from activity log file
    server_list = []
    channel_list = []
    mail_list = []
    for file in os.listdir(output_dir + "/Dumps"):
        if ".log" in file:
            with open(output_dir + "/Dumps/" + file, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
                all_list = re.findall(r"(?:$|\W)([0-9]{1,18})\":(?:$|\W)([0-9]{1,18})", data)
                for i in all_list:
                    if not i[0] in server_list:
                        server_list.append(i[0])
                    if not i[1] in channel_list:
                        channel_list.append(i[1])
                mail_list = re.findall(r"([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)", data)
    return server_list, channel_list, mail_list
