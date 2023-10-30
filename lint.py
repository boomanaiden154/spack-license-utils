"""This script takes a file as input and lints all the license IDs to make sure
that they are SPDX-standards conforming. Note that this does not fully validate
that SPDX expressions are valid.
"""

import logging

from absl import flags
from absl import app

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The input file to lint')
flags.DEFINE_string('license_json', 'licenses.json',
                    'The path to the licenses JSON file.')
flags.DEFINE_string(
    'output_file', None,
    'The (optional) output file to place all info that lints correctly.')

flags.mark_flag_as_required('input_file')


def validate_license(spdx_expression, license_map):
  spdx_expression = spdx_expression.replace('(', '').replace(')', '')
  removed_and_parts = [
      removed_and.strip() for removed_and in spdx_expression.split('AND')
  ]
  removed_or_parts = []

  for removed_and_part in removed_and_parts:
    removed_or_parts.extend(
        [removed_or.strip() for removed_or in removed_and_part.split('OR')])

  for spdx_id in removed_or_parts:
    if spdx_id == 'custom':
      continue
    if spdx_id not in license_map:
      return False

  return True


def main(_):
  package_licenses = utils.load_license_csv(FLAGS.input_file)

  license_map = utils.get_license_list(FLAGS.license_json)

  for package_license in package_licenses:
    if package_license[1] == 'UNKNOWN':
      continue
    if not validate_license(package_license[1], license_map):
      logging.warning(
          f'{package_license[0]} has invalid license string "{package_license[1]}"'
      )
      package_license[1] = 'UNKNOWN'

  if FLAGS.output_file:
    utils.write_license_csv(FLAGS.output_file, package_licenses)


if __name__ == '__main__':
  app.run(main)
