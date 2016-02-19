# Standard imports
import ConfigParser as __ConfigParser
import argparse as __argparse


# All configurable options, mapped to their default value
__CONFIG = {
    # Default configuration file name
    'cfg_file_name': 'Nano.cfg',
    # An absolute path to the root directory in which the database to interact with resides.
    'root_dir': None,
    # Number of bytes in each IndexBlock
    'index_block_size': 4096,
    # Maximum number of blocks a BlockCacheManager will store before writing to file
    'max_num_dirty_blocks': 10,
}

# A set of numeric configuration options
__NUMERIC_CONFIGS = {
    'index_block_size',
    'max_num_dirty_blocks',
}


def __loadFromConfigFile(fileName):
    """
    Attempts to load configuration options from the config file.

    Expects INI style formatting.
    """

    parser = __ConfigParser.RawConfigParser()
    parser.read(fileName)

    # Get the configuration options out of each section parsed by the parser
    cfgList = []
    for section in parser.sections():
        cfgList.extend(parser.items(section))

    # We need up convert the ini-style dash-delimited names to argparse backend, underscore-delimited names
    # Note that converting the list to a dictionary here takes care of any duplicates
    cfg =  {key.replace('-', '_'): val for key, val in cfgList}

    # Assert that all configuration options given are valid; otherwise raise an exception to alert the user
    for key in cfg:
        if key not in __CONFIG:
            raise EnvironmentError("%s is not a recognized configuration directive." % key)

    return cfg

def __loadFromCmdLine():
    """ Attempts to load configuration from the command line arguments. """

    # Command line argments
    parser = __argparse.ArgumentParser(description="Run NanoDB.")

    parser.add_argument('--cfg-file-name',
                        default=__CONFIG['cfg_file_name'],
                        help="Path to configuration file to read for config directives. (default: %(default)s)")
    parser.add_argument('--root-dir',
                        help="""Absolute path to the root directory in which the database to interact with resides.""")
    parser.add_argument('--index-block-size',
                        default=__CONFIG['index_block_size'],
                        help="Number of bytes in each IndexBlock. (default: %(default)s)")
    parser.add_argument('--max_num_dirty_blocks',
                        help="Maximum number of blocks that will be cached before writing to file. (default: %(default)s)")

    return [(k, v) for k, v in parser.parse_args().__dict__.items() if v is not None]

def loadConfiguration(parseCmdLine=True):
    # Default config options take the least precedence
    config = __CONFIG.copy()

    # Config-file config options take the next level of precedence
    config.update(__loadFromConfigFile(config['cfg_file_name']))

    # Command line options take the highest precedence
    if parseCmdLine:
        config.update(__loadFromCmdLine())

    # Ensure we have a value for each configuration option in __CONFIG
    for key, val in config.items():
        if val is None:
            raise Exception("%s is required." % key)

    # Type-check all numeric configuration options
    for confName in __CONFIG:
        if confName in __NUMERIC_CONFIGS:
            try:
                config[confName] = int(config[confName])
            except ValueError:
                raise Exception("Can't cast numeric configuration option %s; value: %s" % (confName, config[confName]))

    # Set the configuration on our global namespace
    for confName in __CONFIG:
        globals()[confName] = config[confName]

# By default, load configuration on import
loadConfiguration()
