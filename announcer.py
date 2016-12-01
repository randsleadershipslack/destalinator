#! /usr/bin/env python

import time

import config
import executor

config = config.Config()


class Announcer(executor.Executor):

    def get_new_channels(self):
        """
        returns [(channel_name, creator, purpose)] created in the last 24 hours
        """

        now = time.time()
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
        new = self.get_new_channels()
        for cname, creator, purpose in new:
            m = "Channel #{} was created by @{} with purpose: {}".format(cname, creator, purpose)
            if self.destalinator_activated:
                if self.slacker.channel_exists(config.announce_channel):
                    self.sb.say(config.announce_channel, m)
                else:
                    self.ds.warning("Attempted to announce in {}, but channel does not exist.".format(config.announce_channel))
            print("ANNOUNCE: {}".format(m))


if __name__ == "__main__":
    announcer = Announcer()
    announcer.announce()
