import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from pytz import timezone
import pause

from gcalendar import add_events

la_timezone = timezone("America/Los_Angeles")

url = "https://simons.berkeley.edu/programs-events/public-lectures#nav-upcoming"

zoom_url = "https://berkeley.zoom.us/j/95040632440"
previous_jsons_dir = "jsons/previous_events.json"


def get_main_website(url: str):
    while url.count("/") > 2:
        url = url.rsplit("/", 1)[0]
    return url


def main():
    # Use requests to get the html for this url
    response = requests.get(url)
    html = response.text

    main_site_url = get_main_website(url)

    # Use BeautifulSoup to parse the html
    soup = BeautifulSoup(html, "html.parser")

    # Get all divs inside the div with the class "views-row"
    events = soup.find_all(class_="views-row")

    event_jsons = []

    # Loop through each event
    for event in events:
        ## Get the time of the event in all elements with the class "time"
        time_elements = event.find_all(class_="datetime")

        # Get the starting and ending time in string format
        starting_datetime_str = time_elements[0]["datetime"]
        ending_datetime_str = time_elements[1]["datetime"]

        # Convert the string to a datetime object
        starting_datetime = parser.parse(starting_datetime_str)
        ending_datetime = parser.parse(ending_datetime_str)

        # Convert the datetime to the local timezone
        starting_datetime = starting_datetime.astimezone(la_timezone)
        ending_datetime = ending_datetime.astimezone(la_timezone)

        # Ignore events that have already happened
        # NOTE: this would only miss events that have been added during the day and are taking place in the same day.
        #       (Assuming a 24-hour cycle of checking for new events)
        if starting_datetime < datetime.now().astimezone(la_timezone):
            continue

        # Get the title of the event
        title_element = event.find(class_="card__title")
        title = title_element.text
        title = title.strip()

        # Get the description of the event by using the href inside the title
        event_url = title_element.find("a")["href"]

        # Get the html for the event page
        event_page_html = requests.get(main_site_url + event_url).text
        event_page_soup = BeautifulSoup(event_page_html, "html.parser")

        # Get the description of the event
        description_element = event_page_soup.find(
            class_="event-series--event__main-content"
        )

        # Get the description of the event
        description = description_element.text
        description = description.strip()

        # Remove any text after the first instance of three "="
        description = description.split("===")[0]

        is_quantum = "quantum" in title.lower()

        # Create the event json
        event_json = {
            "summary": title,
            "location": zoom_url,
            "description": description,
            "start": {
                "dateTime": starting_datetime.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
            "end": {
                "dateTime": ending_datetime.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
            "reminders": {"useDefault": True},
        }

        # Add the event json to the list of event jsons
        event_jsons.append(event_json)

        # Load the previous events from the json file
        with open(previous_jsons_dir, "r") as f:
            previous_events = json.load(f)

        # Get the ids of the previous events
        previous_event_ids = [event["summary"] for event in previous_events]

        # Get rid of the events that have already been added
        event_jsons = [
            event for event in event_jsons if event["summary"] not in previous_event_ids
        ]

        # Add the new events to the json database
        previous_events.extend(event_jsons)

        # Save the new events to the json database
        with open(previous_jsons_dir, "w") as f:
            json.dump(previous_events, f)

        # Add the events to the calendar
        add_events(event_jsons)


if __name__ == "__main__":
    while True:
        main()

        # Wait until the next day to check for new events
        start_of_today = datetime.now().astimezone(la_timezone).replace(hour=0, minute=0, second=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        pause.until(start_of_tomorrow)

