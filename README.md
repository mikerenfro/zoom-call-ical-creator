# Mike's Quick and Dirty Zoom Call iCal Creator

I've hosted regularly-scheduled Zoom calls for an audience largely outside my workplace for a while, and though I can send calendar invites to that group's mailing list, I end up with tons of unwanted RSVP emails.

Also, if we end up needing to cancel a call, we don't have a good way to do that for everyone.

So, here's some Python code to create and update .ics files that can be sent to the audience on the mailing list.

## Requirements

- [`icalendar` Python module](https://pypi.org/project/icalendar/)
- [`PyYAML` Python module](https://pypi.org/project/PyYAML/6.0.1/)

## Instructions

Create a YAML file for your call(s). Structure of the YAML file:

```yaml
organization: Your Org Name
homepage: your.org.homepage.url
name: Regularly-Scheduled Organization Zoom Calls
summary: Regularly-Scheduled Organization Zoom Calls
call_types:
  - title: First Type of Call
    day_of_week: 1 # 0-indexed, so 1==Tuesday
    week_of_month: 1 # 0-indexed, so 1==second week
    hour: 14
    minute: 0
    duration: 50
    timezone: US/Central
    url: https://your.zoom.url/
    schedule:
      2026:
        - topic: ~ # January call gets a default title
        - topic: Some topic for February
        - topic: Some topic for March, with its own call document
          doc: https://url.to.call.document/
        - topic: false # April call is either not scheduled, or previously-scheduled April call is now cancelled
        # continue on through December as needed
  - title: Second Type of Call
    day_of_week: 1 # 0-indexed, so 1==Tuesday
    week_of_month: 2 # 0-indexed, so 1==second week
    hour: 14
    minute: 0
    duration: 50
    timezone: US/Central
    url: https://your.zoom.url/
    schedule:
      2026:
        # insert call topics and documents through December as needed
```

You should be able to add as many call types and years as needed. As shown in the example above:

- each type of call will occur on a particular week and day of the month (e.g., second Tuesday)
- each type of call can have its own Zoom or other conferencing URL
- a call with a topic of `~` will get a default event title matching the `call_types` `title` attribute
- a call with a topic of `false` will be skipped (if the call wasn't previously scheduled) or cancelled (if the call was previously scheduled)
- a call can have a Google doc or other link to an agenda, minutes, or other item.

Once you have your YAML file, you can run `zoom-ical-maker.py --ics ICS_FILE.ics YAML_FILE.yml` to create or update a `.ics` file with your events.

If you keep a current copy of the .ics file available, re-running the script will update the calendar entries without creating duplicates. It can also cancel existing entries, though your recipients **will** still need to delete the now-cancelled items from their calendars.
