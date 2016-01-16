#! /usr/bin/env python

import json
import os
import sys

import executor


class Flagger(executor.Executor):

    def flag(self):
        self.ds.announce_interesting_messages()

if __name__ == "__main__":
    flagger = Flagger()
    flagger.flag()
