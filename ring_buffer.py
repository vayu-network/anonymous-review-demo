from typing import List


class RingBuffer:
    def __init__(self, capacity: int) -> None:
        """Create a ring buffer with the given fixed capacity.

        raises: ValueError
        post: self.capacity == capacity
        post: self.size() == 0
        """
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity: int = capacity
        self._data: List[int] = []

    def push(self, value: int) -> None:
        """Append value, overwriting the oldest value if the buffer is full.

        post: self.size() <= self.capacity
        post: self.size() >= 1
        post: self.size() == (__old__.self.size() if __old__.self.size() == self.capacity else __old__.self.size() + 1)
        post: self._data[-1] == value
        """
        if self.is_full():
            self._data.pop(0)
        self._data.append(value)

    def pop(self) -> int:
        """Remove and return the oldest value.

        raises: IndexError
        post: self.size() == __old__.self.size() - 1
        post: self.size() >= 0
        post: self.size() <= self.capacity
        post: __return__ == __old__.self._data[0]
        """
        if not self._data:
            raise IndexError("pop from empty buffer")
        return self._data.pop(0)

    def size(self) -> int:
        """Return the number of buffered values.

        post: __return__ >= 0
        post: __return__ <= self.capacity
        post: __return__ == len(self._data)
        """
        return len(self._data)

    def is_full(self) -> bool:
        """Return whether the buffer currently holds capacity values.

        post: __return__ == (self.size() == self.capacity)
        """
        return len(self._data) == self.capacity

# Veridict demo: an agent-assisted edit that must carry evidence.
