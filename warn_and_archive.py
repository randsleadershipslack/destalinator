#! /usr/bin/env python

from warner import Warner
from archiver import Archiver

if __name__ == "__main__":
    warner = Warner()
    archiver = Archiver()
    warner.warn()
    archiver.archive()
