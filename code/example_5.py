"""
example_5.py

Just a short example demonstraing a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue
"""

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
        yield


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

    tasks = [
        task('One', queue),
        task('Two', queue)
    ]
    # run the scheduler to run the tasks
    et = ET()
    done = False
    while not done:
        for t in tasks:
            try:
                t.next()
            except StopIteration:
                tasks.remove(t)
            if len(tasks) == 0:
                done = True

    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
