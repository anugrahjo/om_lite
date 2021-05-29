from om_lite.core.component import Component


class ExplicitComponent(Component):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize()
        self.options.update(kwargs)

    def add_output(
        self,
        name,
        val=1.0,
        shape=None,
        units=None,
        res_units=None,
        desc='',
        lower=None,
        upper=None,
    ):
        return super().add_output(
            name,
            val=val,
            shape=shape,
            units=units,
            res_units=res_units,
            desc=desc,
            lower=lower,
            upper=upper,
        )

    # intentionally wrong to catch errors
    def compute(self, outputs):
        pass

    # intentionally wrong to catch errors
    def compute_partials(self, partials):
        pass
