from om_lite.core.options_dictionary import OptionsDictionary


class System(object):
    def __init__(self, **kwargs):
        self.options = OptionsDictionary()

    # def initialize(self):
    #     pass

    @property
    def nonlinear_solver(self):
        """
        Get the nonlinear solver for this system.
        """
        return self._nonlinear_solver

    @nonlinear_solver.setter
    def nonlinear_solver(self, solver):
        """
        Set this system's nonlinear solver.
        """
        self._nonlinear_solver = solver

    @property
    def linear_solver(self):
        """
        Get the linear solver for this system.
        """
        return self._linear_solver

    @linear_solver.setter
    def linear_solver(self, solver):
        """
        Set this system's linear solver.
        """
        self._linear_solver = solver

    @property
    def nonlinear_solver(self):
        """
        Get the nonlinear solver for this system.
        """
        return self._nonlinear_solver

    def add_constraint(self,
                       name,
                       lower=None,
                       upper=None,
                       equals=None,
                       ref=None,
                       ref0=None,
                       adder=None,
                       scaler=None,
                       units=None,
                       indices=None,
                       linear=False,
                       parallel_deriv_color=None,
                       vectorize_derivs=False,
                       cache_linear_solution=False):
        pass

    def add_objective(self,
                      name,
                      ref=None,
                      ref0=None,
                      index=None,
                      units=None,
                      adder=None,
                      scaler=None,
                      parallel_deriv_color=None,
                      vectorize_derivs=False,
                      cache_linear_solution=False):
        pass