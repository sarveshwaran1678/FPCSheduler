## Running the Script

To run the FPC Scheduler script, follow these steps:

1. Ensure that you have Python installed on your system. The script is compatible with Python 3.6 or later versions.

2. Open a terminal or command prompt and navigate to the directory where the `FPCScheduler.py` file is located.

3. Run the following command:

python3 FPCScheduler.py

This command will execute the `FPCScheduler.py` script and start the FPC Scheduler simulation.

After running the command, you should see the output from the simulation in your terminal or command prompt window. The output will show the various stages of the FPC Scheduler, including handling requests, creating containers, processing responses, updating average execution times, and renewing snapshots.


# Function Parallel Container (FPC) Scheduler

This Python script implements a Function Parallel Container (FPC) Scheduler, which is responsible for managing and scheduling requests for different functions across multiple containers. The scheduler aims to efficiently handle incoming requests and allocate resources (containers) dynamically based on the load and the average execution time of the functions.

## Overview

The FPC Scheduler is designed to handle multiple functions simultaneously. For each function, it maintains a separate request queue, a priority queue for containers, and a set of containers that can execute requests for that function. The scheduler periodically checks the request queues and adjusts the number of containers based on the current load and the average execution time of the function.

The main components of the FPC Scheduler are:

- `Container`: Represents an individual container that can execute requests for a specific function.
- `Scheduler`: The main coordinator that manages different `FPCSchedulerForFunction` instances for each function.
- `FPCSchedulerForFunction`: Handles request scheduling, container provisioning, and snapshot management for a specific function.
- `Request` and `Response`: Represent incoming requests and their corresponding responses.

## Usage

To run the FPC Scheduler, simply execute the script:


python FPCScheduler.py


This will simulate requests and responses for two functions (`"function_id_1"` and `"function_id_2"`). You can modify the `function_ids` list in the main script to add or remove functions as needed.

The script will create separate threads for simulating requests and responses for each function. Requests are generated with random sequence numbers and random intervals between 0.4 and 1 second. Responses are simulated by introducing a random execution time between 0.1 and 0.2 seconds.

## Algorithm

The FPC Scheduler follows a specific algorithm to determine the number of containers to create or remove for each function. The algorithm is based on four conditions:

1. **Condition 1**: If there are no existing containers and no containers being created, create one container initially.
2. **Condition 2**: If there are no existing containers, create as many containers as the number of requests in the queue.
3. **Condition 3**: If the number of containers (existing and being created) is less than the number of requests in the queue, and the number of new arrivals is less than the number of requests in the queue, create additional containers based on the required number of containers.
4. **Condition 4**: If the number of containers (existing and being created) is less than the number of requests in the queue, and the number of new arrivals is greater than or equal to the product of the average parallelism and the total number of containers, create additional containers based on the required number of containers.

The algorithm also considers the average execution time of the function, which is updated dynamically based on the last 10 execution times.

## Implementation Details

- The `Scheduler` class manages multiple `FPCSchedulerForFunction` instances, one for each function.
- The `FPCSchedulerForFunction` class is responsible for handling requests, managing containers, and applying the FPC algorithm for a specific function.
- The `Container` class represents an individual container that can execute requests for a function.
- The `Request` and `Response` classes represent incoming requests and their corresponding responses.
- The `simulate_requests` and `simulate_responses` functions simulate the generation of requests and responses for each function, respectively.
- The script uses the `heapq` module to maintain a priority queue for containers.
- The `Timer` class from the `threading` module is used to run a periodic task that renews snapshots and provisions containers based on the FPC algorithm.

## Example Output

```
function_id_1 - Adding request 62 for function_id_1
function_id_1 - Handling request 62
function_id_1 - Renewed snapshot at tick 0  
 Q_begin: 0  
 Q_end: 1  
 C_created : 0  
 C_creating : 0
function_id_1 - Condition 1: Creating one container initially
function_id_1 - Creating 1 containers
function_id_1 - Pulling request 62 in container function_id_1_0
function_id_1 - Assigned request 62 to container function_id_1_0
function_id_1 - Processing response 62 for function_id_1
function_id_1 - Handling response for sequence 62
No execution times available, using default TICK_INTERVAL
function_id_1 - Container function_id_1_0 is idle: False
function_id_1 - Container function_id_1_0 finished at 10.0 lasted 0.10779953956604004
function_id_1 - Renewed snapshot at tick 1  
 Q_begin: 1  
 Q_end: 1  
 C_created : 1  
 C_creating : 0
function_id_1 - Updated average function execution time: 0.10779953956604004
...
```

This example output shows the various stages of the FPC Scheduler, including handling requests, creating containers, processing responses, updating average execution times, and renewing snapshots.

