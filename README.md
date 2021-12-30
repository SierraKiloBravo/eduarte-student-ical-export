# eduarte-student-ical-export

This utility allows users (specifically, students) of Eduarte (a [https://iddinkgroup.com](Iddink Group product) for viewing school timetables and grades) to export timetables to iCal.

It uses Selenium for accessing the content.

**Please note:** Because scraping is a legal grey area, I would like to emphasize the following section of the GPLv2 license:

_IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES._

## Assumptions made

I made this program primarily for my personal use. As of such, I assume the following when obtaining calendar data, which may not be true in your situation:

* You have a working GeckoDriver setup.
* Logins to Eduarte are done via O365 SSO.
* Your browser locale is US English.

Contributions are welcome. If you want to add support for other usecases, feel free to do so!

## Configuration

Configuration is provided by a file named 'config.json' in the current working directory. A example is provided below (available in config.json.dist without annotations)

```
{
    "driver": "firefox", # only firefox is supported
    "authentication": {
        "type": "o365", # only o365 is supported
        "username": "student@example.org",
        "password": "3xAmPl3stuDENT!"
    },
    "endpoint": "https://fictional-school.educus.nl", # Where you would go to if you wanted to log in normally.
    "readahead_weeks": 5, # the amount of weeks to read ahead, including the current week.
    "output": "calendar.ics"
}
```

## Installation

$ `pip install -r requirements.txt`

$ `cp config.json.dist config.json`

$ `$EDITOR config.json`

$ `python export-calendar.py`

Installing GeckoDriver on your system is outside the scope of this readme document.