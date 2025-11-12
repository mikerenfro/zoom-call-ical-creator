#!/usr/bin/env python
import argparse
import calendar
import datetime
import os
import zoneinfo

import icalendar
import yaml

# Read a user-specified yaml, and a corresponding .ics if one exists
# Each yaml file will contain a list of repeating calendar events, occurring on a particular day of week, week of month, time, duration, and URL.

def read_yaml_file(yaml_file):
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    return data

def read_ics_file(ics_file):
    with open(ics_file, 'r') as f:
        ics_calendar = icalendar.Calendar.from_ical(f.read())
    return ics_calendar

def create_calendar(data):
    cal = icalendar.Calendar()
    cal.calendar_name = data['name']
    prodid = f"-//{data['organization']}//{data['homepage']}//EN"
    cal.add("prodid", prodid)
    cal.add("summary", data['summary'])
    return cal

def create_call_event(call, year, month, call_type, homepage, ics_data, current_time_utc):
    # print(f"call = {call}")
    # print(f"call_type = {call_type}")
    title = call_type['title']
    day_of_week = call_type['day_of_week']
    week_of_month = call_type['week_of_month']
    hour = call_type['hour']
    minute = call_type['minute']
    duration = call_type['duration']

    url = call_type['url']
    topic = call['topic']
    status = None
    # If the topic is False, the calendar event for that day is cancelled (also, set the event status to CANCELLED). If the topic is None, we title the calendar event for that day with the name of the call. Otherwise, we title the calendar event for that day with the topic value.
    if topic == False:
        topic = 'CANCELLED'
        status = 'CANCELLED'
    if topic == None:
        topic = ''

    c = calendar.Calendar()
    meeting_date = list(filter(lambda d:d[3] == day_of_week and
                            d[1] == month,
                            c.itermonthdays4(year, month)))[week_of_month]
    meeting_year, meeting_month, meeting_day = meeting_date[0:3]
    timezone = zoneinfo.ZoneInfo(call_type['timezone'])
    event = icalendar.Event()

    # Use the date and time of the call as part of a UID for the event.
    yaml_event_uid = f'{meeting_year}{meeting_month:02d}{meeting_day:02d}{hour:02d}{minute:02d}@{homepage}'
    event.add('uid', yaml_event_uid)
    start = datetime.datetime(meeting_year, meeting_month, meeting_day,
                            hour, minute, 0, tzinfo=timezone)
    end = start + datetime.timedelta(minutes=duration)
    event.add('dtstart', start)
    event.add('dtend', end)
    # Use the call URL as the location for each event in the calendar.
    location = url
    event.add('location', location)
    # If the doc key exists, use its value in the summary of the call (something like f"Call document {doc}").
    call_doc = call.get('doc')
    description = None
    if call_doc is not None:
        description = f"Call document {call_doc}"
        event.add('description', description)
    if topic != None and topic != '':
        summary = f'{title}: {topic}'
    else:
        summary = title
    if status == 'CANCELLED':
        event.add('status', 'CANCELLED')
    event.add('summary', summary)

    # Start with a sequence (revision) of 0 for each event.
    sequence = 0
    if ics_data is not None:
        # If the .ics file exists, walk it for a list of existing events.
        for component in ics_data.walk(name='VEVENT'):
            if yaml_event_uid == str(component.get('uid')):
                # For any event from the .ics file that has a UID matching a UID in the generated call list, if any of the summary, description, URL, status (TODO: or any other attribute) of the event don't match the above generated list, increment the event sequence by 1. Also, set the last-modified date for this event to the current date and time.
                original_summary = str(component.get('summary'))
                original_description = str(component.get('description'))
                original_location = str(component.get('location'))
                original_status = str(component.get('status'))
                # if original_summary != summary and summary is not None:
                #     print(f"summary mismatch: '{summary}' vs '{original_summary}'")
                # if original_description != description and description is not None:
                #     print(f"summary mismatch: '{description}' vs '{original_description}'")
                # if original_location != location and location is not None:
                #     print(f"location mismatch: '{location}' vs '{original_location}'")
                # if original_status != status and status is not None:
                #     print(f"status mismatch: '{status}' vs '{original_status}'")
                if (original_summary != summary and summary is not None) or (original_description != description and description is not None) or (original_location != location and location is not None) or (original_status != status and status is not None):
                    original_sequence = int(component.get('sequence'))
                    sequence = max(original_sequence, sequence)+1
                    event.add('last-modified', current_time_utc)
    event.add('sequence', sequence)

    if sequence == 0 and status == 'CANCELLED':
        return None
    else:
        return event

def write_ics(calendar, ics_file):
    text = calendar.to_ical()
    text = text.replace(b'\r\n ', b'')  # not sure if I really need this
    with open(ics_file, "wb") as f:
        f.write(text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file", help="YAML file containing call types and topics")
    parser.add_argument("--ics", help=".ics file to write or update")
    args = parser.parse_args()

    now_utc = datetime.datetime.now(datetime.UTC)

    yaml_data = read_yaml_file(args.yaml_file)
    if args.ics and os.path.exists(args.ics):
        ical_data = read_ics_file(args.ics)
    else:
        ical_data = None

    cal = create_calendar(yaml_data)

    for call_type in yaml_data['call_types']:
        # print(topics)
        # https://stackoverflow.com/a/61133220
        # Each of those call_types will have a 'calls' hash. That hash will have keys of year numbers, and values of a list of hashes with a mandatory key of "topic" and an optional key of "doc". Usually, this list is 12 elements long, corresponding to 12 events for that year.
        for call_year, years_calls in call_type['schedule'].items():
            for call_month, call_event in enumerate(years_calls, 1):
                event = create_call_event(call_event, call_year, call_month, call_type, yaml_data['homepage'], ical_data, now_utc)
                if event:
                    cal.add_component(event)

    # At this point, we should have a current list of calls that are scheduled or cancelled, with updated last-modified and revision numbers. Write that list of calls out to a new .ics file with a date-time stamp in its filename.
    write_ics(cal, args.ics)
