"""
example_1.py

Just a short example showing synchronous running of 'tasks'
"""

import Queue

def task(name, queue):
    if queue.empty():
        print 'Task %s nothing to do' % name
    else:
        while not queue.empty():
            count = queue.get()
            total = 0
            for x in range(count):
                print 'Task %s running' % name
                total += 1
            print 'Task %s total: %s' % (name, total)


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    queue = Queue.Queue()

    # put some 'work' in the queue
    map(queue.put, [15, 10, 5, 2])

    # create some tasks
    tasks = [
        (task, 'One', queue),
        (task, 'Two', queue)
    ]

    # run the tasks
    for t, n, q in tasks:
        t(n, q)

if __name__ == '__main__':
    main()
