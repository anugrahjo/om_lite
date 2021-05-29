from om_lite.core.system import System


class Group(System):
    def __init__(self):
        super().__init__(**kwargs)

    def setup(self):
        pass

    def promotes(self,
                 subsys_name,
                 any=None,
                 inputs=None,
                 outputs=None,
                 src_indices=None,
                 flat_src_indices=None,
                 src_shape=None):
        pass

    def add_subsystem(self,
                      name,
                      subsys,
                      promotes=None,
                      promotes_inputs=None,
                      promotes_outputs=None,
                      min_procs=1,
                      max_procs=None,
                      proc_weight=1.0):
        self.name = subsys

    def connect(self,
                src_name,
                tgt_name,
                src_indices=None,
                flat_src_indices=None):
        pass
