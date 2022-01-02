"""Copyright (C) 2021 SierraKiloBravo
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; version 2.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA."""
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import authentication
import datetime
from time import sleep
import icalendar
import uuid
import re

# Read config file from current working directory
with open('./config.json', 'rb') as _config_file:
    config = json.load(_config_file)

if config['driver'] == "firefox":
    driver = webdriver.Firefox()
else:
    raise ValueError(
        "Unknown driver {} defined in config".format(config['driver']))

if config['authentication']['type'] == "o365":
    auth = authentication.O365Authentication(driver)
else:
    raise ValueError("Unknown authentication method {} defined in config".format(
        config['authentication']['type']))

# Load the endpoint URL which should redirect us to the authentication page immidiately
driver.get(config['endpoint'])
sleep(1)  # Wait a second for the page to load, entering the credentials before the page has completely loaded will result in no login occuring
auth.login(config['authentication']['username'],
           config['authentication']['password'])

# If we didn't fail we should be at the home page, greeting us and showing us the time of the next timetable entry.
# "Goedemorgen $firstname! Maandag 9 januari begin je om 08:15."
# We now have a session, go to the /agenda page.
driver.get(config['endpoint'] + "/agenda")

# Get last monday's date, and start reading timetables from there.
today = datetime.date.today()
first_monday_of_week = today - datetime.timedelta(days=today.weekday())

sleep(2)  # Wait a second for all redirections to take place

# This will store all calendar items, as a intermediary. We will process this afterwards.
calendaritems = []

for x in range(1, int(config['readahead_weeks'])):
    # Enter the date into the date picker. The html ID's are named like shit (i.e. id123 instead of anything descriptive).
    # id13 is the input field attached to the date picker at the top of the page
    date_entry = driver.find_element(By.XPATH, '//*[@id="ida"]')

    print("Reading from date {}".format(
        first_monday_of_week.strftime("%d-%m-%Y")))
    # The scraped site is apparently REALLY sensitive about the contents of the date input field.
    # Running .clear() on date_entry causes a server side (yes, I'm serious) NullPointerException.
    # For this reason, we need to manually press backspace 10 times (because the date is formatted as "MM-DD-YYYY")
    for x in range(0, 10):
        date_entry.send_keys(Keys.BACKSPACE)
    date_entry.send_keys(first_monday_of_week.strftime("%d-%m-%Y"))
    date_entry.send_keys(Keys.RETURN)
    sleep(0.3)
    days = driver.find_elements_by_class_name("agenda--day")

    weekday = 0  # Start on the current day
    for day in days:
        current_date = first_monday_of_week + datetime.timedelta(days=weekday)
        # Iterate over days found in the current week.

        courses = day.find_elements_by_class_name("agenda--course")
        courses += day.find_elements_by_class_name("agenda--appointment")
        # A 'course' differs from a 'appointment'. Appointments are used (in my case) for exams.
        # They differ slightly, so we need to edit them slightly further ahead to create the same 'intermediary' in calendaritems.

        for course in courses:
            course_meta = {'date': str(current_date)}

            course.click()
            # Clicking on a course makes a popup open. Its class is 'ide'.
            course_popover = driver.find_element(By.XPATH, '//*[@id="ide"]')
            course_popover_title = driver.find_element(
                By.CLASS_NAME, 'popover-title').find_element(By.TAG_NAME, 'h2').text
            course_popover_content = driver.find_element(
                By.CLASS_NAME, 'popover-content').find_element(By.CLASS_NAME, 'popover--panel')

            # The course information is not stored in some way that it can be easily parsed in a key-value sense
            # No, it instead is a long list of <dt> and <dd> tags as children of .popover-content .popover--panel.
            # Wtf?
            popover_children = course_popover_content.find_elements_by_css_selector(
                "*")

            next_key = None
            for child in popover_children:
                if child.tag_name == "dt":
                    if child.text == "Vak":
                        next_key = 'subject'
                    elif child.text == "Locatie":
                        next_key = 'location'
                    elif child.text == 'Met':
                        next_key = 'attendee'
                    elif child.text == 'Omschrijving':
                        next_key = 'description'
                    elif child.text == 'Tijd':
                        next_key = 'time'
                elif child.tag_name == 'dd':
                    # check if the child has children of its own
                    child_children = child.find_elements_by_css_selector("*")
                    value = ""
                    # Check if the current element has children of its own.
                    # Process them into a string or list as needed.
                    if len(child_children) != 0:
                        if next_key == 'attendee':
                            # Process attendees into a list.
                            # Every attendee's class name or name is a separate span.
                            value = []
                            for child_child in child_children:
                                if child_child.text != ',':
                                    # Comma's are also separate spans. Ignore them.
                                    value.append(child_child.text)
                        else:
                            for child_child in child_children:
                                value += child_child.text
                    else:
                        value = child.text
                    course_meta[next_key] = value
            if 'subject' not in course_meta:
                # probably a appointment, use title instead
                course_meta['subject'] = course_popover_title

            if 'description' not in course_meta:
                course_meta['description'] = course_popover_title

            # Close the popover, otherwise we can not click on the next course.
            close_btn_row = course_popover.find_element(
                By.CLASS_NAME, 's5-btn-row')
            buttons = close_btn_row.find_elements(By.TAG_NAME, 'a')

            # Count the amount of buttons. If there are two, there is one called 'Sluit' and 'Les'.
            # 'Sluit' will close the popover, 'Les' opens a separate page with information about the course.
            # The 'Les' button is only present for courses.
            # In my case this page doesn't contain anything we couldn't parse from the current page already,
            # but its URL does contain (what seems to be) a unique identifier.
            if len(buttons) == 2:
                course_meta['uid'] = buttons[1].get_attribute(
                    'href').split('/')[-1]
                # The 'les' button is present, use the value from the URL as a UID
            else:
                # no 'les' button, probably a appointment, make something up
                course_meta['uid'] = str(uuid.uuid1())

            # Click on the first button. It should be 'close'.
            buttons[0].click()
            calendaritems.append(course_meta)

        weekday += 1

    # Add 7 days before continuing (or ending) the loop, so that the next iteration will start at the next calendar week
    first_monday_of_week = first_monday_of_week + datetime.timedelta(days=7)
    sleep(0.1)

driver.close()  # close the window when we're done

cal = icalendar.Calendar()
for entry in calendaritems:
    event = icalendar.Event()

    event['uid'] = "student-calendar-"+entry['uid']
    event['location'] = entry['location']
    event['attendee'] = entry['attendee']
    event['summary'] = entry['subject']
    event['description'] = entry['description']

    # Parse 'date' ('yyyy-mm-dd') and 'time' (i.e. "8:30 - 10:00 (lesuur 2 t/m 4)" or 
    # "8:30 - 08:15 (lesuur 2)", we need to parse it) to a datetime object
    print(entry['time'])
    match_time_re = re.match(
        "^(\d?\d:\d\d) - (\d?\d:\d\d) uur \(lesuur (\d+) ?t?/?m? ?(\d+)?\)$", entry['time'])
    if not match_time_re:
        # There is a better way to do this. I couldn't find that way in time though.
        match_time_re = re.match(
            "^(\d?\d:\d\d) - (\d?\d:\d\d) uur()()$", entry['time'])
        # Appointments are not attached to 'lesuren'. If this is an appointment, the string
        # will only look like '13:37 - 15:37 uur'. The two empty capture groups are there
        # so that the amount of groups matches the first regex match, otherwise time_parse 
        # can't be defined (zip() would raise a ValueError probably)

    match_time_parse = match_time_re.groups()

    time_parse = dict(
        zip(['begin', 'end', 'begin_hourid', 'end_hourid'], match_time_parse))
    # Create a dictionary from the parsed time we created in match_time_parse using given keys

    begin_datetime = datetime.datetime.strptime("{} {}:00".format(
        entry['date'], time_parse['begin']), "%Y-%m-%d %H:%M:%S")
    event['dtstart'] = icalendar.vDatetime(begin_datetime)
    end_datetime = datetime.datetime.strptime("{} {}:00".format(
        entry['date'], time_parse['end']), "%Y-%m-%d %H:%M:%S")
    event['dtend'] = icalendar.vDatetime(end_datetime)
    cal.add_component(event)

with open(config['output'], 'wb') as output_file:
    output_file.write(cal.to_ical())
