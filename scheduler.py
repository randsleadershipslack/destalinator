import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from raven.base import Client as RavenClient

import warner
import archiver
import announcer
import flagger
from config import get_config


def schedule_job():
    # When testing changes, set the "TEST_SCHEDULE" envvar to run more often
    if get_config().test_schedule:
        schedule_kwargs = {"hour": "*", "minute": "*/10"}
    else:
        schedule_kwargs = {"hour": get_config().schedule_hour}

    sched = BlockingScheduler()
    sched.add_job(destalinate_job, "cron", **schedule_kwargs)
    sched.start()


def destalinate_lambda(event, context):
    destalinate_job()


def destalinate_job():
    raven_client = RavenClient()

    logging.info("Destalinating")
    if not get_config().sb_token or not get_config().api_token:
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
            if not get_config().sentry_dsn:
                raise e
    logging.info("END: destalinate_job")


def main():
    # Use RUN_ONCE to only run the destalinate job once immediately
    if get_config().run_once:
        destalinate_job()
    else:
        schedule_job()


if __name__ == "__main__":
    main()
