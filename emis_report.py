#!/usr/bin/env python3

import emis.http

def day_in(day, days):
    """Check whether a given day is in given days.
    Arguments:
    day    -- Datetime object represents the day to be checked.
    days   -- List of single days, each element could be either.
              * A integer represents day of month (1..31)
              * A 2-element-list represents day range ([begin, end] inclusive)
    return -- True if given day in given day ranges.
    """
    for d in days:
        if (isinstance(d, list) and d[0] <= day <= d[1]) or day == d:
                return True
    return False

def date_in(dt, defs):
    """Check whether a given date is in date collection.
    Arguments:
    dt     -- Date to be checked.
    defs   -- Date collection.
    return -- True if given date is in date collection.
    """
    year = str(dt.year)
    month = str(dt.month)
    day = dt.day
    return (year in defs and month in defs[year] and day_in(day, defs[year][month]))

def is_weekend(dt):
    """Check whether a given date is weekend (Saturday or Sunday).
    Arguments:
    dt     -- Date to be checked.
    return -- True if given date is weedend.
    """
    wd = dt.weekday()
    return wd == 5 or wd == 6

def is_day_off(dt, holidays, workdays, work_on_saturday):
    """Check whether a given date is a day off (no reporting needed).
    Arguments:
    dt               -- Date to be checked.
    holidays         -- Holidays definitions.
    workdays         -- Workday definitions(working weekends etc).
    work_on_saturday -- Saturday as work day.
    """
    if not is_weekend(dt) and not date_in(dt, holidays):
        return False
    if date_in(dt, workdays):
        return False
    if work_on_saturday and dt.weekday() == 5 and not date_in(dt, holidays):
        return False;
    return True

def find_student_id(name, students):
    """Find ID of student by given student name.
    Arguments:
    name -- Student name.
    students -- List of student records(usually returned by 'get_students').
    """
    for s in students:
        if name == s['FullName']:
            return s['studId']
    return None

def log(f, s):
    """Print log messages on console and into given file.
    Arguments:
    f -- A file object into which the log message will be printed.
    s -- The log message.
    """
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
    ap.add_argument('--work-on-saturday', default=False, action='store_true',
                    help='Mark Saturday as work day.')
    ap.add_argument('--sickleave', type=str, required=True,
                    help='Sick leave configuration file (JSON)')
    ap.add_argument('--logfile', type=str, required=True,
                    help='Log filename')
    ap.add_argument('--dryrun', default=False, action='store_true',
                    help='Dry run, do not submit anything')
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
            log(f, '<hr><b>{}</b> Report for user "<b>{}</b>".'.format(now, account['username']))
            if is_day_off(now, holidays, workdays, args.work_on_saturday):
                log(f, '<font color=#ff00ff>Holidy, no need to report.</font>')
            else:
                try:
                    http = emis.http.Http(logger=lambda x: log(f, x))
                    http.login(account['username'], account['password'])
                    teacher = http.get_teacher_name()
                    log(f, 'Teacher="<font color=#ff8800><b>{}</b></font>".'.format(teacher))
                    http.get_school_tree()
                    r = http.get_absense_report()
                    if int(r['Total']) > 0:
                        log(f, '<font color=#ff00ff>Already submitted.</font>')
                    else:
                        class_id = http.get_class_id()
                        log(f, 'Class ID="<b>{}</b>".'.format(class_id))
                        if args.dryrun:
                            log('<font color=#00ffff>Dry run, absense not submitted.</font>')
                        else:
                            http.report_absense(class_id)
                        sickleaves_in_class = [x for x in sickleaves if x['teacher'] == teacher]
                        if sickleaves_in_class:
                            students = http.get_students()
                            log(f, 'Total <b>{}</b> students.'.format(len(students)))
                            for sl in sickleaves_in_class:
                                stud_id = find_student_id(sl['name'], students)
                                if stud_id is None:
                                    log(f, 'Student "<b>{}</b>" not found.'.format(sl['name']))
                                else:
                                    if args.dryrun:
                                        self._log('<font color=#00ffff>Dry run, sick leave not submitted.</font>')
                                    else:
                                        http.sick_leave(class_id, stud_id, sl['description'])
                                    log(f, 'Sick leave for "<b>{}</b>": "{}".'.format(sl['name'], sl['description']))
                        log(f, '<font color=#008800>DONE</font>'.format())
                except Exception as e:
                    log(f, '<font color=#ff0000>{}</font>'.format(e))
        print('</body>', file=f)
        print('</html>', file=f)
