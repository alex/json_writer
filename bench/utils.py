import time


def run_benchmark(func, data):
    times = []
    for i in xrange(5):
        t = time.time()
        func(data)
        times.append(time.time() - t)
    print "Best:    %f" % min(times)
    print "Worst:   %f" % max(times)
    print "Average: %f" % (sum(times) / len(times))
