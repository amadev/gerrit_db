import os
import requests
import json
import shutil
import datetime
import logging


host = 'https://review.openstack.org/'
change_url = 'changes/%s/detail/'
# Gerrit has limit of changes we can get via API (500). To overcome that limit
# changes are gotten by period. The following changes determines on what
# number of requests the whole process will be splitted.
num_of_periods = 7
period_length = 7  # in days
dt_format = '%Y-%m-%d %H:%S:%M'
data_dir = '/home/amadev/.gerrit_db/'


def calc_periods(num_of_periods, period_length):
    curr = datetime.datetime.now()
    curr = curr.replace(hour=23, minute=59, second=59, microsecond=0)
    periods = []
    for i in range(num_of_periods):
        end = curr
        start = curr - datetime.timedelta(days=(period_length - 1))
        start = start.replace(hour=0, minute=0, second=0)
        periods.append([start, end])
        curr -= datetime.timedelta(days=period_length)
    return periods


def remove_first_line(text):
    return '\n'.join(text.split('\n')[1:])


def load_changes(start, end):
    conditions = [
        'status:open',
        'project:openstack/nova']
    conditions.append('after:"%s"' % start.strftime(dt_format))
    conditions.append('before:"%s"' % end.strftime(dt_format))
    logging.debug('Getting changes with conditions %s', conditions)
    r = sess.get(
        host + 'changes/',
        params={'q': ' '.join(conditions)})
    data = remove_first_line(r.text)
    if not data:
        return
    fn = 'raw/all-%s-%s.json' % (
        start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d'))
    fn = os.path.join(data_dir, fn)
    f = open(fn, 'w')
    f.write(data.encode('utf8'))
    f.close()

    jdata = json.load(open(fn))

    for change in jdata:
        r = sess.get(host + change_url % change['id'])
        data = remove_first_line(r.text)
        fn = 'raw/%s.json' % change['change_id']
        fn = os.path.join(data_dir, fn)
        f = open(fn, 'w')
        f.write(data.encode('utf8'))
        f.close()


if __name__ == '__main__':
    raw_dir = os.path.join(data_dir, 'raw')
    if os.path.exists(raw_dir):
        shutil.rmtree(raw_dir)
    os.makedirs(raw_dir)
    sess = requests.Session()
    periods = calc_periods(num_of_periods, period_length)
    periods[-1][0] = datetime.date(1970, 1, 1)
    for period in periods:
        load_changes(*period)
