
import re
import random
import requests

class Http:
    def __init__(self, logger=None):
        self.site = 'http://emis.jnjy.net.cn'
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}
        self.logger = logger

    def _get(self, url):
        url = '{}{}'.format(self.site, url)
        r = requests.get(url, headers=self.headers)
        if r.status_code != requests.codes.ok:
            raise Exception('Could not get page {}'.format(url))
        return r

    def _post(self, url, data):
        url = '{}{}'.format(self.site, url)
        r = requests.post(url, headers=self.headers, data=data)
        if r.status_code != requests.codes.ok:
            raise Exception('Could not post on {}'.format(url))
        return r

    def _log(self, msg):
        if self.logger:
            self.logger(msg)

    def login(self, username, password):
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
        return r

    def fetch_class_id(self):
        r = self._get('/ControlCenter/AdminEMIS/Students/StudentAbsentList.aspx')
        print(r.text)
        m = re.search(r'ClassId\s*=\s*(?P<classId>[^"]+)', r.text)
        if m is None:
            raise Exception('Class ID not found')
        return m.group('classId')
