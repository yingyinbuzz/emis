# EMIS client
A simple script that automates absence reporting on EMIS.

## Installation
Main script `emis_report.py` could be invoked along with configuration JSON
files, either from command line or from a systemd service.

You could install  `emis_bot.service` and `emis_bot.timer` systemd services to
automatic the process, make sure to set correct `USER_NAME` and path of
configuration files.

## Dependencies:
* [requests](https://docs.python-requests.org/en/master)
