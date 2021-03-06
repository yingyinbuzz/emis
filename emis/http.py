
import re
import json
import random
import datetime
import requests

class Http:
    def __init__(self, logger=None):
        self.site = 'http://emis.jnjy.net.cn'
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.logger = logger
        self.session = requests.session()

    def _get(self, url):
        url = '{}{}'.format(self.site, url)
        r = self.session.get(url, headers=self.headers)
        if r.status_code != requests.codes.ok:
            raise Exception('Could not get page {}'.format(url))
        return r

    def _post(self, url, data):
        url = '{}{}'.format(self.site, url)
        r = self.session.post(url, headers=self.headers, data=data)
        if r.status_code != requests.codes.ok:
            raise Exception('Could not post on {}'.format(url))
        return r

    def _log(self, msg):
        """Log given message.
        Arguments:
        msg -- The message to be logged.
        """
        if self.logger:
            self.logger(msg)

    def login(self, username, password):
        """Login into EMIS with given user name and password.

        Arguments:
        username -- User name.
        password -- Password.
        """
        # GET /Login.aspx to get coookies
        r = self._get('/Login.aspx')
        # Get captcha from cookies
        rand_str = ''.join((str(random.randint(0, 9)) for x in range(10)))
        url = '/Ajax/CodeImg.aspx?ImgWidth=100&ImgHeight=30&Fitness=100&t={}'.format(rand_str)
        r = self._get(url)
        if 'CheckCode' not in r.cookies:
            raise Exception('Captcha not found in cookies')
        captcha = r.cookies['CheckCode']
        self._log('CAPTCHA=<b>{}</b>'.format(captcha))
        # Login
        data = {'jsonType': 'LoginServer',
                'lt': 1,
                'u': username,
                'p': password}
        r = self._post('/Ajax/Default.ashx', data)
        return r.text

    def get_school_tree(self):
        """Fetch current school information from EMIS.

        Arguments:
        return -- A dict object represents school information.
        """
        data = {'MethodName': 'GetEmisSchoolTree'}
        r = self._post('/ControlCenter/Controllers/Default.ashx', data)
        return json.loads(r.text)

    def get_absense_report(self):
        """Fetch student absense report from EMIS.
        Arguments:
        return -- Absense report information in JSON format.
        """
        now = datetime.datetime.now().strftime('%Y/%m/%d')
        data = {'MethodName': 'GetStudentAbsentFind',
                'bSubDate': now,
                'page': 1,
                'pagesize': 50,
                'sortname': 'AbsentID',
                'sortorder': 'asc'}
        r = self._post('/ControlCenter/AdminEMIS/Controllers/Default.ashx',
                       data)
        return json.loads(r.text)

    def get_teacher_name(self):
        """Get name of current teacher that logged in.
        Arguments:
        return -- Teacher name of current class.
        """
        r = self._get('/ControlCenter/Welcome.aspx')
        m = re.search(r'labelusername">(?P<teacher>[^\(]*)', r.text)
        return m.group('teacher') if m is not None else None

    def get_class_id(self):
        """Get class ID of current class.
        Arguments:
        return -- Current class ID.
        """
        r = self._get('/ControlCenter/AdminEMIS/Students/Student_ClassManager.aspx')
        m = re.search(r'ClassID\s*=\s*(?P<classId>[^;\s]+)', r.text)
        if m is None:
            raise Exception('Class ID not found')
        return m.group('classId')

    def get_students(self):
        """Get list of students of current class.
        Arguments:
        return -- List of student records in JSON format.
        """
        data = {'MethodName': 'GetStudent',
                'isMyClass': 1,
                'GroupId': '',
                'SearchValues': '',
                'page': 1,
                'pagesize': 90,
                'sortname': 'stuID',
                'sortorder': 'asc'}
        r = self._post('/ControlCenter/AdminEMIS/Controllers/Default.ashx',
                       data)
        jo = json.loads(r.text)
        return jo['Rows']

    def report_absense(self, class_id):
        """Submit an absense report to EMIS without any sick leave.
        The whole class is reported as present.
        """
        data = {'MethodName': 'UpClassAllStudentAbsent',
                'ClassID': class_id}
        r = self._post('/ControlCenter/AdminEMIS/Controllers/Default.ashx?MethodName=UpClassAllStudentAbsent', data)
        return r.text

    def sick_leave(self, class_id, student_id, description):
        """Submit an sick leave for given student

        Arguments:
        class_id    -- Class ID for the student.
        student_id  -- Student ID.
        description -- Sick leave description.
        """
        data = {'MethodName': 'SetStudentAbsent',
                'StudentID': student_id,
                'ClassID': class_id,
                'columnname': 'AbsentTypeName',
                'NewValue': 1}
        r = self._post('/ControlCenter/AdminEMIS/Controllers/Default.ashx', data)
        data = {'MethodName': 'SetStudentAbsent',
                'StudentID': student_id,
                'ClassID': class_id,
                'columnname': 'Description',
                'NewValue': description}
        r = self._post('/ControlCenter/AdminEMIS/Controllers/Default.ashx', data)
        return r.text
