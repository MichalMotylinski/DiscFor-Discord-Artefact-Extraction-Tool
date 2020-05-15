from os.path import join
from os import listdir
from re import findall


def get_activity_data(output_dir):
    # Read data from activity log file
    server_list = []
    channel_list = []
    mail_list = []
    for file in listdir(join(output_dir, "Dumps")):
        if ".log" in file:
            with open(join(output_dir, "Dumps", file), "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
                # Find all email addresses, server IDs and channel IDs
                mail_list = findall(r"([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)", data)
                all_list = findall(r"([0-9]+|null)\":\"([0-9]+|null)", data)
                for i in all_list:
                    if not i[0] in server_list and i[0] != "null":
                        server_list.append(i[0])
                    if not i[1] in channel_list and i[1] != "null":
                        channel_list.append(i[1])
    return server_list, channel_list, mail_list
