#! /usr/bin/env python

import json
import time

import requests

from config import WithConfig
from utils.with_logger import WithLogger


class Slacker(WithLogger, WithConfig):

    def __init__(self, slack_name, token, init=True):
        """
        slack name is the short name of the slack (preceding '.slack.com')
        token should be a Slack API Token.
        """
        self.slack_name = slack_name
        self.token = token
        assert self.token, "Token should not be blank"
        self.url = self.api_url()

        if init:
            self.get_users()
            self.get_channels()

    def get_users(self):
        users = self.paginated_lister("users.list", limit=800)
        self.users_by_id = {x['id']: x['name'] for x in users}
        self.restricted_users = [x['id'] for x in users if x.get('is_restricted')]
        self.ultra_restricted_users = [x['id'] for x in users if x.get('is_ultra_restricted')]
        self.all_restricted_users = set(self.restricted_users + self.ultra_restricted_users)
        self.logger.debug("All restricted user names: %s", ', '.join([self.users_by_id[x] for x in self.all_restricted_users]))
        return users

    def asciify(self, text):
        return ''.join([x for x in list(text) if ord(x) in range(128)])

    def api_url(self):
        return "https://{}.slack.com/api/".format(self.slack_name)

    def get_channels(self, exclude_archived=True):
        """
        return a {channel_name: channel_id} dictionary
        if exclude_archived (default: True), only shows non-archived channels
        """
        channels = self.get_all_channel_objects(exclude_archived=exclude_archived)
        self.channels_by_name = {x['name']: x['id'] for x in channels}
        self.channels = self.channels_by_name

    def channel_exists(self, channel_name):
        try:
            # strip leading "#" if it exists, as Slack returns all channels without them
            if channel_name[0] == "#":
                channel = channel_name[1:]
            else:
                channel = channel_name
            return self.channels_by_name[channel]
        except KeyError:  # channel not found
            return None

    def get_all_channel_objects(self, types=[], exclude_archived=True):
        if len(types) == 0:
            # Always default to public channels only
            types = ['public_channel']
        elif type(types) is list:
            if any([conversation_type for conversation_type in types
                    if conversation_type not in self.CONVERSATIONS_LIST_TYPES]):
                raise ValueError('Invalid conversation type')
        types_param = ','.join(types)

        if exclude_archived:
            exclude_archived = 1
        else:
            exclude_archived = 0
        channels = self.paginated_lister(
            "conversations.list?exclude_archived={}&types={types}".format(exclude_archived, types=types_param), limit=1000)

        channels.sort(key=lambda x: x['id'])
        return channels

    def paginated_lister(self, api_call, limit=200, callback=None):
        """
        if callback is defined, we'll call that method on each element we retrieve
        and not keep track of the total set of elements we retrieve.  That way, we can
        get an arbitrary large set of elements without running out of memory
        In that case, we'll only return the latest set of results
        """
        element_name = None
        done = False
        cursor = None
        results = []
        separator = self.use_separator(api_call)
        api_call = api_call + separator + "limit={}".format(limit)
        while not done:
            interim_api_call = api_call
            if cursor:
                interim_api_call += "&cursor={}".format(cursor)
            interim_results = self.api_call(interim_api_call, header_for_token=True)
            if not element_name:
                element_name = Slacker.discover_element_name(interim_results)
            if callback:
                for element in interim_results[element_name]:
                    callback(element)
                results = interim_results[element_name]
            else:
                results += interim_results[element_name]
            if len(interim_results[element_name]) == 2:
                print(json.dumps(interim_results, indent=4))
            cursor = interim_results.get(
                "response_metadata", {}).get(
                "next_cursor", "")
            if not cursor:
                done = True
        return results

    def use_separator(self, url):
        """
        if url already has '?', use &; otherwise, use '?'
        """
        separator = "?"
        if '?' in url:
            separator = "&"
        return separator

    def api_call(
            self,
            api_endpoint,
            method=requests.get,
            json=None,
            header_for_token=False):
        url = "https://{}.slack.com/api/{}".format(self.slack_name, api_endpoint)
        headers = {}
        if header_for_token:
            headers['Authorization'] = "Bearer {}".format(self.token)
        else:
            separator = self.use_separator(url)
            url += "{}token={}".format(separator, self.token)
        if json:
            headers['Content-Type'] = "application/json"
        done = False
        while not done:
            response = self.retry_api_call(
                method, url, json=json, headers=headers)
            if response.status_code == 200:
                done = True
            if response.status_code == 429:
                if 'Retry-After' in response:
                    retry_after = int(response['Retry-After']) + 1
                else:
                    retry_after = 5
                time.sleep(retry_after)
            if response.status_code == 403:
                raise Exception('API returning status code 403')
        payload = response.json()
        return payload

    def retry_api_call(
            self,
            method,
            url,
            json,
            headers,
            delay=1,
            increment=2,
            max_delay=120):
        while True:
            try:
                payload = method(url, json=json, headers=headers)
                return payload
            except Exception as es:
                print(
                    "Failed to retrieve {} : {}.  Sleeping {} seconds".format(
                        url, es, delay))
                time.sleep(delay)
                if delay < max_delay:
                    delay += increment
                    # print "Incrementing delay to {}".format(delay)

    @staticmethod
    def discover_element_name(response):
        """
        Figure out which part of the response from a paginated lister is the list of elements
        the logic is pretty simple -- in the dict response, find the one key that has a list value
        or raise an error if more than one exists
        """
        lists = [k for k in response if isinstance(response[k], list)]
        if len(lists) == 0:
            raise RuntimeError("No list of objects found")
        if len(lists) > 1:
            raise RuntimeError(
                "Multiple response objects corresponding to lists found: {}".format(lists))
        return lists[0]
