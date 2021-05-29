from om_lite.core.component import Component


class ImplicitComponent(Component):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize()
        self.options.update(kwargs)

    def apply_nonlinear(self):
        pass

    def solve_nonlinear(self):
        pass

    def guess_nonlinear(self):
        pass

    def apply_linear(self):
        pass

    def solve_linear(self):
        pass

    def linearize(self):
        pass