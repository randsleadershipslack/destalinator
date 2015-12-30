from apscheduler.schedulers.blocking import BlockingScheduler
import slackbot
import destalinator
import os

sched = BlockingScheduler()

@sched.scheduled_job("cron", minute=30)
def destalinate_daily():
    print("Destalinating")
    if not os.environ["SLACK_SLACKBOT_TOKEN"] or not os.environ["SLACK_API_TOKEN"]:
        print "ERR: Missing at least one Slack environment variable."
    else:
        sb = slackbot.Slackbot("rands-leadership", slackbot_token=os.environ["SLACK_SLACKBOT_TOKEN"])
        ds = Destalinator("rands-leadership", slackbot=sb, api_token=os.environ["SLACK_API_TOKEN"])
        ds.warn_all(30)
        print("OK: destalinated")

sched.start()
