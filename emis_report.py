#!/usr/bin/env python3

import emis.http

def day_in(day, days):
    for d in days:
        if isinstance(d, list):
            return d[0] <= day <= d[1]
        else:
            return day == d
    return False

def date_in(dt, defs):
    year = str(dt.year)
    month = str(dt.month)
    day = dt.day
    return (year in defs and month in defs[year] and day_in(day, defs[year][month]))

def is_weekend(dt):
    wd = dt.weekday()
    return wd == 5 or wd == 6

def is_holiday(dt, holidays, workdays):
    return ((is_weekend(dt) or date_in(dt, holidays)) and
            not date_in(dt, workdays))

def find_student_id(name, students):
    for s in students:
        if name == s['FullName']:
            return s['studId']
    return None

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
                    help='Account configuration file (JSON)')
    ap.add_argument('--holiday', type=str, required=True,
                    help='Holiday configuration file (JSON)')
    ap.add_argument('--workday', type=str, required=True,
                    help='Work day configuration file (JSON)')
    ap.add_argument('--sickleave', type=str, required=True,
                    help='Sick leave configuration file (JSON)')
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
    with open(args.sickleave) as f:
        sickleaves = json.load(f)

    # Report
    with open(args.logfile, 'w') as f:
        print('<html><head><meta charset="utf-8"/><title>EMIS Report</title></head>', file=f)
        print('<body style="font-family: monospace">', file=f)
        for account in accounts:
            now = datetime.datetime.now()
            log(f, '<hr><b>{}</b> Report for user <b>{}</b>'.format(now, account['username']))
            if is_holiday(now, holidays, workdays):
                log(f, '<font color=#ff00ff>Holidy, no need to report</font>')
            else:
                try:
                    http = emis.http.Http(logger=lambda x: log(f, x))
                    http.login(account['username'], account['password'])
                    teacher = http.get_teacher_name()
                    log(f, 'Teacher=<font color=#ff8800><b>{}</b></font>'.format(teacher))
                    http.get_school_tree()
                    r = http.get_student_absense_report()
                    if int(r['Total']) > 0:
                        log(f, '<font color=#ff00ff>Already submitted</font>')
                    else:
                        class_id = http.get_class_id()
                        log(f, 'ClassID=<b>{}</b>'.format(class_id))
                        r = http.report_absense(class_id)
                        sickleaves_in_class = [x for x in sickleaves if x['teacher'] == teacher]
                        if sickleaves_in_class:
                            students = http.get_students()
                            log(f, 'Total <b>{}</b> students'.format(len(students)))
                            for sl in sickleaves_in_class:
                                stud_id = find_student_id(sl['name'], students)
                                if stud_id is None:
                                    log(f, 'Student <b>{}</b> not found'.format(sl['name']))
                                else:
                                    http.sick_leave(class_id, stud_id, sl['description'])
                                    log(f, 'Sick leave for <b>{}</b>: {}'.format(sl['name'], sl['description']))
                        log(f, '<font color=#008800>DONE</font>'.format())
                except Exception as e:
                    log(f, '<font color=#ff0000>{}</font>'.format(e))
        print('</body>', file=f)
        print('</html>', file=f)
