import heapq
import time
import random
import math
from queue import Queue
from threading import Thread,Timer

TICK_INTERVAL = 100  # milliseconds 0.1 seconds
MAX_IDLE_TIME = 15000  # milliseconds 15 seconds

class Container:
    def __init__(self, function_id, container_id):
        self.function_id = function_id
        self.container_id = container_id
        self.state = "idle"
        self.last_execution_time = 0
        self.idle_since = time.time()

    def pull_request(self, request):
        print(f"{self.function_id} - Pulling request {request.sequence_number} in container {self.container_id}")
        self.state = "busy"
        self.idle_since = time.time()
        self.last_execution_time = request.execution_time

    def finish(self):
        self.state = "idle"
        now = time.time()
        print(f"{self.function_id} - Container {self.container_id} finished at {self.last_execution_time} lasted {now - self.last_execution_time}")
        self.last_execution_time = time.time()

    def is_idle(self):
        idle = (time.time() - self.idle_since) * 1000 > MAX_IDLE_TIME
        print(f"{self.function_id} - Container {self.container_id} is idle: {idle}")
        return idle

class Snapshot:
    def __init__(self):
        self.Q_begin = 0
        self.Q_end = 0
        self.C_created = 0
        self.C_creating = 0

class Scheduler:
    def __init__(self, function_ids):
        self.function_schedulers = {fid: FPCSchedulerForFunction(fid) for fid in function_ids}
        self.periodic_task()

    def handle_request(self, request):
        function_scheduler = self.function_schedulers[request.function_id]
        function_scheduler.handle_request(request)

    def handle_response(self, response):
        function_scheduler = self.function_schedulers[response.function_id]
        function_scheduler.handle_response(response)

    def periodic_task(self):
        for function_scheduler in self.function_schedulers.values():
            function_scheduler.renew_snapshot()
            function_scheduler.provision_containers()
        Timer(TICK_INTERVAL / 1000, self.periodic_task).start()

class FPCSchedulerForFunction:
    def __init__(self, function_id):
        self.function_id = function_id
        self.Q_begin = 0
        self.Q_end = 0
        self.C_created = 0
        self.C_creating = 0
        self.tick = 0
        self.T_avg_func_exec = TICK_INTERVAL
        self.S = [Snapshot()]  # list of snapshots
        self.request_queue = Queue()
        self.containers = {}  # container_id -> Container
        self.priority_queue = []  # min-heap of (priority, container_id)
        self.last_execution_times = []  # list of last N execution times

    def renew_snapshot(self):
        if self.request_queue.qsize() == 0:
            s = Snapshot()
            s.C_created = self.C_created
            s.C_creating = self.C_creating
            self.S[self.tick] = s
        else:
            if self.Q_end - self.Q_begin > 0 or (self.tick > 0 and self.Q_end - self.S[self.tick].Q_end > 0):
                self.tick += 1
                s = Snapshot()
                s.Q_begin = self.Q_begin
                s.Q_end = self.Q_end
                s.C_created = self.C_created
                s.C_creating = self.C_creating
                self.S.append(s)
            self.T_avg_func_exec = self.update_avg_func_exec_time()
        print(f"{self.function_id} - Renewed snapshot at tick {self.tick}  \n Q_begin: {self.Q_begin}  \n Q_end: {self.Q_end}  \n C_created : {self.C_created}  \n C_creating : {self.C_creating}")

    def update_avg_func_exec_time(self):
        if not self.last_execution_times:
            print("No execution times available, using default TICK_INTERVAL")
            return TICK_INTERVAL
        avg_exec_time = sum(self.last_execution_times) / len(self.last_execution_times)
        print(f"{self.function_id} - Updated average function execution time: {avg_exec_time}")
        return avg_exec_time

    def provision_containers(self):
        C_shortage = 0
        C_total = self.S[self.tick].C_created + self.S[self.tick].C_creating
        R_in_queue = self.S[self.tick].Q_end - self.S[self.tick].Q_begin

        if self.tick == 1:
            if self.S[self.tick].C_creating == 0:  # condition 1
                C_shortage = 1
                print(f"{self.function_id} - Condition 1: Creating one container initially")
            else:  # condition 2
                C_shortage = self.Q_end - self.S[self.tick].C_creating
                print(f"{self.function_id} - Condition 2: Creating {C_shortage} containers")
        else:
            if C_total < R_in_queue:
                P_container = TICK_INTERVAL / self.T_avg_func_exec
                R_arrivals = self.S[self.tick].Q_end - self.S[self.tick - 1].Q_end
                C_required = math.ceil(R_in_queue / P_container)
                if R_arrivals < R_in_queue:  # condition 3
                    C_shortage = C_required - self.S[self.tick].C_creating
                    print(f"{self.function_id} - Condition 3: Creating {C_shortage} containers")
                elif R_arrivals >= P_container * C_total:  # condition 4
                    C_shortage = C_required - C_total
                    print(f"{self.function_id} - Condition 4: Creating {C_shortage} containers")

        if C_shortage > 0:
            self.create_containers(min(C_shortage, R_in_queue))

    def create_containers(self, num_containers):
        print(f"{self.function_id} - Creating {num_containers} containers")
        for _ in range(int(num_containers)):
            container_id = f"{self.function_id}_{len(self.containers)}"
            container = Container(self.function_id, container_id)
            self.containers[container_id] = container
            self.priority_queue.append((container_id, container_id))
            heapq.heapify(self.priority_queue)
            self.C_creating += 1

    def handle_request(self, request):
        print(f"{request.function_id} - Handling request {request.sequence_number}")
        self.request_queue.put(request)
        self.Q_end += 1
        self.renew_snapshot()
        self.provision_containers()

        if self.priority_queue:
            _, container_id = heapq.heappop(self.priority_queue)
            container = self.containers[container_id]
            container.pull_request(request)
            heapq.heappush(self.priority_queue, (container_id, container_id))
            print(f"{request.function_id} - Assigned request {request.sequence_number} to container {container_id}")
        else:
            print(f"{request.function_id} - No available container for request {request.sequence_number}")

    def handle_response(self, response):
        print(f"{response.function_id} - Handling response for sequence {response.sequence_number if response else 'None'}")
        if response:
            self.Q_begin += 1
            self.last_execution_times.append(response.execution_time)
            if len(self.last_execution_times) > 10:
                self.last_execution_times.pop(0)
            if self.C_creating > 0 :
                self.C_created += 1
                self.C_creating -= 1

        # Remove idle containers
        for container_id, container in self.containers.items():
            if container.is_idle():
                del self.containers[container_id]
                if self.priority_queue:
                    self.priority_queue.remove((container_id, container_id))
                    heapq.heapify(self.priority_queue)
                self.C_created -= 1
                print(f"{self.function_id} - Removed idle container {container_id}")

class Request:
    def __init__(self, function_id, sequence_number):
        self.function_id = function_id
        self.sequence_number = sequence_number
        self.execution_time = 0

class Response:
    def __init__(self, function_id, sequence_number, execution_time):
        self.function_id = function_id
        self.sequence_number = sequence_number
        self.execution_time = execution_time

def simulate_requests(function_id, request_queue, scheduler):
    while True:
        sequence_number = random.randint(1, 100)
        request = Request(function_id, sequence_number)
        request_queue.put(request)
        print(f"{function_id} - Adding request {request.sequence_number} for {function_id}")
        scheduler.handle_request(request)
        time.sleep(random.uniform(0.4, 1))  # Random interval between 0.1 and 1 second

def simulate_responses(function_id, request_queue, response_queue, scheduler):
    while True:
        while not request_queue.empty():
            request = request_queue.get()

            # Simulate function execution
            time.sleep(random.uniform(0.1, 0.2))  # Random execution time between 0.1 and 0.2 seconds

            response = Response(function_id, request.sequence_number, 10)
            scheduler.handle_response(response)
            response_queue.put(response)
            print(f"{function_id} - Processing response {response.sequence_number} for {function_id}")

        time.sleep(0.01)  # Yield control to other threads

if __name__ == "__main__":
    function_ids = ["function_id_1","function_id_2"]
    request_queues = {fid: Queue() for fid in function_ids}
    response_queues = {fid: Queue() for fid in function_ids}
    scheduler = Scheduler(function_ids)

    request_threads = [Thread(target=simulate_requests, args=(fid, request_queues[fid], scheduler)) for fid in function_ids]
    response_threads = [Thread(target=simulate_responses, args=(fid, request_queues[fid], response_queues[fid], scheduler)) for fid in function_ids]

    for thread in request_threads + response_threads:
        thread.start()

    for thread in request_threads + response_threads:
        thread.join()