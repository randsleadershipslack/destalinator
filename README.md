# destalinator
Code for managing Cleanup of Stale Channels

# Making it work in your environment
You'll need to install a few libraries: `pip install -r requirements.txt`

You'll also need to change configuration.yaml appropriately.  warner.py and archiver.py should then work from the command line.  Productionalized automated deployments and running on a schedule are left unspecified because every production environment is unique.

## Components

### warner

The warner notifies channels that have been inactive for a period of time.

### archiver

The archiver archives channels that have been inactive for a period of time.

### announcer

The announcer will notify a channel of all new channels created within a period of time.

### flagger

The flagger uses a ruleset defined in a specific channel to perform actions such as notifying channels of messages that have received a certain number of reactions.

## Setup

### Inside `configuration.yaml`

#### `slack_name`

You'll want to change this to the name of your Slack

#### `warn_threshold` and `archive_threshold`

Tune these two variables to decide how long after inactivity a channel should be warned for inactivity and then subsequently archived.

#### `general_message_channel`, `announce_channel`, `control_channel`, and `log_channel`

These channels need to be manually created by you in your Slack.

### Required environment variables

#### `SB_TOKEN`

1. Make sure [the Slackbot app](https://slack.com/apps/A0F81R8ET-slackbot) is installed for your Slack
2. Add a Slackbot integration, and copy the `token` parameter from the URL provided

#### `API_TOKEN`

The easiest way to get an `API_TOKEN` is to [generate an OAuth test token](https://api.slack.com/docs/oauth-test-tokens).

It's not *nice*, but it's simple and avoids the whole callback-URL-oauth-request-app-creation dance.

#### `DESTALINATOR_ACTIVATED`

Destalinator can be chatty and make potentially big changes to a Slack team (by warning or archiving a large amount of channels), especially when first installed.

To minimize the risk of making a mistake, Destalinator will run in a dry-run mode unless the `DESTALINATOR_ACTIVATED` environment variable exists. Set it to any non-empty value and Destalinator is "active." If you want to remain in dry-run mode, ensure this variable is unset/does not exist.
