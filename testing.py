import datetime
import rejson

rejson_client = rejson.Client(host='localhost', port=6379, decode_responses=True)


def generate_data(format='string', strlen=100, b=0, kb=0, mb=0):
    date_string = str(datetime.datetime.now()) + " "
    if format == 'string':
        length = strlen
    elif format == 'binary':
        length = b + 1024 * kb + (1024 ** 2) * mb
    else:
        raise ValueError("format for generate data not recognized")

    data = "{}{}".format(date_string, "".join(["a" for i in range(length - len(date_string))]))

    if format == 'string':
        return data
    return data.encode()


def time_code_segment(func, kwargs):
    """ Time a function and return milliseconds it took to run"""
    start = datetime.datetime.now()
    func(**kwargs)
    return (datetime.datetime.now() - start).total_seconds() * 1000


def multitrial_time_test(func, kwargs, iterations=3):
    """ Run a segment of code @iterations number of times and return an array of
    times required to complete each iteration """

    times = []
    for i in range(iterations):
        times.append(time_code_segment(func, kwargs))
    return times


