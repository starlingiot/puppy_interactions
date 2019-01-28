PuPPy Interactions
==================

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

###### Concept: 25 Jan 19
###### Private interaction logging for PuPPy Slack members

**Purpose**: Private interaction logging for PuPPy Slack members - keep track and manage your time!

##### Architecture

Serverless Django deployment to AWS Lambda and S3, made possible by Zappa and `s3sqlite` wrapper for the SQLite database over S3.

##### Features

* Log interactions with an individual or many individuals with one command in Slack chat
* Rate interactions during that meeting for each individual as `+` or `-`
* See your logs in Slack: over time by interacton, aggregated by person, or aggregated by time period
* Opt-out command to delete all of your interactions

##### Commands

`/interaction` - basic command to invoke the app.

**Log an interaction**: `/interactions @don +`.

* Multi-person Alternative: `/interactions @don + @Maelle + Random Guy -`.

**See your logs**: `/interactions` - default is all meetings for 30 days. Note no trailing text.

* Change timespan: `/interactions 90` - see 90 days of logs.
* Aggregates: `/interactions [90] person` or `/interactions [90] time`.
* Filters: `/interactions +` or `/interactions -` - return only positive or negative interactions


**Clear your logs**: `/interactions clear` - delete all your interaction logs. Does not require confirmation.

**See these commands**: `/interactions help` - see what's available (help text)

**Alias**: We will respond the same way to `/interaction` (singular).

##### User Interface

**Input**: Slack chat!

**Output**: 

* New interactions: acknowledged in the channel from which the command was invoked. "Got it! You're <xx>% for positive interactions in the last 30 days."
* See logs: popup window with logs.
* Clear logs: acknowledged in the channel from which the command was invoked. "Thanks! Your interaction logs are cleared."

##### Privacy

This app, by its nature, will store indentifying data. The main example is the Slack `user_id` required to log an interaction - for the logger and the loggee. A more insidious form of identifying data is the compiled record of encounters between individuals. While we can't remove the requirement for `user_id` or holding the interaction logs (that's the point), we can take some mitigating steps:

* Open source, non-nefarious design/code.
* Slack is deprecating usernames. That means less "human readable" identifying information. 
* Decline to store additional Slack-provided info like `channel` or `workspace` identifiers.
* Opt-in use with single step opt-out-anytime feature.

### Deployment

The following details how to deploy this application.


