"""This script pulls license information from Alpine Linux and adds it to
the CSV containing package license mappings.
"""

import os
import logging

from absl import flags
from absl import app

from spack_license_utils import utils
from spack_license_utils import alpine

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The path to the input CSV file.')
flags.DEFINE_string('aports_dir', None, 'The path to the aports clone.')
flags.DEFINE_string('output_file', None, 'The path to the output file.')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('aports_dir')
flags.mark_flag_as_required('output_file')


def get_repository(package_name):
  # Check the three repositories (main,community,testing)
  if os.path.exists(os.path.join(FLAGS.aports_dir, 'main', package_name)):
    return 'main'
  elif os.path.exists(
      os.path.join(FLAGS.aports_dir, 'community', package_name)):
    return 'community'
  elif os.path.exists(os.path.join(FLAGS.aports_dir, 'testing', package_name)):
    return 'testing'
  return None


def main(_):
  package_licenses = utils.load_license_csv(FLAGS.input_file)

  has_license_count = 0
  no_license_count = 0

  for package_license in package_licenses:
    # Skip util-linux as the license field in Alpine is three lines long
    # which would massively complicate parsing.
    if package_license[0] == 'util-linux':
      continue
    # Skip packages that already have license info
    if package_license[1] != 'UNKNOWN':
      continue
    repository = get_repository(package_license[0])
    if repository:
      # We found a package that exists
      pkg_license = alpine.get_license(package_license[0], repository,
                                       FLAGS.aports_dir)
      package_license[1] = pkg_license
      has_license_count += 1
    else:
      no_license_count += 1

  utils.write_license_csv(FLAGS.output_file, package_licenses)

  logging.info(f'Found license information for {has_license_count} packages')
  logging.info(
      f'Was unable to find license information for {no_license_count} packages')


if __name__ == '__main__':
  app.run(main)
