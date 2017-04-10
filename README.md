# Asynchronous Programming with Python

This presentation is about creating asynchronous programs with the Python language, and perhaps, why you'd want to do such a thing. A synchronous program is what most of us started out writing, and can be thought of as performing one execution step at a time. Even with conditional branching, loops and function calls, we can still think about the code in terms of taking one execution step at a time, and when complete, moving on to the next. An asynchronous program behaves differently, it still takes one execution step at a time. However the difference is the system may not wait for an execution step to be complete before moving on. This means we are continuing onward through execution steps of the program, even though a previous execution step (or multiple steps) is running "elsewhere". This also implies when one of those execution steps that is running "elsewhere" completes, our program code has to handle it somehow.

Why would we want to write a program in this manner? The simple answer is it helps us handle particular kinds of programming problems. Let's look at a couple of examples. Writing batch processing programs are often created as synchronous programs: get some input, process it, create some output. One step logically follows another till we create the desired output, there's really nothing else the program has to pay attention to besides those steps, and in that order. 

Now let's take a look at a simplistic web server. It's basic unit of work is the same as we described above; get some input, process it, create the output. Written as a synchronous program this would create a working web server. It would also be an absolutely terrible web server. Why? In the case of a web server one unit of work (input, process, output) is not its only purpose. Its real purpose is to handle hundreds, perhaps thousands, of units of work at the same time, and for long periods of time. Can we make our synchronous web server better? Sure, we can optimize our execution steps to make them as fast as possible. There are very real limits to this approach that leads to a web server that can't respond fast enough, and can't handle enough current users.

What are the real limits of optimizing the above approach? The speed of the network, file IO speed, database query speed, the speed of other connected services, etc. The common feature of this list is they are all IO functions. All of these items are many orders of magnitude slower than our CPU's processing speed. In a synchronous program if the execution step starts a database query (for example), the CPU is essentially idle for long periods of time before the query returns with some data, and it can continue with the next execution step. For batch oriented programs this isn't a priority, the processing of the results of that IO is the goal, and often takes far longer than the IO. Any optimization efforts would be focused on the processing work, not the IO.

File IO, network IO, database IO are all pretty fast, but still way slower than the CPU. Asynchronous programming techniques allow our programs to take advantage of the relatively slow IO processes, and free the CPU to do other work.

A lot of books and documentation about writing asynchronous programs tries to explain how they work, and how to write them, by talking about blocking and non-blocking code. This has never really helped me at all to understand asynchronous programming. It's like having a reference manual without any practical context about how put that technical detail together in a meaningful way. I'm going to draw some pictures during the presentation of some real world examples of how humans act in an asynchronous way, and how that might help us relate our own behavior to programming.

[pictures here]

## Let's Get Started - Synchronous Program

This first example shows a somewhat contrived way of having a task pull 'work' off a queue and do that work. In this case the work is jsut getting a number, and the task counts up to that number. It also prints that it's running at every count step, and prints the total at the end. The contrived part is program provides a naive basis for multiple tasks to process the work on the queue.

```python
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
```

When we run this task we get a listing showing that task one does all the work. The loop within it consumes all the work on the queue, and performs it. When that loop exits, task two gets a chance to run, but finds the queue empty, so it prints a statement to that affect and exits. There is nothing in the code that would allow task one and task two to run together.

## Cooperative Concurreny - Simple State Machine

This version of the program adds the ability of the two tasks to run together through the user of generators. The addition of the yield statement in the task loop means the function exits at that point, but maintains its context so it can be restarted later. The 'run the tasks' loop later in the program takes advantage of this when it calls t.next(). This statement restarts the task at the point where it yielded. 

This is a form of cooperative concurrency. The program is yielding control of its current context so something else can run. In this case it allows our primative 'run the tasks' scheduler to run two instances of the task function, each one consuming work from the same queue. This is sort of clever, but a lot of work to get the same results as the first program. 

```python
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
```

When this program is run the output shows that both task one and two are running, consuming work from the queue and processing it. This what's intended, both tasks are processing work, and each ends up processing two items from the queue. But again, quite a bit of work to achieve the results.

## Cooperative Concurreny - With Blocking Calls

This version of the program is exactly the same as the last, except for the addition of a time.sleep(1) call in the body of our task loop. This adds a one second delay to every iteration of the task loop. The delay was added to simulate the affect of a slow IO process occurring in our task.

```python
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
```

When this program is run the output shows that both task one and two are running, consuming work from the queue and processing it. With the addition of the mock IO delay, we're seeing that our cooperative concurrency hasn't gotten us anything, the delay stops the processing of the entire program, and the CPU just waits for the IO delay to be over. Notice the time it takes the run the entire program, this is the cummulative time of the all the delays. This again shows running things this way is not a big win.

## Cooperative Concurrency - With Non-Blocking Calls (Gevent)

This version of the program has been modified quite a bit. It makes use of the Gevent asynchronous programming module right at the top of the program. The module is imported, along with a module called monkey. Then a method of the monkey module is called, patch_all(). What in the world is that doing? The simple explanation is that it sets the program up so any other module that's imported that has blocking (synchronous) calls in it is 'patched' to make them asynchronous. Like most simple explanations, this isn't very helpful. What it means in relation to our example program is the time.sleep(1) (our mock IO delay) no longer 'blocks' the program. Instead it yields control cooperatively back to the system. Notice the 'yield' statement from example_3.py is no longer present. So, if the time.sleep(1) function has been patched by Gevent to yield control, where is the control going? One of the effects of using gevent is that it starts an event loop thread in the program. For our purposes this is like the 'run the tasks' loop from example_3.py. When the time.sleep(1) delay ends, it returns control to the next executable statement after the time.sleep(1) statement. The advantage of this behavior is the CPU is no longer blocked by the delay, but is free to execute other code.

Our 'run the tasks' loop no longer exists, instead our task array contains two calls to gevent.spawn(...). These two calls start two Gevent threads (called greenlets), which are lightweight microthreads that context switch cooperatively, rather than as a result of the system enviroment like regular threads.

```python
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
    This is the main entry point for the program
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
```

When this program runs, notice that both task one and two start at the same time, then wait at the mock IO call. This is an indication the time.sleep(1) call is no longer blocking, and other work can be done. In this case start both greenlet threads running. At the end of the program notice the total elapsed time, it's essentially half the time it took for example_3.py to run. Now we're starting to see the advantages of an asynchronous program, being able to run two, or more, things concurrently by running IO processes in a non-blocking manner.

## Cooperative Concurrency - Doing Real Work, With Blocking Calls



```python
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
```

## Cooperative Concurrency - Doing Real Work, With Non-Blocking Calls (Gevent)

```python
"""
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
    if queue.empty():
        print 'Task %s nothing to do' % name
    else:
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
        gevent.spawn(task, 'Two', queue)
    ]
    gevent.joinall(tasks)
    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
```

## Cooperative Concurrency - Doing Real Work, With Non-Blocking Calls (Twisted)

```python
"""
Just a short example demonstraing a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. This version uses the Twisted
framework to provide the concurrency
"""

from twisted.internet import defer
from twisted.web.client import getPage
from twisted.internet import reactor

import Queue
from lib.elapsed_time import ET


@defer.inlineCallbacks
def task(name, queue):
    if queue.empty():
        print 'Task %s nothing to do' % name
    else:
        while not queue.empty():
            url = queue.get()
            print 'Task %s getting URL: %s' % (name, url)
            et = ET()
            yield getPage(url)
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
    defer.DeferredList([
        task('One', queue),
        task('Two', queue)
    ]).addCallback(reactor.stop)

    # run the event loop
    reactor.run()

    print
    print 'Total elapsed time: %2.1f' % et()


if __name__ == '__main__':
    main()
```
