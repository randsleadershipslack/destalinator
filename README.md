# destalinator

Code for managing Cleanup of Stale Channels

This is a fork of [randsleadershipslack/destalinator](https://github.com/randsleadershipslack/destalinator) configured to run on Amazon Elastic Beanstalk.

## Components

### warner

The warner notifies channels that have been inactive for a period of time.

### archiver

The archiver archives channels that have been inactive for a period of time.

### announcer

The announcer will notify a channel of all new channels created within a period of time.

### flagger

The flagger uses a ruleset defined in a specific channel to perform actions such as notifying channels of messages that have received a certain number of reactions. See [flagger.md](flagger.md) for full details.

## Configuration

### Inside `configuration.yaml`

#### `warn_threshold` and `archive_threshold`

Tune these two variables to decide how long after inactivity a channel should be warned for inactivity and then subsequently archived.

#### `announce_channel`, `control_channel`, and `log_channel`

These three channels need to be manually created by you in your Slack.

### Required environment variables

#### `SLACK_NAME`

You'll want to change this to the name of your Slack.

#### `SB_TOKEN`

1. Make sure [the Slackbot app](https://slack.com/apps/A0F81R8ET-slackbot) is installed for your Slack
2. Add a Slackbot integration, and copy the `token` parameter from the URL provided

#### `API_TOKEN`

The easiest way to get an `API_TOKEN` is to [generate an OAuth test token](https://api.slack.com/docs/oauth-test-tokens).

It's not *nice*, but it's simple and avoids the whole callback-URL-oauth-request-app-creation dance.

#### `DESTALINATOR_ACTIVATED`

Destalinator can be chatty and make potentially big changes to a Slack team (by warning or archiving a large amount of channels), especially when first installed.

To minimize the risk of making a mistake, Destalinator will run in a dry-run mode unless the `DESTALINATOR_ACTIVATED` environment variable exists. Set it to any non-empty value and Destalinator is "active." If you want to remain in dry-run mode, ensure this variable is unset/does not exist.

## Running locally

```
DESTALINATOR_ACTIVATED="True"; export DESTALINATOR_ACTIVATED # Set to something other than True (or don't set) to run in dry mode (as noted above)

API_TOKEN="FILL_ME_IN"; export API_TOKEN # see above for explaination of API_TOKEN

SB_TOKEN="FILL_ME_IN"; export SB_TOKEN # see above

SLACK_NAME="FILL_ME_IN"; export SLACK_NAME # see above

. ./bin/activate # from the top-level directory -- this activates virtualenv -- `deactivate` exits virtualenv

pip install -r requirements.txt # Since we're in virtualenv, installs dependencies in ./lib

python ./warner # or ./archiver, ./announcer, ./flagger  with options: --debug --verbose
```

and if you want to leave dry-mode: `DESTALINATOR_ACTIVATED="True"; export DESTALINATOR_ACTIVATED`

Note: `virtualenv` is used to conveniently include Python package dependencies locally, and subsequently upload them directly to a server (rather than running `pip install` on the server)

## Running on Elastic Beanstalk

### Creating the EB Environment

1. Make sure you have the Elastic Beanstalk CLI installed
1. While running virtualenv (`. ./bin/activate`), use the following command to create a new environment:

```
eb init

eb create CHOOSE_SOME_NAME_FOR_YOUR_EB_ENV --tier worker --single --branch_default --envvars SB_TOKEN="CHANGE_ME",SLACK_NAME="CHANGE_ME",API_TOKEN="CHANGE_ME"
```

This will automatically create and deploy to the EB environment in dry-mode. _Note: for `flagger`, you need to look at the logs

When you've had a chance to test everything in dry-mode: `eb setenv DESTALINATOR_ACTIVATED="True"` to turn off dry-mode.

### Deploying to the EB Environment

`eb deploy` will deploy all files committed in git (add `--staged` to include staged changes)
