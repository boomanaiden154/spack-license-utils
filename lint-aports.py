"""This script looks specifically at alpine/aports and lints the SPDX
identifiers contained within the repository to improve the license
information available from there."""

import logging
import os

from absl import flags
from absl import app

from spack_license_utils import utils
from spack_license_utils import alpine

FLAGS = flags.FLAGS

flags.DEFINE_string('license_json', 'licenses.json',
                    'The path to the licenses JSON file.')
flags.DEFINE_string('aports_dir', None, 'The path to the aports clone')

flags.mark_flag_as_required('aports_dir')


def main(_):
  packages = alpine.get_package_list(FLAGS.aports_dir)

  license_map = utils.get_license_list(FLAGS.license_json)

  for package in packages:
    license_value = alpine.get_license(package[1], package[0], FLAGS.aports_dir)
    license_valid = utils.validate_license(license_value, license_map)
    if not license_valid:
      print(
          f'{package[0]}/{package[1]} has potentially invalid license {license_value}'
      )


if __name__ == '__main__':
  app.run(main)
