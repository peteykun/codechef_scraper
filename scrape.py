from HTMLParser import HTMLParser
from retrying import retry
import requests
import argparse
import sqlite3
import os

parser = argparse.ArgumentParser(description='Scrape codechef problem')
parser.add_argument('problem')
parser.add_argument('language')
parser.add_argument('-d', '--database', default='default.db')
parser.add_argument('-s', '--status', default='All')
parser.add_argument('-b', '--start', type=int, default=0)
args = parser.parse_args()

conn = sqlite3.connect(args.database)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS programs (
                 program_id integer NOT NULL,
                 datetime text NOT NULL,
                 user text NOT NULL,
                 result text NOT NULL,
                 time text NOT NULL,
                 memory text NOT NULL,
                 language text NOT NULL,
                 problem_code text NOT NULL,
                 code text NOT NULL,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 PRIMARY KEY(program_id)
             )''')

languages = {'C': 11,  'JAVA': 10, 'PYTH': 4, 'PYTH3': 116}
statuses  = {'WA': 14, 'AC': 15, 'TLE': 13, 'RTE': 12, 'CTE': 11}

payload = { 'language': languages[args.language], \
            'status': 'All', \
            'sort_by': 'Date/Time', \
            'sorting_order': 'asc', \
            'handle': '' }

if args.status is not 'All':
    payload['status'] = statuses[args.status]

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=5)
def retrying_get(url, params=None):
    r = requests.get(url, params=params)

    if r.status_code != requests.codes.ok:
        print 'Failed to get %s: HTTP %d' % (url, r.status_code)
        raise IOError('Unexpected response, expected OK')

    return r

r = retrying_get('https://www.codechef.com/status/%s' % args.problem, params=payload)

class ResultListParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and attrs.get('class') == '\\"kol\\"':
            self.active = True
            self.results.append([])
        if self.active and tag == 'span':
            self.results[-1].append(attrs['title'])
        if tag == 'div' and attrs.get('class') == 'pageinfo':
            self.grab_pages = True
    def handle_endtag(self, tag):
        if self.active and tag == 'tr':
            self.active = False
    def handle_data(self, data):
        if self.active and data != 'View':
            self.results[-1].append(data)
        if self.grab_pages:
            self.pages = int(data.split()[-1])
            self.grab_pages = False
    def feed(self, data):
        self.active = False
        self.results = []
        self.grab_pages = False
        self.pages  = None
        HTMLParser.feed(self, data)
        return self.results, self.pages

rl_parser  = ResultListParser()
_, pages = rl_parser.feed(r.text)

for page in range(args.start, pages):
    print 'Page %d/%d' % (page, pages)
    payload['page'] = page
    r = retrying_get('https://www.codechef.com/status/%s' % args.problem, params=payload)
    results, _   = rl_parser.feed(r.text)

    for item in results:
        print 'Processing', item[0]

        # Fetch the code
        try:
            code = rl_parser.unescape(retrying_get('https://www.codechef.com/viewplaintext/' + item[0]).text[5:-6])
        except IOError:
            print 'Giving up'

        # Insert into the database
        c.execute("INSERT INTO programs(program_id, datetime, user, result, time, memory, language, problem_code, code)  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(item + [args.problem, code]))

    # Write changes to disk at the end of each page
    conn.commit()

conn.close()
        
