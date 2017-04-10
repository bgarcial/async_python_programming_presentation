"""
example_2.py

Just a short example demonstraing a simple state machine in Python
However, this one has delays that affect it
"""


import Queue


def task(name, queue):
    while not queue.empty():
        count = queue.get()
        total = 0
        for x in range(count):
            print 'Task %s running' % name
            total += 1
            yield
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
        task('One', queue),
        task('Two', queue)
    ]

    # run the tasks
    done = False
    while not done:
        for t in tasks:
            try:
                t.next()
            except StopIteration:
                tasks.remove(t)
            if len(tasks) == 0:
                done = True


if __name__ == '__main__':
    main()
