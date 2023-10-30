"""This script obtains license information by having spack stage the
application of interest and then analyzing the source using the go
license detector.
"""

import logging
import subprocess
import shutil
import json
import os

from absl import flags
from absl import app

import ray

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The path to the input CSV file.')
flags.DEFINE_string('output_file', None, 'The path to the output CSV file.')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')


def get_detected_license_from_dir(repo_dir):
  source_dir = os.path.join(repo_dir, 'spack-src')
  detector_command_line = ['license-detector', '-f', 'json', source_dir]
  try:
    license_detector_process = subprocess.run(
        detector_command_line, stdout=subprocess.PIPE, timeout=300)
  except subprocess.TimeoutExpired:
    logging.info('license-detector timeout expired')
    return 'NOASSERTION'
  if license_detector_process.returncode != 0:
    logging.info('license-detector failed')
    return 'NOASSERTION'
  license_info = json.loads(license_detector_process.stdout.decode('utf-8'))
  primary_project = license_info[0]
  if 'error' in primary_project:
    return 'NOASSERTION'
  licenses_matched = primary_project['matches']
  if licenses_matched[0]['confidence'] > 0.9:
    return licenses_matched[0]['license']
  return 'NOASSERTION'


def get_license_from_package_name(package_name):
  spack_stage_command = ['spack', 'stage', package_name]
  spack_stage_process = subprocess.run(
      spack_stage_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  if spack_stage_process.returncode != 0:
    return 'NOASSERTION'
  stdout_lines = spack_stage_process.stdout.decode('utf-8').split('\n')
  source_path = stdout_lines[-2].split(' ')[-1]
  license_string = get_detected_license_from_dir(source_path)

  shutil.rmtree(source_path)

  return license_string


@ray.remote(num_cpus=1)
def get_package_license_future(package_name):
  return (package_name, get_license_from_package_name(package_name))


def main(_):
  ray.init()

  package_licenses = utils.load_license_csv(FLAGS.input_file)

  license_detection_futures = []

  for package_license in package_licenses:
    if package_license[1] != 'UNKNOWN':
      continue
    license_detection_futures.append(
        get_package_license_future.remote(package_license[0]))

  detected_license_map = {}

  detected_licenses_count = 0
  failed_detection = 0

  while len(license_detection_futures) > 0:
    finished, license_detection_futures = ray.wait(
        license_detection_futures, timeout=5.0)
    detected_licenses = ray.get(finished)

    logging.info(
        f'Just finished {len(finished)} packages, {len(license_detection_futures)} remaining.'
    )

    for detected_license in detected_licenses:
      if detected_license[1] == 'NOASSERTION':
        failed_detection += 1
        continue
      detected_license_map[detected_license[0]] = detected_license[1]
      detected_licenses_count += 1

  for package_license in package_licenses:
    if package_license[0] in detected_license_map:
      license_to_use = detected_license_map[package_license[0]]
      package_license[1] = utils.upgrade_deprecated_spdx_id(license_to_use)

  utils.write_license_csv(FLAGS.output_file, package_licenses)

  logging.info(
      f'Found license information for {detected_licenses_count} packages')
  logging.info(
      f'Failed to find license information for {failed_detection} packages')


if __name__ == '__main__':
  app.run(main)
