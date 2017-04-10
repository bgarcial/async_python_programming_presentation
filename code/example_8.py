"""
example_8.py

Just a short example demonstraing a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. This version uses the Twisted
framework to provide the concurrency
"""

from twisted.internet import defer
from twisted.web.client import getPage
from twisted.internet import reactor, task

import Queue
from lib.elapsed_time import ET


def my_task(name, queue):
    def success_callback(results):
        print 'Task %s got URL: %s' % (name, url)
        print 'Task %s total elapsed time: %2.1f' % (name, et())

    if not queue.empty():
        while not queue.empty():
            url = queue.get()
            print 'Task %s getting URL: %s' % (name, url)
            et = ET()
            d = getPage(url)
            d.addCallback(success_callback)
            yield d


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    queue = Queue.Queue()

    # put some 'work' in the queue
    map(queue.put, [
        "http://google.com",
        "http://yahoo.com",
        "http://linkedin.com",
        "http://shutterfly.com",
        "http://mypublisher.com",
        "http://facebook.com"
    ])

    # run the tasks
    et = ET()

    # create cooperator
    coop = task.Cooperator()

    defer.DeferredList([
        coop.coiterate(my_task('One', queue)),
        coop.coiterate(my_task('Two', queue)),
    ]).addCallback(lambda _: reactor.stop())

    # run the event loop
    reactor.run()

    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
