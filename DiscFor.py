import os
import shutil
import sys
import time
from sys import platform
from pathlib import Path

import activity
import maincache
import report
import simplecache
import common


def main_menu():
    # Main menu function
    home_path = str(Path.home())
    cache_data_list = []
    output_dir = ""
    print("1. Extraction from current file system")
    print("2. Select folder for extraction")
    print("3. Quit")
    selection = input("Enter choice: ")
    if selection == "1":
        print("Please provide output path")
        output_path = input()

        if not output_path:
            output_path = sys.path[0]
        if platform == "linux" or platform == "linux2":
            discord_path = system_search(home_path)
            output_dir = create_dump(discord_path, output_path)
            cache_data_list = simplecache.read_simple_cache(output_dir)
        elif platform == "darwin":
            print("Coming up soon...")
        elif platform == "win32" or platform == "win64":
            discord_path = system_search(home_path)
            output_dir = create_dump(discord_path, output_path)
            cache_data_list = maincache.read_cache_entry(output_dir)
        else:
            print("OS not supported")
            main_menu()
        report.write(cache_data_list, output_dir)
        main_menu()

    elif selection == "2":
        print("Please provide path for extraction")
        target_path = input()
        try:
            if target_path or target_path == "":
                if "Cache" and "Cookies" and "GPUCache" in os.listdir(target_path):
                    print("Please provide output path")
                    output_path = input()

                    if not output_path:
                        output_path = sys.path[0]
                    print(output_path)
                    print("Beginning extraction...")
                    output_dir = create_dump(target_path, output_path)
                    if "data_0" and "data_1" and "data_2" and "data_3" in os.listdir(output_dir + "/Dumps/Cache"):
                        cache_data_list = maincache.read_cache_entry(output_dir)
                    else:
                        cache_data_list = simplecache.read_simple_cache(output_dir)
                    servers, channels, mails = activity.find_mail(output_dir)
                    report.write(cache_data_list, output_dir)
                else:
                    print("This is not a Discord directory")
        except FileNotFoundError:
            print("Discord folder not found"), main_menu()

        main_menu()
    elif selection == "3":
        exit()
    else:
        print("Invalid choice. Enter 1-3")
        main_menu()


def system_search(search_dir):
    discord_path = ""
    for root, dirs, files in os.walk(search_dir):
        for directory in dirs:
            if directory == "discord":
                directory_content = os.listdir(os.path.join(root, directory))
                if "Cache" and "Cookies" and "GPUCache" in directory_content:
                    discord_path = os.path.join(root, directory)
                    break
        if discord_path:
            print("Discord folder found under:\n" + discord_path)
            print("Beginning extraction...")
            return discord_path
    if not discord_path:
        return print("Discord folder not found"), main_menu()


# Create dump directories
def create_dump(discord_path, output_path):
    current_time = time.strftime("%Y%m%d%H%M%S")
    output_dir = output_path + "/Dump_" + current_time
    os.makedirs(output_dir + "/Dumps")
    os.makedirs(output_dir + "/Images")
    os.makedirs(output_dir + "/Chat")
    os.makedirs(output_dir + "/Other")
    os.makedirs(output_dir + "/Extracted")

    cache_path = os.path.join(discord_path, "Cache")
    shutil.copytree(cache_path, output_dir + "/Dumps/Cache")
    if "Cookies" in os.listdir(discord_path):
        shutil.copyfile(discord_path + "/Cookies", output_dir + "/Dumps" + "/Cookies")
    else:
        print("Cookie file has not been found")
    for file in os.listdir(discord_path + "/Local Storage/leveldb"):
        if ".log" in file:
            shutil.copyfile(discord_path + "/Local Storage/leveldb/" + file, output_dir + "/Dumps/" + file)
    return output_dir


common.read_extensions()
main_menu()
