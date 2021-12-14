from multiprocessing import Process, Manager
import time
from reem.connection import RedisInterface, CallbackSubscriber, PublishSpace
from tests.testing import plot_performance

interface = RedisInterface()
publisher = PublishSpace(interface)


class Subscriber(Process):
    def __init__(self):
        self.manager = Manager()
        self.time_list = self.manager.list([])
        self.kill = False
        self.subscriber = None
        self.last_time = time.time() + 1
        super().__init__()

    def callback(self, data, updated_path):
        sent_time = data["timestamp"]
        self.time_list.append((time.time() - sent_time) * 1000)
        self.last_time = time.time()
        # print("Called")

    def run(self):
        self.subscriber = CallbackSubscriber("pub_sub_performance_test", interface, self.callback, {})
        self.subscriber.listen()
        while time.time() - self.last_time < 1:
            # print(len(self.time_list))
            pass
        print("Killed")


def pub_sub_test():
    trials = 100
    data = {}
    for subs in [0,0,1, 10]:
        subscribers = [Subscriber() for i in range(subs)]
        for s in subscribers:
            s.start()
        time.sleep(1)
        for i in range(trials):
            publisher["pub_sub_performance_test"] = {"timestamp": time.time()}
            time.sleep(0.01)
        time.sleep(3)
        times = []
        for s in subscribers:
            s.kill = True
            print("Main Thread: " + str(s.kill))
            times += s.time_list
        data[subs] = times
    return data
    # print("{}:{},".format(num_subcsribers, times))


def pub_sub_plotter(data):
    info = {"title": "Subscriber Overhead", "plots": [], "x_label": "Number of Subscribers", "y_label": "Transmission Time (ms)"}
    for num, times in data.items():
        p = {
            "ticker_label": num,
            "times": times
        }
        info["plots"].append(p)
    plot_performance(info)


data = pub_sub_test()
print(data)
pub_sub_plotter(data)