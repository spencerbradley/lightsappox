
class DMXFrame:
    def __init__(self):
        self.channels = 512
        self.values: tuple = tuple([0] * self.channels)

    def set_values(self, values: list[int]) -> None:
        self.values = tuple(values)
        if len(self.values) != self.channels:
            adder = self.channels - len(self.values)
            self.values = self.values + tuple([0] * adder)


    def get_values(self) -> tuple:
        return self.values