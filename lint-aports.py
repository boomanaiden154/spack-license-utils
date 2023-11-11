"""This script looks specifically at alpine/aports and lints the SPDX
identifiers contained within the repository to improve the license
information available from there."""

import logging
import os

from absl import flags
from absl import app

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('license_json', 'licenses.json', 'The path to the licenses JSON file.')
flags.DEFINE_string('aports_dir', None, 'The path to the aports clone')

flags.mark_flag_as_required('aports_dir')

def get_package_list(aports_dir):
  packages = []
  for main_package in os.listdir(os.path.join(aports_dir, 'main')):
    if main_package == '.rootbld-repositories':
      continue
    packages.append(('main', main_package))
  for community_package in os.listdir(os.path.join(aports_dir, 'community')):
    if main_package == '.rootbld-repositories':
      continue
    packages.append(('community', community_package))
  for testing_package in os.listdir(os.path.join(aports_dir, 'testing')):
    if main_package == '.rootbld-repositories':
      continue
    packages.append(('testing', testing_package))
  return packages

def get_license(package_name, package_repository):
  # This assums that the package exists
  apkbuild_path = os.path.join(FLAGS.aports_dir, package_repository,
                               package_name, 'APKBUILD')
  with open(apkbuild_path) as apkbuild_file:
    apk_lines = apkbuild_file.readlines()
    for line in apk_lines:
      if line.startswith('license='):
        line_parts = line.split('"')
        if len(line_parts) < 2:
          # If we're reaching this path, it's probably because there aren't
          # any quotes around the license string
          return line[8:-1]
        return line_parts[1]


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
  packages = get_package_list(FLAGS.aports_dir)

  license_map = utils.get_license_list(FLAGS.license_json)

  for package in packages:
    license_value = get_license(package[1], package[0])
    license_valid = validate_license(license_value, license_map)
    if not license_valid:
      logging.info(f'{package[0]}/{package[1]} has potentially invalid license {license_value}')


if __name__ == '__main__':
  app.run(main)
