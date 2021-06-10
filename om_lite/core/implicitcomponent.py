from om_lite.core.component import Component


class ImplicitComponent(Component):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._residuals_list = []

        self.initialize()
        self.options.update(kwargs)

    def apply_nonlinear(self):
        pass

    def _solve_nonlinear(self, inputs, outputs, tol):
        self.solve_nonlinear(inputs, outputs, tol)
        for output_name in self._outputs_list:
            self.inputs[output_name] = self.outputs[output_name]

    def guess_nonlinear(self):
        pass

    def apply_linear(self):
        pass

    def solve_linear(self):
        pass

    def linearize(self):
        pass