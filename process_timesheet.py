#!/bin/python

import argparse
import re
import fileinput

# constants
MAX_ALLOWED_WfH_RATIO = 0.7

# terminal colors
RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m' # called to return to standard terminal text color

# handling script arguments
arg_parser = argparse.ArgumentParser('process_timesheet.py')
arg_parser.add_argument('--input', dest='input', help='Input timesheet text file path', type=str)
arg_parser.add_argument('--upcoming_home_days', dest='upcoming_home_days', help='Number of upcoming Home Office days', type=int)
args = arg_parser.parse_args()

# regular expressions
regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')
regexWfH = re.compile(r'ganz.+Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)')
regexWfHpartial = re.compile(r'anteilige Mobilarbeit:\s+(?P<actualWorkTime>[\d.,]+)')
regexWfHthatWeek = re.compile(r'Wochenerfassung Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)')
regexWfO = re.compile(r'(?P<dayOfMonth>\d{2}) (?P<dayOfWeek>\w{2}).*(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5}).*(?P<overTime>[\d.,]{4,5})')
regexWfOtraining = re.compile(r'Weiterbildung\s+(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5})')
regexHoursPerDay = re.compile(r'IRTAZ.*\s+(?P<hoursPerDay>[\d.,]+)')

def get_hours_worked(match):
    return float(match.group('actualWorkTime').replace(',', '.'))

def get_req_hours_per_days(match):
    return float(match.group('hoursPerDay').replace(',', '.'))

# variables to store the results
timeframe = ""
resultWfH = 0
resultWfO = 0
requiredHoursPerDay = 0

# Process each line from input, whether from stdin or file
textInput = open(args.input, 'r') if args.input else fileinput.input()
for line in textInput:
    line = line.strip()
    if (match := regex_timeframe.search(line)):
        timeframe = match.groups()[0] + "-" + match.groups()[1]
    elif (match := regexWfO.search(line)):
        resultWfO += get_hours_worked(match)
    elif (match := regexWfOtraining.search(line)):
        resultWfO += get_hours_worked(match)
    elif (match := regexWfH.search(line)):
        resultWfH += get_hours_worked(match)
    elif (match := regexWfHpartial.search(line)):
        resultWfH += get_hours_worked(match)
    elif (match := regexWfHthatWeek.search(line)):
        resultWfH += get_hours_worked(match)
    elif (match := regexHoursPerDay.search(line)):
        requiredHoursPerDay = get_req_hours_per_days(match)
    # else:
    #     print("No match found for line:", line)

# Print out the results
# print("Result of WfH:", resultWfH)
# print("Result of WfO:", resultWfO)

# Calculate the percentage relation between WfH and WfO
if resultWfO != 0:
    total_hours = resultWfH + resultWfO
    percent_of_work_from_home =  resultWfH / total_hours * 100
    print(timeframe, ":")
    print("Work from Home: ", (RED if percent_of_work_from_home / 100 > MAX_ALLOWED_WfH_RATIO else GREEN) + "{:.2f}".format(percent_of_work_from_home) + "%" + RESET)
    print("Hours Home:\t", "{:.2f}".format(resultWfH))
    print("Hours Office:\t", "{:.2f}".format(resultWfO))
    print("Hours total:\t", "{:.2f}".format(total_hours))
    print("-----")
elif resultWfH > 0:
    print(timeframe, "Work from Home: 100%")
else:
    print("Unable to calculate percentage because neither WorkFromHome nor WorkFromOffice seem to have a value > 0\n")

# Calculate remaining target Office hours if provided
if args.upcoming_home_days:
    resultWfH += args.upcoming_home_days * requiredHoursPerDay
    requiredOfficeHours = (resultWfH + resultWfO) * (1 - MAX_ALLOWED_WfH_RATIO)
    targetWfO = requiredOfficeHours - resultWfO
    adjustedPercentOfWorkFromHome = resultWfH / (resultWfH + resultWfO) * 100
    print("Work from Home with additional {} days:\t".format(args.upcoming_home_days), (RED if adjustedPercentOfWorkFromHome >= MAX_ALLOWED_WfH_RATIO else GREEN) + "{:.2f}%".format(adjustedPercentOfWorkFromHome) + RESET)
    print("Remaining target Office hours:\t", (RED if targetWfO > 0.0 else GREEN) + "{:.1f}".format(round(targetWfO, 1)) + RESET)
