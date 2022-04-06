#! /usr/bin/env python

import time

from slack_sdk import WebClient

import executor


class Announcer(executor.Executor):
    def get_new_channels(self):
        """
        returns [(channel_name, creator, purpose)] created in the last 24 hours
        """

        now = int(time.time())
        dayago = now - 86400
        channels = self.slacker.get_all_channel_objects()
        new_channels = [channel for channel in channels if channel['created'] > dayago]
        new = []
        for new_channel in new_channels:
            print("new channel: {}".format(new_channel))
            purpose = self.slacker.asciify(new_channel['purpose']['value'])
            creator = new_channel['creator']
            cid = new_channel['id']
            friendly = self.slacker.asciify(creator)
            new.append((cid, friendly, purpose))
        return new

    def announce(self):
        self.logger.info("Announcing")
        new = self.get_new_channels()
        client = WebClient(token=self.config.api_token)
        for cid, creator, purpose in new:
            m = "Channel <#{}> was created by <@{}> with purpose: {}".format(cid, creator, purpose)
            if self.config.activated:
                if self.slacker.channel_exists(self.config.announce_channel):
                    client.chat_postMessage(channel=self.config.announce_channel, text=m)
                else:
                    self.logger.warning("Attempted to announce in %s, but channel does not exist.", self.config.announce_channel)
            self.logger.info("ANNOUNCE: %s", m)


if __name__ == "__main__":
    Announcer().announce()
