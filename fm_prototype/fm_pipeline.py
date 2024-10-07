from threading import Thread, Lock
from abc import ABC, abstractmethod
from typing import Callable
from time import sleep
from math import pi, sin, cos, e


def range_wraparound(value: float, min_value: float, max_value: float) -> float:
    range = max_value - min_value

    while value > max_value:
        value -= range
    while value < min_value:
        value += range
    
    return value


class DSPTimeSync:
    def __init__(self, sps: int, start_time: float = 0.0):
        self.sps: int = sps
        self.time: float = start_time
        self.time_step: float = 1.0 / self.sps
    
    def increment_time(self) -> None:
        self.time = range_wraparound(self.time + self.time_step, 0, 2 * pi)

    def get_time(self) -> float:
        time_value: float = self.time

        return time_value


class AbstractLock(ABC):
    pass # will need this later for platform independence when converted to c++


class AbstractBuffer(ABC):
    def __init__(self, buffer_length: int, samples_per_second: int):
        self.push_lock: Lock = Lock()
        self.pull_lock: Lock = Lock()
        
        self.pull_lock.acquire()
        self.push_lock.acquire()

        self.samples_per_second: int = samples_per_second
        self.buffer: list[float] = [0.0 for x in range(buffer_length)]

    @abstractmethod
    def pull_operation(self) -> list[float]:
        pass

    @abstractmethod
    def push_operation(self, value: list[float]) -> list[float]:
        pass

    def pull(self) -> list[float]:
        self.push_lock.release()
        
        value: list[float] = self.pull_operation()
        
        self.pull_lock.acquire()
        
        return value
    
    def push(self, value: list[float]) -> None:
        self.push_lock.acquire()
        
        self.push_operation(value)
        
        self.pull_lock.release()

    def grab_all(self, value: list[float]) -> list[float]:
        return self.buffer

class TimeDomainBuffer(AbstractBuffer):
    def __init__(self, buffer_length: int, samples_per_second: int):
        super().__init__(buffer_length, samples_per_second)
        self.source_value: float = 0.0

    def pull_operation(self) -> list[float]:
        value: float = self.buffer[-1]
        self.buffer = [self.source_value] + self.buffer[0:-1]
        
        return [value]
    
    def push_operation(self, value: list[float]) -> None:
        if len(value) != 1:
            raise ValueError("Time domain values must be scalar (1 element list)")
        self.source_value = value[0]


class FrequencyDomainBuffer(AbstractBuffer):
    def __init__(self, buffer_length: int, samples_per_second: int):
        super().__init__(buffer_length)
        self.frequencies: list[float] = [k * (samples_per_second / buffer_length) for k in range(buffer_length)]

    def pull_operation(self) -> list[float]:
        return self.buffer
    
    def push_operation(self, value: list[float]) -> None:
        if len(value) != len(self.buffer):
            raise ValueError("Frequency domain buffers must remain constant throughout")
        self.buffer = value

    def get_real(self) -> list[float]:
        return [abs(frequency) for frequency in self.buffer]

class AbstractPipelineStep(ABC): # at the rewrite, the type system with template classes will enforce the use of time or frequency domain buffers
    def __init__(self):
        self.entry_buffer: AbstractBuffer = None
        self.exit_buffer: AbstractBuffer = None
        self.dsp_time_sync: DSPTimeSync = None
        
    def add_source(self, source: AbstractBuffer) -> None:
        if not self.entry_buffer:
            self.entry_buffer = source
        else:
            raise AttributeError("Cannot assign multiple source nodes to Pipeline step")
        
    def add_time_sync(self, time_sync: DSPTimeSync) -> None:
        self.dsp_time_sync = time_sync
        
    def set_sink(self, sink: AbstractBuffer) -> None:
        self.exit_buffer = sink

    @abstractmethod
    def computation(self, value: list[float]) -> list[float]:
        pass

    def call(self):
        value: list[float] = self.entry_buffer.pull()
        computed_value: list[float] = self.computation(value)
        self.exit_buffer.push(computed_value)


class DFTStep(AbstractPipelineStep): # violates usual rule because it is the border between time and frequency domain
    def __init__(self, num_bins: int):
        self.num_bins: int = num_bins
        self.preallocated_exponentials: list[float] = [e ** (-2j * pi * k / num_bins) for k in range(num_bins)]

    def computation(self, value: list[float]) -> list[float]: # not using the value like usual will shift phase. Matters? not know. hopefully not! since it shifts all phase...
        amplitudes = self.entry_buffer.grab_all()
        frequency_bins: list[float] = []
        for k in self.preallocated_exponentials:
            frequency_contribution = 0
            for n in range(self.num_bins):
                amplitude_value = amplitudes[n]
                frequency_contribution += amplitude_value * (k ** n)
            frequency_bins.append(frequency_contribution)

        return frequency_bins
    

class IDFTStep(AbstractPipelineStep): # there must be a way to optimize these to work better with previous calculated values
    def __init__(self, num_bins: int):
        self.num_bins: int = num_bins
        self.preallocated_exponentials: list[float] = [e ** (2j * pi * k / num_bins) for k in range(num_bins)]

    def computation(self, value: list[float]) -> list[float]:
        time_domain: list[float] = []

        for k in self.preallocated_exponentials:
            time_domain_value = 0
            for n in range(self.num_bins):
                amplitude_value = value[n]
                time_domain_value += amplitude_value * (k ** n)
            time_domain.append(time_domain_value)
            
        return time_domain
        
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
    def __init__(self, source: Callable, sink: Callable, dsp_time_sync: DSPTimeSync, buffer_length: int, max_threads: int):
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
        self.time_sync: DSPTimeSync = dsp_time_sync
        
    def add_element(self, step: AbstractPipelineStep):
        if not self.selected_step:
            step.add_source(self.source_buffer)
        else:
            shared_buffer: SharedBuffer = SharedBuffer(self.buffer_length)
            
            self.selected_step.set_sink(shared_buffer)
            step.add_source(shared_buffer)
        
        step.add_time_sync(self.time_sync)
        step.set_sink(self.sink_buffer)

        self.function_pool.append(step)
        self.selected_step = step
        self.num_steps += 1

    def __fill_source_buffer(self):
        push_value: float = self.source()
        self.source_buffer.push(push_value)

    def __pull_sink_buffer(self):
        pull_value: float = self.sink_buffer.pull()
        self.sink(pull_value)

        self.time_sync.increment_time()
        
    def run(self, thread_orchestrator: AbstractThreadOrchestrator) -> None:
        self.thread_orchestrator = thread_orchestrator
        self.thread_orchestrator.associate(self.__fill_source_buffer, self.__pull_sink_buffer, self.function_pool)

        self.thread_orchestrator.run()
        
    def end(self) -> None:
        self.thread_orchestrator.end()
            

# barebones implementations
class TestPipelineStep(AbstractPipelineStep):
    def computation(self, value: float) -> float:
        return value * 2
    

class FMModulatorStep(AbstractPipelineStep):
    def __init__(self, sps: int, center_frequency: float, frequency_deviation: float):
        super().__init__()
        self.sps: int = sps
        self.center_frequency: float = center_frequency
        self.modulation_index: float = frequency_deviation / center_frequency

        self.phase_component: float = 0.0

    def computation(self, value: float) -> float: # value corresponds to sample of the modulating signal
        time: float = self.dsp_time_sync.get_time()
        self.phase_component += 2 * pi * self.modulation_index * (value * (1 / self.sps))
        self.phase_component = range_wraparound(self.phase_component, 0, 2 * pi)
        frequency_component: float = self.center_frequency * 2 * pi * time

        return cos(frequency_component + self.phase_component)


class TestThreadUnit(AbstractThreadUnit):
    def __init__(self, functions: list[Callable]):
        super().__init__(functions)
        self.thread: Thread = Thread(target=self.run_function_pool)

    def run(self):
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
    
count = 1

def test_source() -> float:
    global count
    sleep(0.05)
    
    return sin(1000 * 3.14 * count)

def test_sink(value: float) -> None:
    global count
    print(value, end="\r")
    count+=1
            
if __name__ == "__main__":
    SPS = 2000
    pipeline = Pipeline(test_source, test_sink, DSPTimeSync(SPS), 10, 1)
    step = TestPipelineStep()
    pipeline.add_element(step)

    print(step.entry_buffer)
    print(step.exit_buffer)

    #step = FMModulatorStep(SPS, 1000, 1)
    #pipeline.add_element(step)

    print(step.entry_buffer)
    print(step.exit_buffer)
    print(pipeline.function_pool)

    pipeline.run(TestThreadOrchestrator())