import numpy as np

from om_lite.core.system import System
from om_lite.core.indepvarcomp import IndepVarComp
from om_lite.core.explicitcomponent import ExplicitComponent
from om_lite.core.implicitcomponent import ImplicitComponent


class Model(System):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = {}
        self.outputs = {}
        self.partials = {}
        self.residuals = {}
        # self.iv_components_list = []
        self.ex_components_list = []
        self.im_components_list = []

    def add_subsystem(self, name, comp):
        # self.name = comp
        setattr(self, name, comp)
        if isinstance(comp, IndepVarComp):
            comp.inputs = self.inputs  # Even though ivc's don't have inputs, their outputs can also be inputs to other componentsin the model
            comp.outputs = self.outputs
            comp.setup()

        elif isinstance(comp, ExplicitComponent):
            comp.inputs = self.inputs
            comp.outputs = self.outputs
            comp.partials = self.partials
            comp.setup()

        elif isinstance(comp, ImplicitComponent):
            comp.inputs = self.inputs
            comp.outputs = self.outputs
            comp.partials = self.partials
            comp.residuals = self.residuals
            comp.setup()

    def setup(self):
        # Setup (Note: Promotes all)

        # for comp in self.iv_components_list:
        #     comp.inputs = self.inputs
        #     comp.outputs = self.outputs
        #     comp.partials = self.partials
        #     comp.setup()

        for comp in self.ex_components_list:
            comp.inputs = self.inputs
            comp.outputs = self.outputs
            comp.partials = self.partials
            comp.setup()

        for comp in self.im_components_list:
            comp.inputs = self.inputs
            comp.outputs = self.outputs
            comp.partials = self.partials
            comp.residuals = self.residuals
            comp.setup()

        pass

    def setup_partials(self):
        pass

    def set_val(self, name, val):
        if name in self.inputs:
            # need more raise error to ensure same type and shape.
            self.inputs[name] = val

        elif name in self.outputs:
            self.outputs[name] = val

        else:
            raise Exception("Given name is not in inputs or outputs")

    def add_input(self,
                  name,
                  val=1.0,
                  shape=None,
                  src_indices=None,
                  flat_src_indices=None,
                  units=None,
                  desc=''):
        if shape is None:
            self.inputs[name] = val
        else:
            self.inputs[name] = np.zeros(shape, dtype=float)

    def add_output(self,
                   name,
                   val=1.0,
                   shape=None,
                   units=None,
                   res_units=None,
                   desc='',
                   lower=None,
                   upper=None):
        if shape is None:
            self.outputs[name] = val
        else:
            self.outputs[name] = np.zeros(shape, dtype=float)

    def declare_partials(self,
                         of,
                         wrt,
                         dependent=True,
                         rows=None,
                         cols=None,
                         val=None,
                         method='exact'):
        def _declare_partials(of, wrt):
            if rows is None:
                if val is None:
                    if type(self.outputs[of]) == float:
                        if type(self.inputs[wrt]) == float:
                            self.partials[of, wrt] = np.zeros((1, 1))
                        else:
                            self.partials[of, wrt] = np.zeros(
                                (1, self.inputs[wrt].size))

                    elif type(self.inputs[wrt]) == float:
                        self.partials[of, wrt] = np.zeros(
                            (self.outputs[of].size, 1))

                    else:
                        self.partials[of, wrt] = np.zeros(
                            (self.outputs[of].size, self.inputs[wrt].size))
                else:
                    self.partials[of, wrt] = val
            else:
                if val is None:
                    self.partials[of, wrt, 'coo'] = (rows, cols)
                    self.partials[of, wrt] = np.zeros((rows.size, ),
                                                      dtype=float)
                else:
                    self.partials[of, wrt, 'coo'] = (rows, cols)
                    self.partials[of, wrt] = val

        if of == '*' and wrt == '*':
            for of_ in self.outputs:
                for wrt_ in self.inputs:
                    _declare_partials(of_, wrt_)

        elif of == '*':
            for of_ in self.outputs:
                _declare_partials(of_, wrt)

        elif wrt == '*':
            for wrt_ in self.inputs:
                _declare_partials(of, wrt_)

        else:
            _declare_partials(of, wrt)

    def set_check_partial_options(self,
                                  wrt,
                                  method='fd',
                                  form=None,
                                  step=None,
                                  step_calc=None,
                                  directional=False):
        pass