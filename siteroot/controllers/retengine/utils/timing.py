#!/usr/bin/env python

import time

class TimerBlock:
    """
        Class for timing groups of statements.

        Used to time blocks of statements contained within a 'with' block
        e.g. with TimerBlock() as t: <statements>

        Upon exit from the block, the time taken is stored in t.interval
    """
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
