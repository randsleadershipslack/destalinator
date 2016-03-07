# destalinator
Code for managing Cleanup of Stale Channels

# Making it work in your environment
You'll need to change configuration.yaml appropriately.  warner.py and archiver.py
should then work from the commandline.  Productionalized automated deployments
and running on a schedule are left unspecified because every production environment
is unique

## Environment Variables

These assume default values in `configuration.yaml`

### `SB_TOKEN`

1. Make sure [the Slackbot app](https://slack.com/apps/A0F81R8ET-slackbot) is installed for your Slack
2. Add a Slackbot integration, and copy the `token` parameter from the URL provided

### `API_TOKEN`

The easiest way to get an `API_TOKEN` is to [generate an OAuth test token](https://api.slack.com/docs/oauth-test-tokens).

It's not *nice*, but it's simple and avoids the whole callback-URL-oauth-request-app-creation dance.
