"""
example_8.py

Just a short example demonstrating a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. This version uses the Twisted
framework to provide the concurrency
"""

from twisted.internet import defer
from twisted.web.client import getPage
from twisted.internet import reactor, task

import queue
from lib.elapsed_time import ET


def success_callback(results, name, url, et):
    print(f'Task {name} got URL: {url}')
    print(f'Task {name} total elapsed time: {et():.1f}')


def my_task(name, queue):
    if not queue.empty():
        while not queue.empty():
            url = queue.get()
            print(f'Task {name} getting URL: {url}')
            et = ET()
            d = getPage(url)
            d.addCallback(success_callback, name, url, et)
            yield d


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for url in [
        b"http://google.com",
        b"http://yahoo.com",
        b"http://linkedin.com",
        b"http://shutterfly.com",
        b"http://mypublisher.com",
        b"http://facebook.com"
    ]:
        work_queue.put(url)

    # run the tasks
    et = ET()

    # create cooperator
    coop = task.Cooperator()

    defer.DeferredList([
        coop.coiterate(my_task('One', work_queue)),
        coop.coiterate(my_task('Two', work_queue)),
    ]).addCallback(lambda _: reactor.stop())

    # run the event loop
    reactor.run()

    print()
    print(f'Total elapsed time: {et():.1f}')


if __name__ == '__main__':
    main()
