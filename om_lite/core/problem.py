from om_lite.core.options_dictionary import OptionsDictionary


class Problem(object):
    def __init__(self,
                 model=None,
                 driver=None,
                 comm=None,
                 name=None,
                 **options):

        if model is None:
            self.model = Group()
        elif isinstance(model, System):
            self.model = model
        else:
            raise TypeError(
                self.msginfo +
                ": The value provided for 'model' is not a valid System.")

        if driver is None:
            self.driver = Driver()
        elif isinstance(driver, Driver):
            self.driver = driver
        else:
            raise TypeError(
                self.msginfo +
                ": The value provided for 'driver' is not a valid Driver.")

        self.options = OptionsDictionary()

    def __getitem__(self, name):
        """
        Get an output/input variable.
        Parameters
        ----------
        name : str
            Promoted or relative variable name in the root system's namespace.
        Returns
        -------
        float or ndarray or any python object
            the requested output/input variable.
        """
        return self.get_val(name, get_remote=None)

    def get_val(self, name, units=None, indices=None, get_remote=False):
        """
        Get an output/input variable.
        Function is used if you want to specify display units.
        Parameters
        ----------
        name : str
            Promoted or relative variable name in the root system's namespace.
        units : str, optional
            Units to convert to before return.
        indices : int or list of ints or tuple of ints or int ndarray or Iterable or None, optional
            Indices or slice to return.
        get_remote : bool or None
            If True, retrieve the value even if it is on a remote process.  Note that if the
            variable is remote on ANY process, this function must be called on EVERY process
            in the Problem's MPI communicator.
            If False, only retrieve the value if it is on the current process, or only the part
            of the value that's on the current process for a distributed variable.
            If None and the variable is remote or distributed, a RuntimeError will be raised.
        Returns
        -------
        object
            The value of the requested output/input variable.
        """
        if self._metadata['setup_status'] == _SetupStatus.POST_SETUP:
            val = self._get_cached_val(name, get_remote=get_remote)
            if val is not _UNDEFINED:
                if indices is not None:
                    val = val[indices]
                if units is not None:
                    val = self.model.convert2units(name, val,
                                                   simplify_unit(units))
        else:
            val = self.model.get_val(name,
                                     units=units,
                                     indices=indices,
                                     get_remote=get_remote,
                                     from_src=True)

        if val is _UNDEFINED:
            if get_remote:
                raise KeyError('{}: Variable name "{}" not found.'.format(
                    self.msginfo, name))
            else:
                raise RuntimeError(
                    f"{self.model.msginfo}: Variable '{name}' is not local to "
                    f"rank {self.comm.rank}. You can retrieve values from "
                    "other processes using `get_val(<name>, get_remote=True)`."
                )

        return val

    def __setitem__(self, name, value):
        """
        Set an output/input variable.
        Parameters
        ----------
        name : str
            Promoted or relative variable name in the root system's namespace.
        value : float or ndarray or any python object
            value to set this variable to.
        """
        self.set_val(name, value)

    def set_val(self, name, value, units=None, indices=None):
        """
        Set an output/input variable.
        Function is used if you want to set a value using a different unit.
        Parameters
        ----------
        name : str
            Promoted or relative variable name in the root system's namespace.
        value : float or ndarray or list
            Value to set this variable to.
        units : str, optional
            Units that value is defined in.
        indices : int or list of ints or tuple of ints or int ndarray or Iterable or None, optional
            Indices or slice to set to specified value.
        """
        model = self.model
        if self._metadata is not None:
            conns = model._conn_global_abs_in2out
        else:
            raise RuntimeError(
                f"{self.msginfo}: '{name}' Cannot call set_val before setup.")

        all_meta = model._var_allprocs_abs2meta
        loc_meta = model._var_abs2meta
        n_proms = 0  # if nonzero, name given was promoted input name w/o a matching prom output

        try:
            ginputs = model._group_inputs
        except AttributeError:
            ginputs = {}  # could happen if top level system is not a Group

        abs_names = name2abs_names(model, name)
        if abs_names:
            n_proms = len(abs_names)  # for output this will never be > 1
            if n_proms > 1 and name in ginputs:
                abs_name = ginputs[name][0].get('use_tgt', abs_names[0])
            else:
                abs_name = abs_names[0]
        else:
            raise KeyError(f'{model.msginfo}: Variable "{name}" not found.')

        if abs_name in conns:
            src = conns[abs_name]
            if abs_name not in model._var_allprocs_discrete['input']:
                value = np.asarray(value)
                tmeta = all_meta['input'][abs_name]
                tunits = tmeta['units']
                sunits = all_meta['output'][src]['units']
                if abs_name in loc_meta['input']:
                    tlocmeta = loc_meta['input'][abs_name]
                else:
                    tlocmeta = None

                gunits = ginputs[name][0].get(
                    'units') if name in ginputs else None
                if n_proms > 1:  # promoted input name was used
                    if gunits is None:
                        tunit_list = [
                            all_meta['input'][n]['units'] for n in abs_names
                        ]
                        tu0 = tunit_list[0]
                        for tu in tunit_list:
                            if tu != tu0:
                                model._show_ambiguity_msg(
                                    name, ('units', ), abs_names)

                if units is None:
                    # avoids double unit conversion
                    if self._metadata['setup_status'] > _SetupStatus.POST_SETUP:
                        ivalue = value
                        if sunits is not None:
                            if gunits is not None and gunits != tunits:
                                value = model.convert_from_units(
                                    src, value, gunits)
                            else:
                                value = model.convert_from_units(
                                    src, value, tunits)
                else:
                    if gunits is None:
                        ivalue = model.convert_from_units(
                            abs_name, value, units)
                    else:
                        ivalue = model.convert_units(name, value, units,
                                                     gunits)
                    if self._metadata[
                            'setup_status'] == _SetupStatus.POST_SETUP:
                        value = ivalue
                    else:
                        value = model.convert_from_units(src, value, units)
        else:
            src = abs_name
            if units is not None:
                value = model.convert_from_units(abs_name, value, units)

        # Caching only needed if vectors aren't allocated yet.
        if self._metadata['setup_status'] == _SetupStatus.POST_SETUP:
            if indices is not None:
                self._get_cached_val(name)
                try:
                    if _is_slicer_op(indices):
                        self._initial_condition_cache[name] = value[indices]
                    else:
                        self._initial_condition_cache[name][indices] = value
                except IndexError:
                    self._initial_condition_cache[name][indices] = value
                except Exception as err:
                    raise RuntimeError(
                        f"Failed to set value of '{name}': {str(err)}.")
            else:
                self._initial_condition_cache[name] = value
        else:
            myrank = model.comm.rank

            if indices is None:
                indices = _full_slice

            if model._outputs._contains_abs(abs_name):
                model._outputs.set_var(abs_name, value, indices)
            elif abs_name in conns:  # input name given. Set value into output
                if model._outputs._contains_abs(src):  # src is local
                    if (model._outputs._abs_get_val(src).size == 0
                            and src.rsplit('.', 1)[0] == '_auto_ivc'
                            and all_meta['output'][src]['distributed']):
                        pass  # special case, auto_ivc dist var with 0 local size
                    elif tmeta['has_src_indices']:
                        if tlocmeta:  # target is local
                            src_indices = tlocmeta['src_indices']
                            flat = False
                            if name in model._var_prom2inds:
                                sshape, inds, flat = model._var_prom2inds[name]
                                if inds is not None:
                                    if _is_slicer_op(inds):
                                        inds = _slice_indices(
                                            inds, np.prod(sshape), sshape)
                                        flat = True
                                src_indices = inds
                            if src_indices is None:
                                model._outputs.set_var(src, value, None, flat)
                            else:
                                if flat:
                                    src_indices = src_indices.ravel()
                                if tmeta['distributed']:
                                    ssizes = model._var_sizes['nonlinear'][
                                        'output']
                                    sidx = model._var_allprocs_abs2idx[
                                        'nonlinear'][src]
                                    ssize = ssizes[myrank, sidx]
                                    start = np.sum(ssizes[:myrank, sidx])
                                    end = start + ssize
                                    if np.any(src_indices < start) or np.any(
                                            src_indices >= end):
                                        raise RuntimeError(
                                            f"{model.msginfo}: Can't set {name}: "
                                            "src_indices refer "
                                            "to out-of-process array entries.")
                                    if start > 0:
                                        src_indices = src_indices - start
                                model._outputs.set_var(src, value,
                                                       src_indices[indices],
                                                       flat)
                        else:
                            raise RuntimeError(
                                f"{model.msginfo}: Can't set {abs_name}: remote"
                                " connected inputs with src_indices currently not"
                                " supported.")
                    else:
                        value = np.asarray(value)
                        model._outputs.set_var(src, value, indices)
                elif src in model._discrete_outputs:
                    model._discrete_outputs[src] = value
                # also set the input
                # TODO: maybe remove this if inputs are removed from case recording
                if n_proms < 2:
                    if model._inputs._contains_abs(abs_name):
                        model._inputs.set_var(abs_name, ivalue, indices)
                    elif abs_name in model._discrete_inputs:
                        model._discrete_inputs[abs_name] = value
                    else:
                        # must be a remote var. so, just do nothing on this proc. We can't get here
                        # unless abs_name is found in connections, so the variable must exist.
                        if abs_name in model._var_allprocs_abs2meta:
                            print(
                                f"Variable '{name}' is remote on rank {self.comm.rank}.  "
                                "Local assignment ignored.")
            elif abs_name in model._discrete_outputs:
                model._discrete_outputs[abs_name] = value
            elif model._inputs._contains_abs(
                    abs_name):  # could happen if model is a component
                model._inputs.set_var(abs_name, value, indices)
            elif abs_name in model._discrete_inputs:  # could happen if model is a component
                model._discrete_inputs[abs_name] = value

    def run_model(self, case_prefix=None, reset_iter_counts=True):
        """
        Run the model by calling the root system's solve_nonlinear.
        Parameters
        ----------
        case_prefix : str or None
            Prefix to prepend to coordinates when recording.
        reset_iter_counts : bool
            If True and model has been run previously, reset all iteration counters.
        """
        if self._mode is None:
            raise RuntimeError(
                self.msginfo +
                ": The `setup` method must be called before `run_model`.")

        if case_prefix:
            if not isinstance(case_prefix, str):
                raise TypeError(
                    self.msginfo +
                    ": The 'case_prefix' argument should be a string.")
            self._recording_iter.prefix = case_prefix
        else:
            self._recording_iter.prefix = None

        if self.model.iter_count > 0 and reset_iter_counts:
            self.driver.iter_count = 0
            self.model._reset_iter_counts()

        self.final_setup()

        self._run_counter += 1
        record_model_options(self, self._run_counter)

        self.model._clear_iprint()
        self.model.run_solve_nonlinear()

    def run_driver(self, case_prefix=None, reset_iter_counts=True):
        """
        Run the driver on the model.
        Parameters
        ----------
        case_prefix : str or None
            Prefix to prepend to coordinates when recording.
        reset_iter_counts : bool
            If True and model has been run previously, reset all iteration counters.
        Returns
        -------
        boolean
            Failure flag; True if failed to converge, False is successful.
        """
        if self._mode is None:
            raise RuntimeError(
                self.msginfo +
                ": The `setup` method must be called before `run_driver`.")

        if case_prefix:
            if not isinstance(case_prefix, str):
                raise TypeError(
                    self.msginfo +
                    ": The 'case_prefix' argument should be a string.")
            self._recording_iter.prefix = case_prefix
        else:
            self._recording_iter.prefix = None

        if self.model.iter_count > 0 and reset_iter_counts:
            self.driver.iter_count = 0
            self.model._reset_iter_counts()

        self.final_setup()

        self._run_counter += 1
        record_model_options(self, self._run_counter)

        self.model._clear_iprint()
        return self.driver.run()

    def compute_jacvec_product(self):
        pass

    def setup(
        self,
        check=False,
        logger=None,
        mode='auto',
        force_alloc_complex=False,
        #   distributed_vector_class=PETScVector,
        # local_vector_class=DefaultVector,
        derivatives=True):

        # # PETScVector is required for MPI
        # if comm.size > 1:
        #     if PETScVector is None:
        #         raise ValueError(
        #             self.msginfo +
        #             ": Attempting to run in parallel under MPI but PETScVector "
        #             "could not be imported.")
        #     elif distributed_vector_class is not PETScVector:
        #         raise ValueError(
        #             "%s: The `distributed_vector_class` argument must be "
        #             "`PETScVector` when running in parallel under MPI but '%s' was "
        #             "specified." %
        #             (self.msginfo, distributed_vector_class.__name__))

        if mode not in ['fwd', 'rev', 'auto']:
            msg = "%s: Unsupported mode: '%s'. Use either 'fwd' or 'rev'." % (
                self.msginfo, mode)
            raise ValueError(msg)

        self._mode = self._orig_mode = mode

        model_comm = self.driver._setup_comm(comm)

        # this metadata will be shared by all Systems/Solvers in the system tree
        self._metadata = {
            'coloring_dir':
            self.options['coloring_dir'],  # directory for coloring files
            'recording_iter':
            _RecIteration(),  # manager of recorder iterations
            'local_vector_class': local_vector_class,
            'distributed_vector_class': distributed_vector_class,
            'solver_info': SolverInfo(),
            'use_derivatives': derivatives,
            'force_alloc_complex': force_alloc_complex,
            'vars_to_gather':
            {},  # vars that are remote somewhere. does not include distrib vars
            'prom2abs': {
                'input': {},
                'output': {}
            },  # includes ALL promotes including buried ones
            'static_mode': False,  # used to determine where various 'static'
            # and 'dynamic' data structures are stored.
            # Dynamic ones are added during System
            # setup/configure. They are wiped out and re-created during
            # each Problem setup.  Static ones are added outside of
            # Problem setup and they are never wiped out or re-created.
            'config_info':
            None,  # used during config to determine if additional updates required
            'parallel_groups':
            [],  # list of pathnames of parallel groups in this model (all procs)
            'setup_status': _SetupStatus.PRE_SETUP,
            'vec_names': None,  # names of all nonlinear and linear vectors
            'lin_vec_names': None,  # names of linear vectors
            'model_ref':
            weakref.ref(model),  # ref to the model (needed to get out-of-scope
            # src data for inputs)
        }
        model._setup(model_comm, mode, self._metadata)

        # set static mode back to True in all systems in this Problem
        self._metadata['static_mode'] = True

        # Cache all args for final setup.
        self._check = check
        self._logger = logger

        self._metadata['setup_status'] = _SetupStatus.POST_SETUP

        return self

    def check_partials(
            self,
            #    out_stream=_DEFAULT_OUT_STREAM,
            includes=None,
            excludes=None,
            compact_print=False,
            abs_err_tol=1e-6,
            rel_err_tol=1e-6,
            method='fd',
            step=None,
            form='forward',
            step_calc='abs',
            force_dense=True,
            show_only_incorrect=False):

        pass

    def compute_totals(self,
                       of=None,
                       wrt=None,
                       return_format='flat_dict',
                       debug_print=False,
                       driver_scaling=False,
                       use_abs_names=False,
                       get_remote=True):

        pass