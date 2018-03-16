#! /usr/bin/env python

import time

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
            purpose = self.slacker.asciify(new_channel['purpose']['value'])
            creator = new_channel['creator']
            friendly = self.slacker.asciify(self.slacker.users_by_id[creator])
            name = self.slacker.asciify(new_channel['name'])
            new.append((name, friendly, purpose))
        return new

    def announce(self):
        self.logger.info("Announcing")
        new = self.get_new_channels()
        for cname, creator, purpose in new:
            m = "Channel #{} was created by @{} with purpose: {}".format(cname, creator, purpose)
            if self.config.activated or self.config.announcer_activated:
                if self.slacker.channel_exists(self.config.announce_channel):
                    self.slackbot.say(self.config.announce_channel, m)
                else:
                    self.logger.warning("Attempted to announce in %s, but channel does not exist.", self.config.announce_channel)
            self.logger.info("ANNOUNCE: %s", m)


if __name__ == "__main__":
    Announcer().announce()
