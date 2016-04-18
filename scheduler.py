from apscheduler.schedulers.blocking import BlockingScheduler
from warner import Warner
from archiver import Archiver
from announcer import Announcer
from flagger import Flagger
import os

sched = BlockingScheduler()


@sched.scheduled_job("cron", hour=4)
def destalinate_job():
    print("Destalinating")
    if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ:
        print "ERR: Missing at least one Slack environment variable."
        # print "1 {}".format(os.environ["SLACK_SLACKBOT_TOKEN"])
        # print "2 {}".format(os.environ["SLACK_API_TOKEN"])
    else:
        warner = Warner()
        archiver = Archiver()
        announcer = Announcer()
        flagger = Flagger()
        print("Warning")
        warner.warn()
        print("Archiving")
        archiver.archive()
        print("Announcing")
        announcer.announce()
        print("Flagging")
        flagger.flag()
        print("OK: destalinated")
    print("END: destalinate_job")

sched.start()
