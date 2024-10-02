from threading import Thread, Lock
from abc import ABC, abstractmethod
from typing import Callable


class SharedBuffer:
    def __init__(self, buffer_length: int):
        self.buffer: list[float] = [0.0 for x in range(buffer_length)]
        
        self.push_lock: Lock = Lock()
        self.pull_lock: Lock = Lock()
        
        self.pull_lock.acquire()
        
    def pull_head(self) -> float:
        self.pull_lock.acquire()
        
        value = self.buffer[-1]
        self.buffer = [0] + self.buffer[0:-1]
        
        self.push_lock.release()
        
        return value
    
    def push_tail(self, value: float) -> None:
        self.push_lock.acquire()
        
        self.buffer[0] = value
        
        self.pull_lock.release()
            
            
class AbstractSourceNode:
    @abstractmethod
    def push(self, value: float) -> None:
        self.shared_buffer.push_tail(value)
        

class AbstractSinkNode:
    @abstractmethod
    def pull(self) -> float:
        return self.shared_buffer.pull_head()
    
    
class AbstractPipelineStart:
    pass


class AbstractPipelineEnd:
    pass

            
class BufferStartNode(ABC):
    def __init__(self, buffer: SharedBuffer):
        self.shared_buffer: SharedBuffer = buffer
        
    def push(self, value: float) -> None:
        self.shared_buffer.push_tail(value)
        

class BufferEndNode(ABC):
    def __init__(self, buffer: SharedBuffer):
        self.shared_buffer: SharedBuffer = buffer
    
    def pull(self) -> float:
        return self.shared_buffer.pull_head()
    
    
class AbstractPipelineStep(ABC):
    def __init__(self):
        self.source_node: AbstractSourceNode = None
        self.sink_node: AbstractSinkNode = None
        
    def add_source(self, source: AbstractSourceNode) -> None:
        if not self.source_node:
            self.source_node = source
        else:
            raise AttributeError("Cannot assign multiple source nodes to Pipeline step")
        
    def set_sink(self, sink: AbstractSinkNode) -> None:
        self.sink_node = sink
        
        
class AbstractThreadUnit(ABC): # must be abstracted in prototype to simulate when library will be platform independent
    def __init__(self, function: Callable):
        self.function: Callable = function
        
    @abstractmethod
    def run(self):
        pass
    
    @abstractmethod
    def join(self):
        pass
    

class Pipeline:
    def __init__(self, source: AbstractSourceNode, sink: AbstractSinkNode, buffer_length: int, max_threads: int):
        self.source: AbstractSourceNode = source
        self.sink: AbstractSinkNode = sink
        self.selected_step: AbstractPipelineStep = None
        
        self.num_steps: int = 2
        self.max_threads: int = max_threads
        
        if buffer_length < 1:
            raise ValueError("Buffer length must be at least 1")

        self.buffer_length: int = buffer_length
        
        self.threading_pool: list[AbstractThreadUnit] = []
        
    def add_element(self, step: AbstractPipelineStep):
        if not self.selected_step:
            step.add_source(self.source)
            step.set_sink(self.sink)
        else:
            shared_buffer: SharedBuffer = SharedBuffer(self.buffer_length)
            buffer_start_node: BufferStartNode = BufferStartNode(shared_buffer)
            buffer_end_node: BufferEndNode = BufferEndNode(shared_buffer)
            
            self.selected_step.set_sink(buffer_start_node)
            step.add_source(buffer_end_node)
            step.set_sink(self.sink)
        
        self.selected_step = step
        self.num_steps += 1
        
    def run(self) -> None:
        steps_per_thread: int = int((self.num_steps / self.max_threads) + 1)
        
    
    def end(self) -> None:
        pass
            
            
if __name__ == "__main__":
    pipeline = Pipeline(AbstractSourceNode(), AbstractSinkNode(), 3)
    step = AbstractPipelineStep()
    pipeline.add_element(step)
    print(step.source_node)
    print(step.sink_node)
    
    step = AbstractPipelineStep()
    pipeline.add_element(step)
    print(step.source_node)
    print(step.sink_node)
    

    
    