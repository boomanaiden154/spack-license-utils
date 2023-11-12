"""Some utilities for the license collection infra."""

import json


def load_license_csv(license_csv_path):
  package_license_pairs = []
  with open(license_csv_path) as license_csv:
    package_license_lines = license_csv.readlines()
    for line in package_license_lines:
      package_license_pair = line.split(',')
      assert len(package_license_pair) == 2
      package_license_pair[1] = package_license_pair[1].strip()
      package_license_pairs.append(package_license_pair)
  return package_license_pairs


def write_license_csv(license_csv_path, package_licenses):
  with open(license_csv_path, 'w') as license_csv_file:
    for package_license in package_licenses:
      pkg_name, pkg_license = package_license
      license_csv_file.write(f'{pkg_name},{pkg_license}\n')


def upgrade_deprecated_spdx_id(spdx_id):
  if not spdx_id.startswith('deprecated'):
    # Nothing to do here
    return spdx_id
  match (spdx_id[11:]):
    case 'AGPL-3.0':
      return 'AGPL-3.0-only'
    case 'GFDL-1.3':
      return 'GFDL-1.3-only'
    case 'GPL-2.0':
      return 'GPL-2.0-only'
    case 'GPL-3.0':
      return 'GPL-3.0-only'
    case 'GPL-3.0+':
      return 'GPL-3.0-or-later'
    case 'LGPL-2.0':
      return 'LGPL-2.0-only'
    case 'LGPL-2.0+':
      return 'LGPL-2.0-or-later'
    case 'LGPL-2.1+':
      return 'LGPL-2.1-or-later'
    case 'LGPL-3.0':
      return 'LGPL-3.0-only'
    case 'LGPL-3.0+':
      return 'LGPL-3.0-or-later'
    case _:
      return 'UNKNOWN'


def get_license_list(license_file_path):
  license_list = {}
  with open(license_file_path) as license_list_file:
    licenses_json = json.load(license_list_file)
    for lic in licenses_json['licenses']:
      license_list[lic['licenseId']] = True
  return license_list


def validate_exception(exception_string):
  match (exception_string):
    case 'OpenSSL-Exception':
      return True
    case 'LLVM-exception':
      return True
  return False


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
    if 'WITH' in spdx_id:
      id_parts = spdx_id.split('WITH')
      spdx_id = id_parts[0].strip()
      exception = id_parts[1].strip()
      if not validate_exception(exception):
        return False
    if spdx_id == 'custom':
      continue
    elif spdx_id == 'Public-Domain':
      continue
    if spdx_id not in license_map:
      return False

  return True
