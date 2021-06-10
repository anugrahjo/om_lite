from om_lite.core.explicitcomponent import ExplicitComponent
import numpy as np


class IndepVarComp(ExplicitComponent):
    def __init__(self, name=None, val=1.0, **kwargs):
        super().__init__(**kwargs)

    def initialize(self):
        pass

    # def add_output(self,
    #                name,
    #                val=1.0,
    #                shape=None,
    #                units=None,
    #                res_units=None,
    #                desc='',
    #                lower=None,
    #                upper=None,
    #                ref=None,
    #                ref0=None,
    #                res_ref=None,
    #                tags=None,
    #                shape_by_conn=False,
    #                copy_shape=None,
    #                distributed=None):
    #     return super().add_output(
    #         name,
    #         val=val,
    #         shape=shape,
    #         units=units,
    #         res_units=res_units,
    #         desc=desc,
    #         lower=lower,
    #         upper=upper,
    #     )