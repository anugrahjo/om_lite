import om_lite.api as om

# from atomics.api import PDEProblem, AtomicsGroup

from atomics.api import PDEProblem

# from atomics.pdes.neo_hookean_addtive import get_residual_form

from atomics.general_filter_comp import GeneralFilterComp

from atomics.scalar_output_comp import ScalarOutputsComp
from atomics.field_output_comp import FieldOutputsComp


class HyperElasticModel(object):
    def setup(self, num_dof_density, density_function_space, pde_problem):
        self.inputs = {}
        self.outputs = {}
        self.partials = {}
        self.residuals = {}
        self.ex_components_list = []  # does not include IndepVarComp

        self.x = om.IndepVarComp()
        self.x.outputs = self.outputs
        self.x.add_output(
            'density_unfiltered',
            shape=num_dof_density,
            val=np.ones(num_dof_density),
            # val=x_val,
            # val=np.random.random(num_dof_density) * 0.86,
        )

        self.density_filter = GeneralFilterComp(
            density_function_space=density_function_space)
        self.ex_components_list.append(density_filter)
        # density_filter.setup()

        # group = AtomicsGroup(pde_problem=pde_problem)
        # components_list.append(group)

        self.c = ScalarOutputsComp(
            pde_problem=pde_problem,
            scalar_output_name='avg_density',
        )
        self.ex_components_list.append(c)
        # c.setup()

        self.y = FieldOutputsComp(
            pde_problem=pde_problem,
            field_output_name='displacements',
        )
        # self.ex_components_list.append(y)
        # y.setup()

        self.f = ScalarOutputsComp(
            pde_problem=pde_problem,
            scalar_output_name='compliance',
        )
        self.ex_components_list.append(f)
        # f.setup()

        # Setup (Note: Promotes all)
        for comp in self.ex_components_list:
            comp.inputs = self.inputs
            comp.outputs = self.outputs
            comp.partials = self.partials
            comp.setup()

        self.y.inputs = self.inputs
        self.y.outputs = self.outputs
        self.y.partials = self.partials
        self.y.setup()

    def run(self, x_val=None, y_val=None, psi=None, tol=None):
        # self.x.set_value()
        # self.res.warm_start(y)

        self.density_filter.compute(inputs, outputs)
        self.density_filter.compute_partials(inputs, outputs, partials)

        self.c.compute(inputs, outputs)
        self.c.compute_partials(inputs, outputs, partials)

        if tol == None:
            self.y.apply_nonlinear(inputs, outputs, tol)
        else:
            # solve_nonlinear is different from OM
            self.y.solve_nonlinear(inputs, outputs, tol)

        y.linearize(inputs, outputs, partials)

        f.compute(inputs, outputs)
        f.compute_partials(inputs, outputs, partials)

        # Adjoint vector
        # psi = np.linalg.solve(partials['R', 'y'].T, partials['f', 'y'].T)
        psi = np.linalg.solve(partials['displacements', 'displacements'].T,
                              partials['compliance', 'displacements'])

        # df_dx1 = psi @ partials['R', 'x1']
        df_dx1 = psi @ partials['displacements', 'density']

        # Chain rule
        # dc_dx = partials['c', 'x1'] @ partials['x1', 'x']
        dc_dx = partials['avg_density',
                         'density'] @ partials['density', 'density_unfiltered']
        # df_dx = partials['f', 'x1'] @ partials['x1', 'x']
        df_dx = partials['compliance',
                         'density'] @ partials['density', 'density_unfiltered']
        # pR_px = partials['R', 'x1'] @ partials['x1', 'x']
        pR_px = partials['displacements',
                         'density'] @ partials['density', 'density_unfiltered']

        return f, df_dx, c, dc_dx, psi, pR_px
