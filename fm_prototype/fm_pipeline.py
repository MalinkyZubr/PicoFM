from threading import Thread, Lock
from abc import ABC, abstractmethod
from typing import Callable
from time import sleep
from math import sin


class AbstractLock(ABC):
    pass # will need this later for platform independence when converted to c++


class SharedBuffer:
    def __init__(self, buffer_length: int):
        self.push_lock: Lock = Lock()
        self.pull_lock: Lock = Lock()
        
        self.pull_lock.acquire()
        self.push_lock.acquire()
        
        self.source_value: float = 0.0

        self.buffer: list[float] = [0.0 for x in range(buffer_length)]

    def pull_head(self) -> float:
        self.push_lock.release()
        
        value: float = self.buffer[-1]
        self.buffer = [self.source_value] + self.buffer[0:-1]
        
        self.pull_lock.acquire()
        
        return value
    
    def push_tail(self, value: float) -> None:
        self.push_lock.acquire()
        
        self.source_value = value 
        
        self.pull_lock.release()
    
    
class AbstractPipelineStep(ABC):
    def __init__(self):
        self.entry_buffer: SharedBuffer = None
        self.exit_buffer: SharedBuffer = None
        
    def add_source(self, source: SharedBuffer) -> None:
        if not self.entry_buffer:
            self.entry_buffer = source
        else:
            raise AttributeError("Cannot assign multiple source nodes to Pipeline step")
        
    def set_sink(self, sink: SharedBuffer) -> None:
        self.exit_buffer = sink

    @abstractmethod
    def computation(self, value: float) -> float:
        pass

    def call(self):
        value: float = self.entry_buffer.pull_head()
        computed_value: float = self.computation(value)
        self.exit_buffer.push_tail(computed_value)

        
class AbstractThreadUnit(ABC): # must be abstracted in prototype to simulate when library will be platform independent
    num_threads: int = 0
    
    def __init__(self, function: list[Callable]):
        self.functions: list[Callable] = function
        self.runflag = False
        
        AbstractThreadUnit.num_threads += 1
        
        self.thread_number: int = AbstractThreadUnit.num_threads

    def run_function_pool(self):
        while self.runflag:
            for action in self.functions:
                action()
        
    @abstractmethod
    def run(self):
        pass
    
    @abstractmethod
    def join(self):
        pass

class AbstractThreadOrchestrator(ABC):
    def associate(self, source: Callable, sink: Callable, function_pool: list[AbstractPipelineStep]):
        self.source: Callable = source
        self.sink: Callable = sink
        self.function_pool: list[AbstractPipelineStep] = function_pool
        self.threading_pool: list[AbstractThreadUnit] = []

    @abstractmethod
    def orchestrate_threads(self, source: Callable, sink: Callable, function_pool: list[AbstractPipelineStep]) -> list[AbstractThreadUnit]:
        pass

    def run(self) -> None:
        self.threading_pool = self.orchestrate_threads(self.source, self.sink, self.function_pool)
        for thread in self.threading_pool:
            thread.runflag = True
            thread.run()
        
    def end(self) -> None:
        for thread in self.threading_pool:
            thread.runflag = False
            thread.join()


class Pipeline:
    def __init__(self, source: Callable, sink: Callable, buffer_length: int, max_threads: int):
        self.source: Callable = source
        self.sink: Callable = sink

        self.source_buffer: SharedBuffer = SharedBuffer(buffer_length)
        self.sink_buffer: SharedBuffer = SharedBuffer(buffer_length)

        self.selected_step: AbstractPipelineStep = None
        
        self.num_steps: int = 2
        self.max_threads: int = max_threads
        
        if buffer_length < 1:
            raise ValueError("Buffer length must be at least 1")

        self.buffer_length: int = buffer_length
        self.function_pool: list[AbstractPipelineStep] = []
        self.thread_orchestrator: AbstractThreadOrchestrator = None
        
    def add_element(self, step: AbstractPipelineStep):
        if not self.selected_step:
            step.add_source(self.source_buffer)
            step.set_sink(self.sink_buffer)
        else:
            shared_buffer: SharedBuffer = SharedBuffer(self.buffer_length)
            
            self.selected_step.set_sink(shared_buffer)
            step.add_source(shared_buffer)
            step.set_sink(self.sink_buffer)
        
        self.function_pool.append(step)
        self.selected_step = step
        self.num_steps += 1

    def __fill_source_buffer(self):
        push_value: float = self.source()
        self.source_buffer.push_tail(push_value)
        
        print(self.source_buffer.buffer, end=" -> ")

    def __pull_sink_buffer(self):
        print(f"STEP RESULT: {self.sink_buffer.source_value} -> {self.sink_buffer.buffer}", end="\r")
        pull_value: float = self.sink_buffer.pull_head()
        self.sink(pull_value)
        
    def run(self, thread_orchestrator: AbstractThreadOrchestrator) -> None:
        self.thread_orchestrator = thread_orchestrator
        print("Now associating threads")
        self.thread_orchestrator.associate(self.__fill_source_buffer, self.__pull_sink_buffer, self.function_pool)

        self.thread_orchestrator.run()
        
    def end(self) -> None:
        self.thread_orchestrator.end()
            

# barebones implementations
class TestPipelineStep(AbstractPipelineStep):
    def computation(self, value: float) -> float:
        return value * 2
    
class TestThreadUnit(AbstractThreadUnit):
    def __init__(self, functions: list[Callable]):
        super().__init__(functions)
        self.thread: Thread = Thread(target=self.run_function_pool)

    def run(self):
        print(f"starting the thread {self.thread_number}")
        self.thread.start()

    def join(self):
        self.thread.join()

class TestThreadOrchestrator(AbstractThreadOrchestrator):
    def orchestrate_threads(self, source: Callable, sink: Callable, function_pool: list[AbstractPipelineStep]) -> list[AbstractThreadUnit]:
        threading_pool = []

        threading_pool.append(TestThreadUnit([source]))
        for task in function_pool:
            threading_pool.append(TestThreadUnit([task.call]))
        threading_pool.append(TestThreadUnit([sink]))

        return threading_pool
    
def test_source() -> float:
    global count
    sleep(0.5)
    
    return int(100 * sin(count))

count = 1
def test_sink(value: float) -> None:
    global count
    count+=1
            
if __name__ == "__main__":
    pipeline = Pipeline(test_source, test_sink, 10, 1)
    step = TestPipelineStep()
    pipeline.add_element(step)
    print(step.entry_buffer)
    print(step.exit_buffer)
    print(pipeline.function_pool)

    pipeline.run(TestThreadOrchestrator())

    
    