"""
example_4.py

Just a short example demonstraing a simple state machine in Python
However, this one has delays that affect it
"""

import gevent
from gevent import monkey
monkey.patch_all()

import time
import Queue
from lib.elapsed_time import ET


def task(name, queue):
    while not queue.empty():
        count = queue.get()
        total = 0
        et = ET()
        for x in range(count):
            print 'Task %s running' % name
            time.sleep(1)
            total += 1
        print 'Task %s total: %s' % (name, total)
        print 'Task %s total elapsed time: %2.1f' % (name, et())


def main():
    """
    This is the main entry point for the programWhen
    """
    # create the queue of 'work'
    queue = Queue.Queue()

    # put some 'work' in the queue
    map(queue.put, [15, 10, 5, 2])

    # run the tasks
    et = ET()
    tasks = [
        gevent.spawn(task, 'One', queue),
        gevent.spawn(task, 'Two', queue)
    ]
    gevent.joinall(tasks)
    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
