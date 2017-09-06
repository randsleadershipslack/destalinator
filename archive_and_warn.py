#! /usr/bin/env python

from warner import Warner
from archiver import Archiver

if __name__ == "__main__":
    Archiver().archive()
    Warner().warn()
