"""This script pulls license information on python packages from pypi.
"""

import logging
import requests
import json

from absl import flags
from absl import app

from bs4 import BeautifulSoup
from bs4 import SoupStrainer

from tqdm import tqdm

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The path to the input CSV file.')
flags.DEFINE_string('output_file', None, 'The path to the output CSV file.')
flags.DEFINE_string('license_json', 'licenses.json',
                    'The path to the license JSON file.')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')


def get_license_list():
  license_list = {}
  with open(FLAGS.license_json) as license_list_file:
    licenses_json = json.load(license_list_file)
    for lic in licenses_json['licenses']:
      license_list[lic['licenseId']] = True
  return license_list


def get_package_map():
  package_map = {}

  pypi_package_index = requests.get('https://pypi.org/simple')

  for package_link in BeautifulSoup(
      pypi_package_index.content,
      parse_only=SoupStrainer('a'),
      features="html.parser"):
    package_name = package_link.text
    package_map[package_name.upper()] = package_name

  return package_map


def get_license_info(package_name, license_list):
  api_endpoint = f'https://pypi.org/pypi/{package_name}/json'

  package_info_raw = requests.get(api_endpoint)

  package_info = json.loads(package_info_raw.content)

  if 'info' not in package_info or 'license' not in package_info['info']:
    return None

  license_string = package_info['info']['license']

  if license_string is None:
    return None

  license_string = license_string.replace(' ', '-')
  if license_string in license_list:
    return license_string

  return None


def main(_):
  license_list = get_license_list()

  package_licenses = utils.load_license_csv(FLAGS.input_file)

  logging.info('Grabbing package list from pypi.')
  package_map = get_package_map()
  logging.info(
      'Finished grabbing package list from pypi, tagging spack packages.')

  packages_with_license = 0
  packages_without_license = 0

  for package_license in tqdm(package_licenses, miniters=1):
    # Skip packages that already have license info
    if package_license[1] != 'UNKNOWN':
      continue
    # Skip non-python packages
    if not package_license[0].startswith('py-'):
      continue

    # We have a python package
    pypi_name = package_license[0][3:].upper()
    if pypi_name in package_map:
      pkg_license = get_license_info(package_map[pypi_name], license_list)
      if pkg_license:
        packages_with_license += 1
        package_license[1] = pkg_license
      else:
        packages_without_license += 1

  utils.write_license_csv(FLAGS.output_file, package_licenses)

  logging.info(
      f'Tagged {packages_with_license} packages with license information.')
  logging.info(
      f'Could not find (correctly formatted) license information for {packages_without_license} python packages.'
  )


if __name__ == '__main__':
  app.run(main)
