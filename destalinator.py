#! /usr/bin/env python

import time

import requests


api_token = "REDACTED"
sname = "rands-leadership"


def get_channels(slack_name, api_token, exclude_archived=True):
    """
    Given a slack name and an api token, return a {channel_name: channel_id} dictionary
    if exclude_arhived (default: True), only shows non-archived channels
    """

    url_template = "https://{}.slack.com/api/channels.list?exclude_archived={}&token={}"
    if exclude_archived:
        exclude_archived = 1
    else:
        exclude_archived = 0
    url = url_template.format(slack_name, exclude_archived, api_token)
    request = requests.get(url)
    payload = request.json()
    assert 'channels' in payload
    channels = {x['name']: x['id'] for x in payload['channels']}
    return channels

channels = get_channels("rands-leadership", api_token)

def get_channelid(channel_name):
    """
    Given a channel name, returns the ID of the channel
    """
    return channels[channel_name]

def get_messages(slack_name, channel_name, api_token, days):
    """
    get 'all' messages for the given channel name in the slack
    name from the last DAYS days
    By default, Slack only returns 100 messages, so if more than 100 messages
    were sent, we'll only bget a subset of messages.  Since this code is used for
    stale channel handling, that's considered acceptable.
    """

    url_template = "https://{}.slack.com/api/channels.history?oldest={}&token={}&channel={}"
    cid = get_channelid(channel_name)
    ago = time.time() - (days * 86400)
    url = url_template.format(slack_name, ago, api_token, cid)
    payload = requests.get(url).json()
    assert 'messages' in payload
    return [x for x in payload['messages'] if x.get("subtype") is None]

def stale(slack_name, channel_name, api_token, magic_token, days):
    """
    returns True/False whether the channel is stale.  Definition of stale is
    no messages in the last DAYS days which do not contain the magic_token
    """
    messages = get_messages(slack_name, channel_name, api_token, days)
    texts = [x['text'] for x in messages]
    texts_from_humans = [x for x in texts if x.find(magic_token) == -1]
    if texts_from_humans:
        return False
    else:
        return True

def get_stale_channels(days):
    ret = []
    for channel in sorted(channels.keys()):
        if stale(sname, channel, api_token, "automated", days):
            ret.append(channel)
    return ret

stale30 = get_stale_channels(30)
print "{} channels are stale for 30 days: {}".format(len(stale30), ", ".join(stale30))
stale60 = get_stale_channels(60)
print "{} channels are stale for 60 days: {}".format(len(stale60), ", ".join(stale60))
