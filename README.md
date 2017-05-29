# Asynchronous Programming with Python

This article is about using Python to write asynchronous programs, and perhaps, why you'd want to do such a thing. A synchronous program is what most of us started out writing, and can be thought of as performing one execution step at a time. Even with conditional branching, loops and function calls, we can still think about the code in terms of taking one execution step at a time, and when complete, moving on to the next. An asynchronous program behaves differently, it still takes one execution step at a time. However the difference is the system may not wait for an execution step to be complete before moving on. This means we are continuing onward through execution steps of the program, even though a previous execution step (or multiple steps) is running "elsewhere". This also implies when one of those execution steps that is running "elsewhere" completes, our program code somehow has to handle it.

Why would we want to write a program in this manner? The simple answer is it helps us handle particular kinds of programming problems. Let's look at a couple of examples.

* Writing batch processing programs are often created as synchronous programs: get some input, process it, create some output. One step logically follows another till we create the desired output, there's really nothing else the program has to pay attention to besides those steps, and in that order. 

* Command line programs are often small, quick processes to "transform" something into something else. This can be expressed as a series of program steps executed serially and done.

Now let's take a look at a simplistic web server. It's basic unit of work is the same as we described above for batch processing; get some input, process it, create the output. Written as a synchronous program this would create a working web server. It would also be an absolutely terrible web server. Why? In the case of a web server one unit of work (input, process, output) is not its only purpose. Its real purpose is to handle hundreds, perhaps thousands, of units of work at the same time, and for long periods of time. Can we make our synchronous web server better? Sure, we can optimize our execution steps to make them as fast as possible. Unfortunately there are very real limits to this approach that leads to a web server that can't respond fast enough, and can't handle enough current users.

What are the real limits of optimizing the above approach? The speed of the network, file IO speed, database query speed, the speed of other connected services, etc. The common feature of this list is they are all IO functions. All of these items are many orders of magnitude slower than our CPU's processing speed. In a synchronous program if an execution step starts a database query (for example), the CPU is essentially idle for a long time before the query returns with some data and it can continue with the next execution step. For batch oriented programs this isn't a priority, the processing of the results of that IO is the goal, and often takes far longer than the IO. Any optimization efforts would be focused on the processing work, not the IO.

File, network and database IO are all pretty fast, but still way slower than the CPU. Asynchronous programming techniques allow our programs to take advantage of the relatively slow IO processes, and free the CPU to do other work.

When I started trying to understand asynchrnous programming, people I asked and documentation I read talked a lot about the importance of writing non-blocking code. Yeah, this never helped me either. That information was like having a reference manual without any practical context about how use that technical detail in a meaningful way.

## The Real World is Asynchronous

Writing asynchronous programs is different, and kind of hard to get your head around. That's interesting to me because the world we live in, and how we interact with it, is decidedly asynchronous. Here's an example a lot of you can relate to, being a parent trying to perform several things at once; balance the checkbook, do some laundry and keep an eye on the kids. We do this without even thinking about it, but let's break it down somewhat. Balancing the checkbook is a task we're trying to get done, and we could think of it as a synchronous tasks; one step follows another till it's done. However, we can break away from it to do laundry, moving clothes from the washer to the dryer and starting another load in the washer. However, these tasks are asynchronous. While we're actually working with the washer and dryer we're performing a synchronous task, but the bulk of the task happens after we start the washer and dryer and walk away and get back to the checkbook task. Now the task is asynchronous, the washer and dryer will run independently till the buzzer goes off, notifying us that one or the other needs attention. 

Watching the kids is another asynchronous task. Once they are set up and playing, they do so independently (sort of) until they need attention; someone's hungry, someone gets hurt, someone yells in alarm, and as parents we react to it. The kids are a long running task with high priority, superceding any other task we might be doing, like the checkbook or laundry.

Think about trying to do these tasks in a synchronous manner. If we're a good parent in this scenario we just watch the kids, waiting for something to happen that needs our attention. Nothing else, like the checkbook or laundry, would get done in this scenario. We could re-prioritize the tasks any way we want, but only one of them would happen at a time in a synchronous manner. 

As people this is not how we work, we're naturally always juggling multiple things at once, often without thinking about it. As programmers the trick is how to translate this kind of behavior into code that does kind of the same thing.

### By The Way

All the examples in this article have been tested with Python 3.6.1, and the requirements.txt file indicates what modules you'll need to run all the examples. I would strongly suggest setting up a Python virtual environment to run the code so as not to interfere with your system Python.

## Let's Get Started - Synchronous Program

This first example shows a somewhat contrived way of having a task pull 'work' off a queue and do that work. In this case the work is just getting a number, and the task counts up to that number. It also prints that it's running at every count step, and prints the total at the end. The contrived part is this program provides a naive basis for multiple tasks to process the work on the queue.

### example 1

```python
"""
example_1.py

Just a short example showing synchronous running of 'tasks'
"""

import queue

def task(name, work_queue):
    if work_queue.empty():
        print(f'Task {name} nothing to do')
    else:
        while not work_queue.empty():
            count = work_queue.get()
            total = 0
            for x in range(count):
                print(f'Task {name} running')
                total += 1
            print(f'Task {name} total: {total}')


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for work in [15, 10, 5, 2]:
        work_queue.put(work)

    # create some tasks
    tasks = [
        (task, 'One', work_queue),
        (task, 'Two', work_queue)
    ]

    # run the tasks
    for t, n, q in tasks:
        t(n, q)

if __name__ == '__main__':
    main()
```

The 'task' in this program is just a function that accepts a string and a queue. When executed it looks to see if there is anything in the queue to process, and if so it pulls values off the queue, starts a for loop to count up to that value, and prints the total at the end. It continues this till there is nothing left in the queue, and exits.

When we run this task we get a listing showing that task one does all the work. The loop within it consumes all the work on the queue, and performs it. When that loop exits, task two gets a chance to run, but finds the queue empty, so it prints a statement to that affect and exits. There is nothing in the code that allows task one and task two to play nice together and switch between them.

## Cooperative Concurreny - Simple State Machine

The next version of the program (example_2.py) adds the ability of the two tasks to play nice together through the use of generators. The addition of the yield statement in the task loop means the function exits at that point, but maintains its context so it can be restarted later. The 'run the tasks' loop later in the program takes advantage of this when it calls t.next(). This statement restarts the task at the point where it previously yielded. 

This is a form of cooperative concurrency. The program is yielding control of its current context so something else can run. In this case it allows our primative 'run the tasks' scheduler to run two instances of the task function, each one consuming work from the same queue. This is sort of clever, but a lot of work to get the same results as the first program. 

### Example 2

```python
"""
example_2.py

Just a short example demonstrating a simple state machine in Python
"""

import queue

def task(name, queue):
    while not queue.empty():
        count = queue.get()
        total = 0
        for x in range(count):
            print(f'Task {name} running')
            total += 1
            yield
        print(f'Task {name} total: {total}')

def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for work in [15, 10, 5, 2]:
        work_queue.put(work)

    # create some tasks
    tasks = [
        task('One', work_queue),
        task('Two', work_queue)
    ]

    # run the tasks
    done = False
    while not done:
        for t in tasks:
            try:
                next(t)
            except StopIteration:
                tasks.remove(t)
            if len(tasks) == 0:
                done = True


if __name__ == '__main__':
    main()
```

When this program is run the output shows that both task one and two are running, consuming work from the queue and processing it. This what's intended, both tasks are processing work, and each ends up processing two items from the queue. But again, quite a bit of work to achieve the results.

The trick here is using the yield statement, which turns the task function into a generator, to perform a 'context switch'. The program uses this context switch in order to run two instance of the task.

## Cooperative Concurreny - With Blocking Calls

The next version of the program (example_3.py) is exactly the same as the last, except for the addition of a time.sleep(1) call in the body of our task loop. This adds a one second delay to every iteration of the task loop. The delay was added to simulate the affect of a slow IO process occurring in our task.

### Example 3

```python
"""
example_3.py

Just a short example demonstraing a simple state machine in Python
However, this one has delays that affect it
"""

import time
import queue
from lib.elapsed_time import ET


def task(name, queue):
    while not queue.empty():
        count = queue.get()
        total = 0
        et = ET()
        for x in range(count):
            print(f'Task {name} running')
            time.sleep(1)
            total += 1
            yield
        print(f'Task {name} total: {total}')
        print(f'Task {name} total elapsed time: {et():.1f}')


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for work in [15, 10, 5, 2]:
        work_queue.put(work)


    tasks = [
        task('One', work_queue),
        task('Two', work_queue)
    ]
    # run the scheduler to run the tasks
    et = ET()
    done = False
    while not done:
        for t in tasks:
            try:
                next(t)
            except StopIteration:
                tasks.remove(t)
            if len(tasks) == 0:
                done = True

    print()
    print('Total elapsed time: {}'.format(et()))


if __name__ == '__main__':
    main()

```

When this program is run the output shows that both task one and two are running, consuming work from the queue and processing it as before. With the addition of the mock IO delay, we're seeing that our cooperative concurrency hasn't gotten us anything, the delay stops the processing of the entire program, and the CPU just waits for the IO delay to be over. This is exactly what's meant by "blocking code" in asynchronous documentation. Notice the time it takes the run the entire program, this is the cummulative time of the all the delays. This again shows running things this way is not a win.

## Cooperative Concurrency - With Non-Blocking Calls (Gevent)

The next version of the program (example_4.py) has been modified quite a bit. It makes use of the Gevent asynchronous programming module right at the top of the program. The module is imported, along with a module called monkey. Then a method of the monkey module is called, patch_all(). What in the world is that doing? The simple explanation is it sets the program up so any other module imported having blocking (synchronous) code in it is 'patched' to make it asynchronous. Like most simple explanations, this isn't very helpful. What it means in relation to our example program is the time.sleep(1) (our mock IO delay) no longer 'blocks' the program. Instead it yields control cooperatively back to the system. Notice the 'yield' statement from example_3.py is no longer present. So, if the time.sleep(1) function has been patched by Gevent to yield control, where is the control going? One of the effects of using gevent is that it starts an event loop thread in the program. For our purposes this is like the 'run the tasks' loop from example_3.py. When the time.sleep(1) delay ends, it returns control to the next executable statement after the time.sleep(1) statement. The advantage of this behavior is the CPU is no longer blocked by the delay, but is free to execute other code.

Our 'run the tasks' loop no longer exists, instead our task array contains two calls to gevent.spawn(...). These two calls start two Gevent threads (called greenlets), which are lightweight microthreads that context switch cooperatively, rather than as a result of the system switching contexts like regular threads. Notice the gevent.joinall(tasks) right after our tasks are spawned. This statement causes are program to wait till task one and task two are both finished. Without this our program would have continued on through the print statements, but with essentially nothing to do.

### Example 4

```python
"""
example_4.py

Just a short example demonstrating a simple state machine in Python
However, this one has delays that affect it
"""

import gevent
from gevent import monkey
monkey.patch_all()

import time
import queue
from lib.elapsed_time import ET


def task(name, work_queue):
    while not work_queue.empty():
        count = work_queue.get()
        total = 0
        et = ET()
        for x in range(count):
            print(f'Task {name} running')
            time.sleep(1)
            total += 1
        print(f'Task {name} total: {total}')
        print(f'Task {name} total elapsed time: {et():.1f}')


def main():
    """
    This is the main entry point for the programWhen
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for work in [15, 10, 5, 2]:
        work_queue.put(work)

    # run the tasks
    et = ET()
    tasks = [
        gevent.spawn(task, 'One', work_queue),
        gevent.spawn(task, 'Two', work_queue)
    ]
    gevent.joinall(tasks)
    print()
    print(f'Total elapsed time: {et():.1f}')


if __name__ == '__main__':
    main()

```

When this program runs, notice both task one and two start at the same time, then wait at the mock IO call. This is an indication the time.sleep(1) call is no longer blocking, and other work is being done. At the end of the program notice the total elapsed time, it's essentially half the time it took for example_3.py to run. Now we're starting to see the advantages of an asynchronous program. Being able to run two, or more, things concurrently by running IO processes in a non-blocking manner. By using Gevent greenlets and controlling the context switches, we're able to multiplex between tasks without to much trouble.

## Cooperative Concurrency - Doing Real Work, With Blocking Calls

The next version of the program (example_5.py) is kind of a step forward and step back. The program now is doing some actual work with real IO, making HTTP requests to a list of URLs and getting the page contents, but it's doing so in a blocking (synchronous) manner. We've modified the program to import the wonderful requests module to make the actual HTTP requests, and added a list of URLs to the queue rather than numbers. Inside the task, rather than increment a counter, we're using the requests module to get the contents of a URL gotten from the queue, and printing how long it took to do so.

I've also included a simple Elapsed Time class to handle the start time/elapsed time features used in the reporting.

### Example 5

```python
"""
example_5.py

Just a short example demonstrating a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue
"""

import queue
import requests
from lib.elapsed_time import ET


def task(name, work_queue):
    while not work_queue.empty():
        url = work_queue.get()
        print(f'Task {name} getting URL: {url}')
        et = ET()
        requests.get(url)
        print(f'Task {name} got URL: {url}')
        print(f'Task {name} total elapsed time: {et():.1f}')
        yield


def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for url in [
        "http://google.com",
        "http://yahoo.com",
        "http://linkedin.com",
        "http://shutterfly.com",
        "http://mypublisher.com",
        "http://facebook.com"
    ]:
        work_queue.put(url)

    tasks = [
        task('One', work_queue),
        task('Two', work_queue)
    ]
    # run the scheduler to run the tasks
    et = ET()
    done = False
    while not done:
        for t in tasks:
            try:
                next(t)
            except StopIteration:
                tasks.remove(t)
            if len(tasks) == 0:
                done = True

    print()
    print(f'Total elapsed time: {et():.1f}')


if __name__ == '__main__':
    main()

```

As in an earlier version of the program, we're using a yield to turn our task function into a generator, and perform a context switch in order to let the other task instance run. Each task gets a URL from the work queue, gets the contents of the page pointed to by the URL and reports how long it took to get that content. As before, the yield allows both our tasks to run, but because this program is running synchrnously, each requests.get() call blocks the CPU till the page is retrieved. Notice the total time to run the entire program at the end, this will be meaningful for the next example.

## Cooperative Concurrency - Doing Real Work, With Non-Blocking Calls (Gevent)

This version of the program (example_6.py) modifies the previous version to use the Gevent module again. Remember the Gevent monkey.patch_all() call modifies any following modules so synchronous code becomes asynchronous, this includes requests. Now the tasks have been modified to remove the yield call because the requests.get(url) call is no longer blocking, but performs a context switch back to the Gevent event loop. In the 'run the task' section we use Gevent to spawn two instance of the task generator, then use joinall() to wait for them to complete. 

### Example 6

```python
"""
example_6.py

Just a short example demonstrating a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. It's also using Gevent to get the
URL's in an asynchronous manner.
"""

import gevent
from gevent import monkey
monkey.patch_all()

import queue
import requests
from lib.elapsed_time import ET


def task(name, work_queue):
    while not work_queue.empty():
        url = work_queue.get()
        print(f'Task {name} getting URL: {url}')
        et = ET()
        requests.get(url)
        print(f'Task {name} got URL: {url}')
        print(f'Task {name} total elapsed time: {et():.1f}')

def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for url in [
        "http://google.com",
        "http://yahoo.com",
        "http://linkedin.com",
        "http://shutterfly.com",
        "http://mypublisher.com",
        "http://facebook.com"
    ]:
        work_queue.put(url)

    # run the tasks
    et = ET()
    tasks = [
        gevent.spawn(task, 'One', work_queue),
        gevent.spawn(task, 'Two', work_queue)
    ]
    gevent.joinall(tasks)
    print()
    print(f'Total elapsed time: {et():.1f}')

if __name__ == '__main__':
    main()

```

At the end of this program run, take a look at the total time for the program to run, and the individual times to get the contens of the URL's. You'll see the total time is less than the cummulative time of all the requests.get() calls. This is because those calls are running asynchronously, so we're effectively taking better advantage of the CPU by allowing it to download multiple things at once. 

## Cooperative Concurrency - Doing Real Work, With Non-Blocking Calls (Twisted)

This version of the program (example_7.py) uses the Twisted module to do essentially the same thing as the Gevent module, download the URL contents in a non-blocking manner. Twisted is a very powerful system, and takes a fundementally different approach to create asynchronous programs. Where Gevent modifies modules to make their synchronous code asynchronous, Twisted provides it's own functions and methods to reach the same ends. Where example_6.py used the patched requests.get(url) call to get the contents of the URLs, here we use the Twisted function getPage(url).

In this version the '@defer.inlineCallbacks' function decorator works together with the 'yield getPage(url)' to perform a context switch into the Twisted event loop. In Gevent the event loop was implied, but in Twisted it's explicitely provided by the 'reactor.run()' statement line near the bottom of the program. 

### Example 7

```python
"""
example_7.py

Just a short example demonstrating a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a work_queue. This version uses the Twisted
framework to provide the concurrency
"""

from twisted.internet import defer
from twisted.web.client import getPage
from twisted.internet import reactor, task

import queue
from lib.elapsed_time import ET


@defer.inlineCallbacks
def my_task(name, work_queue):
    try:
        while not work_queue.empty():
            url = work_queue.get()
            print(f'Task {name} getting URL: {url}')
            et = ET()
            yield getPage(url)
            print(f'Task {name} got URL: {url}')
            print(f'Task {name} total elapsed time: {et():.1f}')
    except Exception as e:
        print(str(e))


def main():
    """
    This is the main entry point for the program
    """
    # create the work_queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the work_queue
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
    defer.DeferredList([
        task.deferLater(reactor, 0, my_task, 'One', work_queue),
        task.deferLater(reactor, 0, my_task, 'Two', work_queue)
    ]).addCallback(lambda _: reactor.stop())

    # run the event loop
    reactor.run()

    print()
    print(f'Total elapsed time: {et():.1f}')


if __name__ == '__main__':
    main()

```

Notice the end result is the same as the Gevent version, the total program run time is less than the cummulative time for each URL to be retrieved.

## Cooperative Concurrency - Doing Real Work, With Non-Blocking Calls (Twisted - traditional)

This version of the program (example_8.py) also uses the Twisted library, but shows a more traditional approach to using Twisted. By this I mean rather than using the @defer.inlineCallbacks / yield style of coding, this version uses explicit callbacks. A 'callback' is a function that is passed to the system and can be called later in reaction to an event. In the example below the 'success_callback()' function is provided to Twisted to be called when the getPage(url) call completes. 

Notice in the program the '@defer.inlineCallbacks' decorator is no longer present on the my_task() function. In addtion, the function is yielding a variable called 'd', shortand for a deferred, which is what is returned by the getPage(url) function call. A deferred is Twisted way of handling asynchronous programming, and is what the callback is attached to. When this deferred 'fires' (when the getPage(url) completes), the callback function will be called with the variables defined at the time the callback was attached. 

### Example 8

```python
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
```

The end result of running this program is the same as the previous two examples, the total time of the program is less than the cummulative time of getting the URLs. Whether you use Gevent or Twisted is a matter of personal preference and coding style. Both are powerful libaries that provide mechanisms allowing the programmer to create asynchronous code.

## Conclusion

I hope this has helped you see and understand where and how asynchronous programming can be useful. If you're writing a program that's calculating PI to the millionth decimal place, asynchronous code isn't going to help at all. However, if you're trying to implement a server, or a program that does a significant amount of IO, it could make a huge difference. It's a powerful technique that can take your programs to the next level.
