import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from raven.base import Client as RavenClient

import warner
import archiver
import announcer
import flagger
from config import get_config

_config = get_config()

raven_client = RavenClient()

# When testing changes, set the "TEST_SCHEDULE" envvar to run more often
if _config.test_schedule:
    schedule_kwargs = {"hour": "*", "minute": "*/10"}
else:
    schedule_kwargs = {"hour": _config.schedule_hour}

sched = BlockingScheduler()


@sched.scheduled_job("cron", **schedule_kwargs)
def destalinate_job():
    logging.info("Destalinating")
    if not _config.sb_token or not _config.api_token:
        logging.error(
            "Missing at least one required Slack environment variable.\n"
            "Make sure to set DESTALINATOR_SB_TOKEN and DESTALINATOR_API_TOKEN."
        )
    else:
        try:
            archiver.Archiver().archive()
            warner.Warner().warn()
            announcer.Announcer().announce()
            flagger.Flagger().flag()
            logging.info("OK: destalinated")
        except Exception as e:  # pylint: disable=W0703
            raven_client.captureException()
            if not _config.sentry_dsn:
                raise e
    logging.info("END: destalinate_job")


if __name__ == "__main__":
    # Use RUN_ONCE to only run the destalinate job once immediately
    if _config.run_once:
        destalinate_job()
    else:
        sched.start()
