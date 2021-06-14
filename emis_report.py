#!/usr/bin/env python3

import emis.http

def find_date(dt, defs):
    year = str(dt.year)
    month = str(dt.month)
    day = dt.day
    return (year in defs and month in defs[year] and day in defs[year][month])

def is_weekend(dt):
    wd = dt.weekday()
    return wd == 5 or wd == 6

def is_holiday(dt, holidays, workdays):
    return ((is_weekend(dt) or find_date(dt, holidays)) and
            not find_date(dt, workdays))

def log(f, s):
    print('-- {}'.format(s))
    print('{}<br>'.format(s), file=f)

if __name__ == '__main__':
    import sys
    import json
    import argparse
    import datetime

    # Parse inputs
    ap = argparse.ArgumentParser(description='EMIS automation utility')
    ap.add_argument('--account', type=str, required=True,
                    help='Account definition file')
    ap.add_argument('--holiday', type=str, required=True,
                    help='Holiday definition file')
    ap.add_argument('--workday', type=str, required=True,
                    help='Work day definition file')
    ap.add_argument('--logfile', type=str, required=True,
                    help='Log filename')
    args = ap.parse_args()

    # Load configuration
    with open(args.account) as f:
        accounts = json.load(f)
    with open(args.holiday) as f:
        holidays = json.load(f)
    with open(args.workday) as f:
        workdays = json.load(f)

    # Report
    now = datetime.datetime.now()
    with open(args.logfile, 'w') as f:
        print('<html><head><title>EMIS Report</title></head>', file=f)
        print('<body style="font-family: monospace">', file=f)
        for account in accounts:
            log(f, '<hr><b>{}</b> Report for user <b>{}</b>'.format(now, account['username']))
            if is_holiday(now, holidays, workdays):
                log(f, '<font color=#ff00ff>Holidy, no need to report</font>')

                try:
                    http = emis.http.Http(logger=lambda x: log(f, x))
                    r = http.login(account['username'], account['password'])
                    class_id = http.fetch_class_id()
                    log(f, 'ClassId=<b>{}</b>'.format(class_id))
                except Exception as e:
                    log(f, '<font color=#ff0000>{}</font>'.format(e))
            else:
                pass
        print('</body>', file=f)
        print('</html>', file=f)