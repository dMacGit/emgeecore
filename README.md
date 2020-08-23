# Emgeecore - Backend for (Media Grabber) application


[![Release](https://img.shields.io/github/release/dmacgit/emgeecore.svg)](https://github.com/dMacGit/emgeecore/releases/latest) [![Commit](https://img.shields.io/github/tag/dmacgit/emgeecore.svg)](https://github.com/dMacGit/emgeecore/tags/latest)

### __*An automated way to backup your media collection to your computer*__

*This is the backend logic which runs the frontend [Media Grabber Application](https://github.com/dMacGit/Media_Grabber).*

## Table of Contents

- [General Info](#General-Info)
- [Technologies](#Technologies)
- [Setup](#Setup)
- [How to Use](#How-to-Use)
- [Future Plans](#Future-Plans)
- [Status](#Status)

## General Info

This application runs the Backend Server, which contains the core logic to Automate Ripping, and Encoding a DVD or CD to a target location.
Uses the `Makemkv-cli` 3rd Party API to rip a disc title once detected.

It keeps track of jobs via job-files, which include source-device ID's, media ID's and job ID's. Also keeps track of if the job is ripped or encoded for example. 

### *This is Still work in progress.*


## Technologies

- Python 3
- [Makemkv](https://www.makemkv.com/) (**3rd Party API**) 
- [Meta-Core](https://github.com/dMacGit/meta_core) (**Another Personal Project**)

## Setup

1. Clone the Repository into your chosen/target directory
2. Navagate to the directory and open the Terminal. Install the requirements by running this command: `pip3 install -r requirements.txt`

## How To Use

1. To run the application Run: `python main.py` in the terminal. 
2. `CTRL + C` to exit the app.

## Future Plans

By the end of the project, I hope to have the followoing features.

* Scanning of CD's, DVD's and Blu Rays on insert for meta data.
* Parsing media meta data.
* Compatibility with, and interfacing to multiple connected optical media devices at once.
* Using 3rd party application/projects to automate backingup media.
* Offloading to 3rd party applications/projects for further processing.
* Keeping logs based on device/disc/backup job etc.
* Compatibity with Front end [Media Grabber Application](https://github.com/dMacGit/Media_Grabber).

## Status

### - Active Deveopment