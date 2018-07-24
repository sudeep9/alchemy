
import inspect
import importlib

UNIT_TYPE_SIMPLE = 1
UNIT_TYPE_META = 2
UNIT_TYPE_DERIVED = 3

class Unit:
    def __init__(self):
        self.name = None
        self.unit_type = UNIT_TYPE_SIMPLE

class FunctionUnit(Unit):
    def __init__(self):
        Unit.__init__(self)
        self.module = None
        self.func = None
        self.args = None
        self.kargs = None
        self.input_desc = {}
        self.output = {}
    
    def get_args(self):
        return self.args
    
    def get_default_vars(self):
        if self.kargs is None:
            return None
        return self.kargs.keys()

    def get_spec(self):
        spec = {
            'input': {}, 'output': self.output, 'type': self.unit_type,
        }

        for arg in self.args:
            arg_info = {'def': '', 'desc': ''}
            try:
                if self.kargs:
                    arg_info['def'] = self.kargs[arg]
            except KeyError:
                pass

            try:
                if self.input_desc:
                    arg_info['desc'] = self.input_desc[arg]
            except KeyError:
                pass

            spec['input'][arg] = arg_info            

        return spec

        
class DerivedUnit(Unit):
    def __init__(self):
        Unit.__init__(self)
        self.name = None
        self.input = None
        self.output = None
        self.defaults = {}
        self.ui_list = None
        self.unit_type = UNIT_TYPE_DERIVED

    def get_args(self):
        if not self.defaults:
            return self.input

        args = [a for a in self.input if a not in self.defaults]
        return args

    def get_default_vars(self):
        if self.defaults is None:
            return []
        return self.defaults.keys()

    def get_spec(self):
        spec = {
            'input': {}, 'output': self.output, 'type': self.unit_type,
        }

        for arg in self.input:
            arg_info = {'def': '', 'desc': ''}
            try:
                if self.defaults:
                    arg_info['def'] = self.defaults[arg]
            except KeyError:
                pass

            try:
                if self.input:
                    arg_info['desc'] = self.input[arg]
            except KeyError:
                pass

            spec['input'][arg] = arg_info 

        return spec

class UnitInstance:
    def __init__(self, name, params):
        desc = None
        try:
            if params:
                desc = params['@desc']
                del params['@desc']
            else:
                params = {}
        except KeyError:
            pass

        self.name = name
        self.params = params
        self.desc = desc

    def to_dict(self):
        return {
            'name': self.name,
            'desc': self.desc,
            'params': self.params,
        }

    def get_desc(self):
        if not self.desc:
            return self.name

        return self.desc

def create_derived_unit(name, input, output, defaults, ui_list):
    u = DerivedUnit()
    u.name = name
    u.input = input
    u.output = output
    u.ui_list = ui_list
    u.defaults = defaults

    return u

def create_unit_inst_from_dict(d):
    name = d.keys()[0]
    params = d[name]
    return UnitInstance(name, params)

def create_derived_unit_from_dict(name, d):
    unit_input = d.get('input', None)
    unit_output = d.get('output', None)
    unit_defaults = d.get('defaults', {})

    ui_list = []
    for unit_info in d['units']:
        ui = create_unit_inst_from_dict(unit_info)
        ui_list.append(ui)

    u = create_derived_unit(name, unit_input, unit_output, unit_defaults, ui_list,)
    return u
        

def _get_pos_args(spec):
    if spec.defaults:
        karg_count = len(spec.defaults)
        return spec.args[:-karg_count]

    return spec.args

def _get_kargs(pos_args, spec):
    kargs = {}
    if spec.defaults:
        for i, v in enumerate(spec.defaults):
            kargs[spec.args[len(pos_args) + i]] = v

    return kargs

def _get_func_args(spec):
    pos_args = _get_pos_args(spec)
    kargs = _get_kargs(pos_args, spec)

    return (pos_args, kargs)

def _create(name, module, func):
    spec = inspect.getargspec(func)
    args, kargs = _get_func_args(spec)

    u = FunctionUnit()
    u.name = name
    u.module = module
    u.func = func
    u.args = args
    u.kargs = kargs

    return u

def create_unit_from_dict(name, module, d):
    func_name = d['func']
    f = getattr(module, func_name)
    u = _create(name, module, f)

    if 'input' in d:
        u.input_desc = d['input']
    if 'output' in d:
        u.output = d['output']
    return u

def create_unit(name, module, func_name):
    f = getattr(module, func_name)
    return _create(name, module, f)

def create_unit_by_str(name, module_name, func_name):
    m = importlib.import_module(module_name)
    return create_unit(name, m, func_name)

def mark_as_meta_unit(u):
    u.unit_type = 'meta'

def is_meta_unit(u):
    return u.unit_type == 'meta'

