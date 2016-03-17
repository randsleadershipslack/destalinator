#! /usr/bin/env python

import re
import time

import requests


class Slacker(object):

    def __init__(self, slack_name, token):
        """
        slack name is the short name of the slack (preceding '.slack.com')
        token should be a Slack API Token.
        """
        self.slack_name = slack_name
        self.token = token
        assert self.token, "Token should not be blank"
        self.url = self.api_url()
        self.get_users()
        self.get_channels()

    def get_users(self):
        url = self.url + "users.list?token=" + self.token
        payload = requests.get(url).json()['members']
        self.users_by_id = {x['id']: x['name'] for x in payload}
        self.users_by_name = {x['name']: x['id'] for x in payload}

    def asciify(self, text):
        return ''.join([x for x in list(text) if ord(x) in range(128)])

    def get_messages_in_time_range(self, oldest, cid, latest=None):
        assert cid in self.channels_by_id, "Unknown channel ID {}".format(cid)
        cname = self.channels_by_id[cid]
        messages = []
        done = False
        while not done:
            murl = self.url + "channels.history?oldest={}&token={}&channel={}".format(oldest, self.token, cid)
            if latest:
                murl += "&latest={}".format(latest)
            else:
                murl += "&latest={}".format(time.time())
            payload = requests.get(murl).json()
            messages += payload['messages']
            if payload['has_more'] is False:
                done = True
                continue
            ts = [float(x['ts']) for x in messages]
            earliest = min(ts)
            latest = earliest
        messages.sort(key=lambda x: float(x['ts']))
        for message in messages:
            message['channel'] = cname
        return messages

    def replace_id(self, cid):
        """
        Assuming either a #channelid or @personid, replace them with #channelname or @username
        """
        stripped = cid[1:]
        first = cid[0]
        if first == "#":
            m = [x for x in self.channels if self.channels[x] == stripped]
            if m:
                return "#" + m[0]
            else:
                return cid
        elif first == "@":
            uname = self.users_by_id[stripped]
            if uname:
                return "@" + uname
        return cid

    def detokenize(self, message):
        new = []
        tokens = re.split("(<.*?>)", message)
        for token in tokens:
            if len(token) > 3 and token[0] == "<" and token[-1] == ">":
                token = self.replace_id(token[1:-1])
            new.append(token)
        message = " ".join(new)
        return message

    def api_url(self):
        return "https://{}.slack.com/api/".format(self.slack_name)

    def get_channels(self, exclude_archived=True):
        """
        return a {channel_name: channel_id} dictionary
        if exclude_archived (default: True), only shows non-archived channels
        """
        channels = self.get_all_channel_objects(exclude_archived=exclude_archived)
        self.channels_by_id = {x['id']: x['name'] for x in channels}
        self.channels_by_name = {x['name']: x['id'] for x in channels}
        self.channels = self.channels_by_name

    def get_channelid(self, channel_name):
        return self.channels_by_name[channel_name]

    def delete_message(self, cid, message_timestamp):
        url_template = self.url + "chat.delete?token={}&channel={}&ts={}"
        url = url_template.format(self.token, cid, message_timestamp)
        ret = requests.get(url).json()
        if not ret['ok']:
            print ret
        return ret['ok']

    def get_channel_info(self, channel_name):
        """
        returns JSON with channel information.  Adds 'age' in seconds to JSON
        """
        url_template = self.url + "channels.info?token={}&channel={}"
        cid = self.get_channelid(channel_name)
        now = time.time()
        url = url_template.format(self.token, cid)
        ret = requests.get(url).json()
        if ret['ok'] is not True:
            m = "Attempted to get channel info for {}, but return was {}"
            m = m.format(channel_name, ret)
            self.warning(m)
            raise RuntimeError(m)
        created = ret['channel']['created']
        age = now - created
        ret['channel']['age'] = age
        return ret['channel']

    def get_all_channel_objects(self, exclude_archived=True):
        """
        return all channels
        if exclude_archived (default: True), only shows non-archived channels
        """

        url_template = self.url + "channels.list?exclude_archived={}&token={}"
        if exclude_archived:
            exclude_archived = 1
        else:
            exclude_archived = 0
        url = url_template.format(exclude_archived, self.token)
        request = requests.get(url)
        payload = request.json()
        assert 'channels' in payload
        return payload['channels']

    def archive(self, channel_name):
        url_template = self.url + "channels.archive?token={}&channel={}"
        cid = self.get_channelid(channel_name)
        url = url_template.format(self.token, cid)
        request = requests.get(url)
        payload = request.json()
        return payload
