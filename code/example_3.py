"""
example_3.py

Just a short example demonstraing a simple state machine in Python
However, this one has delays that affect it
"""

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
            yield
        print 'Task %s total: %s' % (name, total)
        print 'Task %s total elapsed time: %2.1f' % (name, et())


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    queue = Queue.Queue()

    # put some 'work' in the queue
    map(queue.put, [15, 10, 5, 2])


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
