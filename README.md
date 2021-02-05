# LXDProfileGenerator
A simple python script to populate YAML profiles for LXD

# User guide
The script takes a YAML template as input, updates it using a YAML file (`-u UPDATE`), and outputs a YAML file (`-p PROFILE`).

Type `$python3 lxd_profile_generator.py -h` to get this short help :
```
usage: lxd_profile_generator.py [-h] [-u UPDATE] [-p PROFILE] [-c] [-V] [-s] template

Script to generate LXD profiles from templates

positional arguments:
  template              YAML template used to generate the profile

optional arguments:
  -h, --help            show this help message and exit
  -u UPDATE, --update UPDATE
                        YAML values applied to the template
  -p PROFILE, --profile PROFILE
                        YAML profile generated
  -c, --cloud-init      parse cloud-init data
  -V, --verbose         make script verbose
  -s, --skip-errors     skip errors
```

# Update rules
The script compares the template and the update dictionaries according to the following rules, which are applied recursively :
- dicts are compared to find matching keys :
  - keys missing in `template` are added using `update`values
  - keys present in both dicts lead to a recursive search
  - keys missing in `update` remain untouched
- `template` lists are extended by counterpart `update`lists
- other `template`values are updated by their `update` counterpart if their type is identical (None value match any value).

Cloud-init data dicts, which are stored as plain strings in LXD profile YAML, are also compared with `update` dict, but their top key (`data.<something>`) must be inserted in the top dict of `update`. The required comment `#cloud-config` is also added at the required place in the output YAML file.


# Dependencies
This script should run on python3.5 and later. However, it has only be tested on python3.9

The PyYAML module is required. Credits and documentation may be found at https://pyyaml.org. \
The module may be installed easily using pip : `python3 -m pip install pyyaml` \
A C backend can also be used to speed up PyYAML, but it is not mandatory and requires to modify `YAML_LOADER` and `YAML_DUMPER` constants in the script.


# License
This repository and its content are licensed under the EUPL-1.2-or-later.

Check https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
