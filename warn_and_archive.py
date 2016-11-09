#! /usr/bin/env python

import warner
import archiver

if __name__ == "__main__":
    warn_and_archive_warner = warner.Warner()
    warn_and_archive_archiver = archiver.Archiver()
    warn_and_archive_warner.warn()
    warn_and_archive_archiver.archive()
