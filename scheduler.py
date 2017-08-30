import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from raven.base import Client as RavenClient

import warner
import archiver
import announcer
import flagger


raven_client = RavenClient()

# When testing changes, set the "TEST_SCHEDULE" envvar to run more often
if os.getenv("DESTALINATOR_TEST_SCHEDULE"):
    schedule_kwargs = {"hour": "*", "minute": "*/10"}
else:
    schedule_kwargs = {"hour": 4}

sched = BlockingScheduler()


@sched.scheduled_job("cron", **schedule_kwargs)
def destalinate_job():
    logging.info("Destalinating")
    if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ:
        logging.error("Missing at least one Slack environment variable.")
    else:
        try:
            warner.Warner().warn()
            archiver.Archiver().archive()
            announcer.Announcer().announce()
            flagger.Flagger().flag()
            logging.info("OK: destalinated")
        except Exception as e:  # pylint: disable=W0703
            raven_client.captureException()
            if not os.getenv('DESTALINATOR_SENTRY_DSN'):
                raise e
    logging.info("END: destalinate_job")


if __name__ == "__main__":
    sched.start()
