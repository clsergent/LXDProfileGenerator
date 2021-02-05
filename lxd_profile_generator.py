#!/usr/bin/env python3

import os
import yaml
import argparse
import logging

CLOUD_INIT_KEYS = ['user.user-data', 'user.network-config', 'user.vendor-data', 'user.meta-data']
CLOUD_INIT_HEADER = "#cloud-config\n"

YAML_LOADER = yaml.Loader
YAML_DUMPER = yaml.Dumper
YAML_DUMPER_ARGS = dict(sort_keys=False, default_flow_style=False)


class PlainString(str):
    @staticmethod
    def presenter(dumper, plain_string):
        return dumper.represent_scalar('tag:yaml.org,2002:str', plain_string, style='|')

def presenterNone(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '[]')

#yaml.add_representer(type(None), presenterNone)
yaml.add_representer(PlainString, PlainString.presenter)


def loadData(source, skip_errors=False, data_name='data'):
    logging.info(f'loading {data_name}...')
    # source is a file
    if os.path.isfile(os.path.expanduser(source)):
        try:
            logging.info(f'loading {data_name} from{source} for YAML parsing')
            with open(source, mode='r', encoding='utf8', errors='skip') as file:
                data = yaml.load(file, Loader=YAML_LOADER)
                logging.info(f'{data_name} loaded from {source}')
                return data
        except (IOError, FileNotFoundError, yaml.YAMLError) as error:
            if skip_errors:
                logging.warning(f'{source} is not a valid YAML file, skipping')
                return None
            else:
                raise error
    # source is raw data
    else:
        try:
            return yaml.load(source, Loader=YAML_LOADER)
        except (ValueError, yaml.YAMLError) as error:
            if skip_errors:
                logging.warning(f'{data_name} is not valid YAML, skipping')
                return None
            else:
                raise error
        finally:
            logging.info(f'{data_name} loaded from raw')


def loadCloudInit(data, skip_errors=True):
    logging.info('parsing cloud-init data...')
    if 'config' in data.keys():
        for key, value in data['config'].items():
            if key in CLOUD_INIT_KEYS:
                data['config'][key] = loadData(value, skip_errors, data_name=key)
    logging.info('cloud-init data parsed')
    return data


def updateCloudInit(data: dict, update: dict) -> (dict, dict):
    if 'config' in data.keys():
        for key, value in data['config'].items():
            if key in CLOUD_INIT_KEYS and key in update:
                logging.info(f'updating cloud-init: {key}')
                data['config'][key] = updateData(data['config'][key], update[key])
                del update[key]
    return data, update


def updateData(data, update):
    if data is None:
        return update

    elif type(data) is not type(update):
        return data

    if type(data) is dict:
        for key, value in data.items():
            if key in update:
                data[key] = updateData(data[key], update[key])
        for key in update:
            if key not in data:
                data[key] = update[key]

    elif type(data) is list:
        data += update
    else:
        return update
    return data


def dumpCloudInit(data) -> dict:
    logging.info('dumping cloud-init data...')
    if 'config' in data.keys():
        for key, value in data['config'].items():
            if key in CLOUD_INIT_KEYS:
                logging.info(f'dumping {key}')
                data['config'][key] = PlainString(CLOUD_INIT_HEADER + yaml.dump(value,
                                                                                Dumper=YAML_DUMPER,
                                                                                **YAML_DUMPER_ARGS))
    logging.info('cloud-init data dumped')
    return data


def dumpData(data, destination='', skip_errors=False, data_name='data') -> None:
    logging.info(f'dumping {data_name}...')
    # to file
    if os.path.isdir(os.path.dirname(destination)):
        try:
            logging.info(f'writing {data_name} to {destination}')
            with open(destination, mode='w', encoding='utf8', errors='skip') as file:
                yaml.dump(data, file, Dumper=YAML_DUMPER, **YAML_DUMPER_ARGS)
                logging.info(f'{data_name} dumped to {destination}')
        except (IOError, FileNotFoundError, yaml.YAMLError) as error:
            if skip_errors:
                logging.warning(f'an error occurred while dumping {data_name} to {destination}: {error}')
            else:
                raise error
        finally:
            return
    # to stdout
    else:
        try:
            print(yaml.dump(data, Dumper=YAML_DUMPER, **YAML_DUMPER_ARGS))
        except (ValueError, yaml.YAMLError) as error:
            if skip_errors:
                logging.warning(f'{data_name} is not valid YAML, returning an empty dictionary')
                print('')
            else:
                raise error


def getArgs():
    parser = argparse.ArgumentParser(description='Script to generate LXD profiles from templates')
    parser.add_argument('template', type=str, help='YAML template used to generate the profile')
    parser.add_argument('-u', '--update', type=str, default='{}', help='YAML values applied to the template')
    parser.add_argument('-p', '--profile', type=str, default='', help='YAML profile generated')
    parser.add_argument('-c', '--cloud-init', action='store_true', default=False, help='parse cloud-init data')
    parser.add_argument('-V', '--verbose', action='store_true', default=False, help='make script verbose')
    parser.add_argument('-s', '--skip-errors', action='store_true', default=False, help='skip errors')

    return parser.parse_args()


def setVerbosity(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(message)s')


def run(args):
    setVerbosity(args)

    template = loadData(args.template, skip_errors=args.skip_errors, data_name='template')
    if args.cloud_init is True:
        template = loadCloudInit(template, skip_errors=args.skip_errors)

    update = loadData(args.update, skip_errors=args.skip_errors, data_name='update')
    if type(update) is not dict:
        logging.warning('values is not a valid dictionary, skipping')
        update = {}

    # print(f'template {template}')
    # print(f'values {values}')

    logging.info('updating template...')
    template, update = updateCloudInit(template, update)
    template = updateData(template, update)
    logging.info('template updated')

    if args.cloud_init is True:
        template = dumpCloudInit(template)

    dumpData(template, args.profile, skip_errors=args.skip_errors)


if __name__ == '__main__':
    args = getArgs()
    run(args)