# destalinator
Code for managing Cleanup of Stale Channels

[![Build Status](https://travis-ci.org/randsleadershipslack/destalinator.svg?branch=master)](https://travis-ci.org/randsleadershipslack/destalinator)

[![Coverage Status](https://coveralls.io/repos/github/randsleadershipslack/destalinator/badge.svg?branch=master)](https://coveralls.io/github/randsleadershipslack/destalinator?branch=master)

# Making it work in your environment
You'll need to install a few libraries: `pip install -r requirements.txt`

You'll also need to change `configuration.yaml` appropriately. `warner.py` and `archiver.py` should then work from the command line. Productionized automated deployments and running on a schedule are left unspecified because every production environment is unique.

That said, if you're running on Heroku, you can create a single `clock` process that runs `python scheduler.py`.

## AWS Lambda
You can also run Destalinator using AWS Lambda.

Steps
```
pip install -r requirements.txt -t . --upgrade
zip -r destalinator.zip .
```

Upload this folder to a Python 2.7 Lambda function. Use Lambda Environment Variables to control your configuration (See the Environment variables section below). Make sure to use the `RUN_ONCE=true` flag as well. Set the function handler to `scheduler.destalinate_lambda`. Also set the function timeout to 15 minutes. Finally, create a CloudWatch Events cron trigger to run your function once a day. Create a cron called `Daily` with the cron expression `cron(0 10 * * ? *)`.

NOTE: Destalinator logging is to a local file so the CloudWatch logs will be sparse. This can make debugging difficult.

# Development

We recommend using `virtualenv` to manage your development environment.

    pip install virtualenv
    virtualenv env
    source env/bin/activate

In addition to `requirements.txt`, there's also `build-requirements.txt` for development environments. `./bin/install` will install both.

### Docker

Build a local docker image:

    docker build . -t destalinator

#### Checking code coverage locally

    docker run -it -p 8080:80 destalinator sh -c "coverage html --skip-covered && python -m http.server 80"

    open http://localhost:8080/htmlcov/

## Components

### Warner

The Warner notifies channels that have been inactive for a period of time.

### Archiver

The archiver archives channels that have been inactive for a period of time.

### Announcer

The Announcer will notify a channel of all new channels created within a period of time.

### Flagger

The Flagger uses a ruleset defined in a specific channel to perform actions such as notifying channels of messages that have received a certain number of reactions.

## Setup

### Inside `configuration.yaml`

#### `slack_name`

You'll want to change this to the name of your Slack

#### `warn_threshold` and `archive_threshold`

Tune these two variables to decide how long after inactivity a channel should be warned for inactivity and then subsequently archived.

#### `general_message_channel`, `announce_channel`, `control_channel`, and `log_channel`

These channels need to be manually created by you in your Slack.

### Environment variables

All configs in `configuration.yaml` are overrideable through environment variables with the same name prefixed by `DESTALINATOR_` (e.g. `activated` -> `DESTALINATOR_ACTIVATED`). Set array environment variables (e.g. `DESTALINATOR_IGNORE_CHANNELS`) by comma delimiting items. If you only have one value for an array type environment variable add a training comma to denote the variable as a list.

#### `DESTALINATOR_SB_TOKEN` (Required)

1. Make sure [the Slackbot app](https://slack.com/apps/A0F81R8ET-slackbot) is installed for your Slack
2. Add a Slackbot integration, and copy the `token` parameter from the URL provided

#### `DESTALINATOR_API_TOKEN` (Required)

The best way to get an `API_TOKEN` is to [create a new Slack App](https://api.slack.com/apps/new).

Once you create and name your app on your team, go to "OAuth & Permissions" to give it the following permission scopes:

- `channels:history`
- `channels:read`
- `channels:write`
- `chat:write:bot`
- `chat:write:user`
- `emoji:read`
- `users:read`

After saving, you can copy the OAuth Access Token value from the top of the same screen. It probably starts with `xox`.

#### `DESTALINATOR_ACTIVATED` (Required)

Destalinator can be chatty and make potentially big changes to a Slack team (by warning or archiving a large amount of channels), especially when first installed.

To minimize the risk of making a mistake, Destalinator will run in a dry-run mode unless the `DESTALINATOR_ACTIVATED` environment variable exists. Set it to true and Destalinator is "active." If you want to remain in dry-run mode, ensure this variable is unset/does not exist.

#### `DESTALINATOR_LOG_LEVEL` (Optional; Default: `WARNING`)

Tune your preferred log level for server logs or local debugging. Does not affect the ENV var specified by `output_debug_env_varname`.


#### `DESTALINATOR_LOG_TO_CHANNEL` (Optional)

If you would like to log to a Slack channel as well as the default log destination, you can set `true` here. The channel
will then be pulled from `log_channel` in `configuration.yaml`.

#### `DESTALINATOR_EARLIEST_ARCHIVE_DATE` (Optional)

If you don't want to start archiving channels until a certain date right after introducing destalinator to your team,
you can set an ISO-8601 date here (`YYYY-mm-dd`).

#### `DESTALINATOR_FLAGGER_DISABLED` (Optional)

Disable the Flagger by setting `DESTALINATOR_FLAGGER_DISABLED` to `true`

#### `DESTALINATOR_SCHEDULE_HOUR` (Optional)

When should the destalinator run? Defaults to 4. Which time that means depends on your operating system time zone. Good luck!

#### `SENTRY_DSN` (Optional)

*Note:* No `DESTALINATOR_` prefix! The Sentry plugin uses this environment variable on its own.

If you would like to configure exception handling & tracking with [Sentry](https://sentry.io/), set up a Sentry account
and configure this environment variable with the appropriate DSN value.

If you're on Heroku, you can provision this with:

    heroku addons:create sentry:f1

## Code of Conduct

As part of the Rands Leadership Slack community, the [Rands Leadership Slack Code of Conduct](https://github.com/randsleadershipslack/documents-and-resources/blob/master/code-of-conduct.md) applies to this project.
