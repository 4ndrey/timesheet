#!/bin/python

from datetime import datetime
import numpy
from urllib.request import urlopen
import json

currentMonth = datetime.now().strftime('%m')
currentYear = datetime.now().strftime('%Y')

holidays = json.loads(urlopen('https://digidates.de/api/v1/germanpublicholidays?year={}&region=de-by'.format(currentYear)).read())
startDate = currentYear + '-' + currentMonth
endDate = numpy.datetime64(startDate) + numpy.timedelta64(1, 'M')
businessDays = numpy.busday_count(startDate, endDate, holidays=list(holidays))
print("Working days in {}: {}".format(startDate, businessDays))
