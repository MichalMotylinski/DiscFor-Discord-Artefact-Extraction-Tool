# DiscordExtractor
Digital Artefact Extraction Tool for Discord Application

Developed as part of my B.Sc. (Hons.) Dissertation entitled "Retrieval and analysis of digital artefacts from Discord local directories"

This tool automates the extraction of digital artefacts and data that can be found in Discord local files. 

The scripts were developed using only standard libraries and tested with Python3 only.

To use the tool simply run the following command: python3 discfor.py

Main menu allows you to choose one of the following options:
1. Extraction from current file system
2. Select folder for extraction
3. Quit

First option allows you to scan your file system in search of Discord folder. Data from local Discord files will be pulled and any digital artefacts extracted from local cache if directory is found.
Second option allows you to choose discord folder for extraction as well as output directory. (Script directory by default)

Information pulled from local files is stored in csv (for readability) and json (for further data manipulation)
All information is being stored in Dump[date of scan] folder.

This tool is for research purposes only.
