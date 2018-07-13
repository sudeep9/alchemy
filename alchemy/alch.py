#!/usr/bin/env python 

import os, sys, argparse
import logging

log = None

EXENAME = os.path.basename(sys.argv[0])

CMDINFO = {
    'help': 'Print top level help',
    'cmd' : 'Prints the available commands',
    'check': 'Check integrity of the config file',
    'run' : 'Runs the flow',
    'list': 'List entities',
    'cfglist': 'Detect config files',
    'version': 'Show alchemy version',
}

def top_level_help():
    print "Usage: {0} <command> <command args>".format(EXENAME)
    print "See '{0} cmd' to see the available commands".format(EXENAME)

def version_cmd(args):
    import alchemy
    print alchemy.__version__

def cmd_cmd():
    print "Available commands:"
    for cmd, info in CMDINFO.iteritems():
        print "{0:10} {1}".format(cmd, info)

def check_cmd(args):
    if len(args) < 1:
        print "Error: not enough arguments"
        print "Usage: {0} check <config file>".format(EXENAME)
        sys.exit(1)

    cfgfile = args[0]

    import yaml
    from pprint import pprint
    with open(cfgfile) as f:
        y = yaml.load(f)
        pprint(y)


def get_registry(cfgfile):
    from alchemy import flow, registry, loader, executor

    if 'ALCH_CFG_PATH' in os.environ:
        cfgpath = os.environ['ALCH_CFG_PATH'].split(':')
    else:
        cfgpath = ['.']

    reg = loader.load_config(cfgfile, cfgpath = cfgpath)
    return reg
    

def run_cmd(args):
    if len(args) < 2:
        print "Error: not enough arguments"
        print "Usage: {0} run <config file> <flow name>".format(EXENAME)
        sys.exit(1)
    
    cfgfile, flow_name = args[0], args[1]
    log.info("Config file: %s", cfgfile)
    log.info("Flow name: %s", flow_name)

    from alchemy import registry, executor
    reg = get_registry(cfgfile)
    flow_inst = registry.get_flow(reg, flow_name)

    from threading import Thread
    from Queue import Queue

    progress_q = Queue()

    def print_names(pq):
        while True:
            name, event = pq.get()
            if name == '--end--':
                log.info("-- END --")
                break
            log.info("%s - %s", name, event)

    def notify(name, event):
        if event == 'start':
            print ">>", name
        progress_q.put((name, event))
        
    t = Thread(target = print_names, args=(progress_q,))
    t.start()

    try:
        executor.execute(reg, flow_inst, notify = notify)
    finally:
        progress_q.put(("--end--", None))


def list_units(cfgfile):
    reg = get_registry(cfgfile)

    for i, (name, u) in enumerate(reg.unit_map.iteritems()):
        doc = ""
        if u.func.__doc__:
            doc = u.func.__doc__
        print "{0:<3} {1:<20} {2}".format((i+1), name, doc)
        print "------------------------------------------"

def list_flows(cfgfile):
    reg = get_registry(cfgfile)

    for i, name in enumerate(reg.flow_map.keys()):
        print "{0:<2} {1}".format((i+1), name)

def list_cmd(args):
    if len(args) < 2:
        print "Error: not enough arguments"
        print "Usage: {0} list <entity> <config file>".format(EXENAME)
        print "     entity = unit | flow"
        sys.exit(1)
    
    entity, cfgfile = args[0], args[1]
    if entity == 'unit':
        list_units(cfgfile)
    elif entity == 'flow':
        list_flows(cfgfile)
    else:
        print "Error: unknown entity [%s]" % entity

def is_cfg_file(filepath):
    import yaml
    try:
        with open(filepath) as f:
            data = yaml.load(f)
            if 'alchemy' in data:
                return True
            return False
    except:
        return False
    
def cfglist_cmd(args):
    if 'ALCH_CFG_PATH' in os.environ:
        cfgpath = os.environ['ALCH_CFG_PATH'].split(':')
    else:
        cfgpath = ['.']

    for dirpath in cfgpath:
        for filename in os.listdir(dirpath):
            fullpath = os.path.join(dirpath, filename)
            if filename.endswith('.yml') and is_cfg_file(fullpath):
                print fullpath
                
        

def dispatch_cmd(cmd, args):
    if cmd == 'help':
        top_level_help()
    elif cmd == 'cmd':
        cmd_cmd()
    elif cmd == 'check':
        check_cmd(args)
    elif cmd == 'run':
        run_cmd(args)
    elif cmd == 'list':
        list_cmd(args)
    elif cmd == 'cfglist':
        cfglist_cmd(args)
    elif cmd == 'version':
        version_cmd(args)
    else:
        print "Error: unknown command [{0}]".format(cmd)
        top_level_help()
        sys.exit(1)

def setup_logging():
    global log
    log = logging.getLogger()

    handler = logging.FileHandler('alch.log', mode='w')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

def run():
    cmd, args = sys.argv[1], sys.argv[2:]

    setup_logging()
    log.info("Logging setup done")
    dispatch_cmd(cmd, args)


if __name__ == '__main__':
    if len(sys.argv[1:]) < 1:
        print "Error: not enough arguments"
        top_level_help()
        sys.exit(1)

    run()


    