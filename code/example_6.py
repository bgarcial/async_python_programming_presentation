"""
example_6.py

Just a short example demonstraing a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. It's also using Gevent to get the
URL's in an asynchronous manner.
"""

import gevent
from gevent import monkey
monkey.patch_all()

import Queue
import requests
from lib.elapsed_time import ET


def task(name, queue):
    while not queue.empty():
        url = queue.get()
        print 'Task %s getting URL: %s' % (name, url)
        et = ET()
        requests.get(url)
        print 'Task %s got URL: %s' % (name, url)
        print 'Task %s total elapsed time: %2.1f' % (name, et())


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
    tasks = [
        gevent.spawn(task, 'One', queue),
        gevent.spawn(task, 'Two', queue),
        gevent.spawn(task, 'Three', queue)

    ]
    gevent.joinall(tasks)
    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
