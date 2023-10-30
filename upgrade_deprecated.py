"""This script takes in a list of licenses and upgrades deprecated licenses
into standards-conforming SPDX identifiers.
"""

import logging

from absl import flags
from absl import app

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input file to process.')
flags.DEFINE_string('output_file', None,
                    'The path to place the output file at.')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')


def main(_):
  package_licenses = utils.load_license_csv(FLAGS.input_file)

  for package_license in package_licenses:
    package_license[1] = utils.upgrade_deprecated_spdx_id(package_license[1])

  utils.write_license_csv(FLAGS.output_file, package_licenses)


if __name__ == '__main__':
  app.run(main)
