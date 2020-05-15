# List of standard library imports
from os.path import dirname, join
from os import listdir, walk, makedirs
from shutil import copytree, copy2, Error
from time import strftime, perf_counter
from pathlib import Path
import sys

# List of local imports
from activity import get_activity_data
from maincache import read_cache_entry
from report import chat_to_html, report_cache, report_activity
from simplecache import read_simple_cache


def main_menu():
    # Main menu function
    home_path = str(Path.home())
    print("===================================================")
    print("DISCFOR MAIN MENU")
    print("===================================================")
    print("1. Extraction from current file system")
    print("2. Select folder for extraction")
    print("3. Quit")
    selection = input("\nEnter choice: ")
    if selection == "1":
        print("\nPlease provide output path")
        output_path = input()
        try:
            if not output_path:
                if getattr(sys, "frozen", False):
                    output_path = dirname(sys.executable)
                else:
                    output_path = sys.path[0]
            else:
                if sys.path[0] not in output_path:
                    output_path = join(sys.path[0], output_path)
            discord_path = system_search(home_path)
            recovery(discord_path, output_path)
        except FileNotFoundError:
            print("Incorrect path structure")
        main_menu()
    elif selection == "2":
        print("\nPlease provide path for extraction")
        try:
            target_path = input()
        # print("\nIncorrect file/folder/volume syntax\n")
            if target_path or target_path == "":
                if "Cache" and "Local Storage" in listdir(target_path):
                    print("Please provide output path")
                    output_path = input()
                    if not output_path:
                        if getattr(sys, "frozen", False):
                            output_path = dirname(sys.executable)
                        else:
                            output_path = sys.path[0]
                    else:
                        if sys.path[0] not in output_path:
                            output_path = join(sys.path[0], output_path)
                    recovery(target_path, output_path)
                else:
                    print("\nThis is not a Discord directory or something is missing")
                    print("Following folders are required:")
                    print("Cache\n" + join("Local Storage", "leveldb\n"))
        except FileNotFoundError:
            print("Incorrect path structure")
        main_menu()
    elif selection == "3":
        exit()
    else:
        print("Invalid choice. Enter 1-3")
        main_menu()


def system_search(search_dir):
    print("\nSearching system...")
    discord_path = ""
    for root, dirs, files in walk(search_dir):
        for directory in dirs:
            if directory.lower() == "discord":
                directory_content = listdir(join(root, directory))
                if "Cache" and "Local Storage" in directory_content:
                    discord_path = join(root, directory)
                    break
        if discord_path:
            print("\nDiscord folder found under:\n" + discord_path)
            return discord_path
    if not discord_path:
        return print("Discord folder not found"), main_menu()


# Create dump directories
def create_dump(discord_path, output_path):
    output_dir = ""
    try:
        with open(join(discord_path, "Cache", "index"), "rb"):
            in_use = False
    except Error and PermissionError:
        in_use = True

    if in_use is False:
        current_time = strftime("%Y%m%d%H%M%S")
        output_dir = join(output_path, f"Dump_{current_time}")
        makedirs(join(output_dir, "Dumps"))
        makedirs(join(output_dir, "Extracted", "Images"))
        makedirs(join(output_dir, "Extracted", "Chat_logs"))
        makedirs(join(output_dir, "Extracted", "Video"))
        makedirs(join(output_dir, "Extracted", "Audio"))
        makedirs(join(output_dir, "Extracted", "Other"))
        makedirs(join(output_dir, "Reports", "Chat_logs"))

        cache_path = join(discord_path, "Cache")
        copytree(cache_path, join(output_dir, "Dumps", "Cache"))
        activity_path = join(discord_path, "Local Storage", "leveldb")
        for file in listdir(activity_path):
            if ".log" in file:
                copy2(join(activity_path, file), join(output_dir, "Dumps", file))
                break
    else:
        print("Permission denied, please close discord.")
        main_menu()
    return output_dir


def recovery(discord_path, output_path):
    print("\nCreating data backup...")
    backup_start = perf_counter()
    output_dir = create_dump(discord_path, output_path)
    backup_end = perf_counter()
    print("Backup created successfully in: ", round((backup_end - backup_start), 2), "s")
    recovery_start = perf_counter()
    if "data_0" and "data_1" and "data_2" and "data_3" in listdir(join(output_dir, "Dumps", "Cache")):
        print("\nBeginning data extraction...")
        cache_data_list, all_entries, recovered, empty_entries, reconstructed = read_cache_entry(output_dir)
    else:
        print("\nBeginning data extraction...")
        cache_data_list, all_entries, recovered, empty_entries, reconstructed = read_simple_cache(output_dir)
    servers, channels, mails = get_activity_data(output_dir)
    recovery_end = perf_counter()
    print("Data recovery completed successfully in: ", round((recovery_end - recovery_start), 2), "s")
    print("\nCreating reports...")
    reporting_start = perf_counter()
    chat_to_html(cache_data_list, output_dir)
    report_cache(cache_data_list, output_dir)
    report_activity(servers, channels, mails, output_dir)
    reporting_end = perf_counter()
    print("Reporting completed successfully in: ", round((reporting_end - reporting_start), 2), "s")
    print("\nDiscFor completed extraction of Discord data.")
    print("Total number of entries found: ", all_entries)
    print("Files recovered: ", recovered)
    print("Empty or partial entries: ", empty_entries)
    print("Reconstructed entries/files: ", reconstructed)
    print("Total time: ", round((reporting_end - backup_start), 2), "s")
    print("\nYou can find results of extraction in:")
    print(output_dir, "\n")
    for name in dir():
        if not name.startswith("_"):
            if name in globals():
                del globals()[name]
            if name in locals():
                del locals()[name]


main_menu()
