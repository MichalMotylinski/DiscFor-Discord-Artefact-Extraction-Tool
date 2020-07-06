# List of standard library imports
from os import listdir, walk, makedirs
from os.path import dirname, join
from pathlib import Path
import sys
from shutil import copytree, copy2, Error
from time import strftime, perf_counter


# List of local imports
from activity import get_activity_data
from maincache import read_cache_entry
from report import chat_to_html, report_cache, report_activity
from simplecache import read_simple_cache


# This is main script containing functions run at the start of the program
# Functions from other scripts are called from here


# Main menu function is the starting point of DiscFor.
def main_menu():
    home_path = str(Path.home())
    output_dir = ""
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
                # Check how program is run
                if getattr(sys, "frozen", False):
                    # If tool is run as executable file
                    output_path = dirname(sys.executable)
                else:
                    # If tool is run as a script
                    output_path = sys.path[0]
            else:
                # Ensure that full path is taken
                if sys.path[0] not in output_path:
                    output_path = join(sys.path[0], output_path)
            discord_path = system_search(home_path)

            recovery(discord_path, output_path)
        except FileNotFoundError:
            print("Incorrect path structure")
        main_menu()
    elif selection == "2":
        print("\nPlease provide path for extraction")

        target_path = input()
        if target_path or target_path == "":
            # Check if structure of a directory given by user is correct
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

        main_menu()
    elif selection == "3":
        exit()
    else:
        print("Invalid choice. Enter 1-3")
        main_menu()


# Function searching file system for Discord directory
def system_search(search_dir):
    print("\nSearching system...")
    discord_path = ""

    # Generate files and directories of current file system
    # Traverse generated directory tree in search of Discord folder
    for root, dirs, files in walk(search_dir):
        for directory in dirs:
            if directory.lower() == "discord":
                directory_content = listdir(join(root, directory))
                if "Cache" and "Local Storage" in directory_content:
                    discord_path = join(root, directory)
                    print("\nDiscord folder found under:\n" + discord_path)
                    decision = ""
                    while decision != "y" and decision != "n" and decision != "yes" and decision != "no":
                        print("\nType [y/yes] to accept the result or [n/no] to continue search:")
                        decision = input()
                    if decision == "y" or decision == "yes":
                        break
                    elif decision == "n" or decision == "no":
                        discord_path = None
                        continue
        if discord_path:
            return discord_path
    if not discord_path:
        return print("\nDiscord folder not found"), main_menu()


# Create dump directories for output of the program
def create_recovery_dir(discord_path, output_path, backup):
    output_dir = ""
    # Check if Discord files are locked by application
    try:
        # File index appears in all Discord distributions. Check if its set to read-only state.
        with open(join(discord_path, "Cache", "index"), "rb"):
            in_use = False
    except Error and PermissionError:
        in_use = True

    if in_use is False:
        current_time = strftime("%Y%m%d%H%M%S")
        output_dir = join(output_path, f"Dump_{current_time}")
        makedirs(join(output_dir, "Extracted", "Images"))
        makedirs(join(output_dir, "Extracted", "Chat_logs"))
        makedirs(join(output_dir, "Extracted", "Video"))
        makedirs(join(output_dir, "Extracted", "Audio"))
        makedirs(join(output_dir, "Extracted", "Other"))
        makedirs(join(output_dir, "Reports", "Chat_logs"))

        if backup:
            discord_path = create_backup(discord_path, output_dir)
    else:
        print("Permission denied, please close discord.")
        main_menu()
    return output_dir, discord_path


def create_backup(discord_path, output_dir ):
    makedirs(join(output_dir, "Dumps"))
    cache_path = join(discord_path, "Cache")
    # Copy Discord cache directory with all of its content
    copytree(cache_path, join(output_dir, "Dumps", "Cache"))
    activity_path = join(discord_path, "Local Storage")
    copytree(activity_path, join(output_dir, "Dumps", "Local Storage"))
    return join(output_dir, "Dumps")


# Three phases of recovery are called from here.
# Creation of output directory, actual extraction of data and reports creation.
def recovery(discord_path, output_path):
    decision = ""
    output_dir = ""
    backup_time = 0
    while decision != "y" and decision != "n" and decision != "yes" and decision != "no":
        print("\nDo you want to create data backup? (y/n or yes/no)")
        decision = input().lower()
        if decision != "y" and decision != "n" and decision != "yes" and decision != "no":
            print("\nWrong input")
        if decision == "y" or decision == "yes":
            backup = True
            print("\nCreating data backup...")
            backup_start = perf_counter()
            output_dir, discord_path = create_recovery_dir(discord_path, output_path, backup)
            backup_time = round((perf_counter() - backup_start), 2)
            print("Backup created successfully in: ", backup_time, "s")
        else:
            backup = False
            output_dir, discord_path = create_recovery_dir(discord_path, output_path, backup)

    recovery_start = perf_counter()
    # Check what structure is used (Disk Cache or Simple Cache) and call appropriate function
    if "data_0" and "data_1" and "data_2" and "data_3" in listdir(join(discord_path, "Cache")):
        print("\nBeginning data extraction...")
        cache_data_list, all_entries, recovered, empty_entries, reconstructed = read_cache_entry(discord_path, output_dir)
    else:
        print("\nBeginning data extraction...")
        cache_data_list, all_entries, recovered, empty_entries, reconstructed = read_simple_cache(discord_path, output_dir)
    servers, channels, mails = get_activity_data(discord_path)
    recovery_time = round((perf_counter() - recovery_start), 2)
    print("Data recovery completed successfully in: ", recovery_time, "s")
    print("\nCreating reports...")
    reporting_start = perf_counter()
    chat_to_html(cache_data_list, output_dir)
    report_cache(cache_data_list, output_dir)
    report_activity(servers, channels, mails, output_dir)
    reporting_time = round((perf_counter() - reporting_start), 2)
    print("Reporting completed successfully in: ", reporting_time, "s")
    print("\nDiscFor completed extraction of Discord data.")
    print("Total number of entries found: ", all_entries)
    print("Files recovered: ", recovered)
    print("Empty or partial entries: ", empty_entries)
    print("Reconstructed entries/files: ", reconstructed)
    print("Total time: ", str(round(backup_time + recovery_time + reporting_time, 2)), "s")
    print("\nYou can find results of extraction in:")
    print(output_dir, "\n")
    # Clear memory before ending current iteration
    for name in dir():
        if not name.startswith("_"):
            if name in globals():
                del globals()[name]
            if name in locals():
                del locals()[name]


# Start the program
main_menu()
