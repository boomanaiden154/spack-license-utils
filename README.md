# Spack Licensing Utilities

This repository contains some utility scripts that process CSV files containing
spack package names and license information to help with some automation
for automatically tagging spack packages with license info.

## Usage

Start off by gathering the list of packages and their associated license
information from within Spack:

```shell
python3 ./get-packages.py --output_file=./packages.csv
```

The above command assumes that you have appended the necessary spack
directories to your `PYTHONPATH`. If you have not, you can also just run the
command swapping out `python3` for `spack` and it should work.

The CSV file `packages.csv` will be in a two column format with the name of
each package being in the first column and the SPDX string identifying the
license in the second column.

Next, you need to pull license information from one of the available sources:

### Alpine Linux Aports

Alpine Linux is a linux distribution that packages a varietey of different
software and keeps track of license information. There are a significant
number of packages that both Spack and Alpine Linux package. To gather
information from the Alpine Linux package repositories, run the following
command:

```shell
cd /path/to/thing
git clone https://github.com/alpinelinux/aports
cd /path/to/spack-license-utils
python3 ./alpine.py --aports_dir=/path/to/thing/aports --input_file=./packages.csv --output_file=./packages_alpine.csv
```

### PyPI

The Python package index has some license information available, although
a significant proportion of it is non-SPDX conforming. However, we can still
pull a large amount of information from the portion that is. Run the following
script to tag packages with license information from PyPI:

```shell
python3 ./pypi.py --input_file=/tmp/packages.csv --output_file=/tmp/packages_pypi.csv
```

