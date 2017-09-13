#! /usr/bin/env python

import sys

import executor


class Warner(executor.Executor):
    def warn(self, force_warn=False):
        self.logger.info("Warning")
        self.ds.warn_all(self.config.warn_threshold, force_warn)


if __name__ == "__main__":
    force_warn = False
    if len(sys.argv) == 2 and sys.argv[1] == "force":
        force_warn = True
    Warner().warn(force_warn=force_warn)
