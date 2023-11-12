"""Utilities for working with the Alpine Linux aports repository.
"""

import os


def get_package_list(aports_dir):
  packages = []
  for main_package in os.listdir(os.path.join(aports_dir, 'main')):
    if main_package == '.rootbld-repositories':
      continue
    packages.append(('main', main_package))
  for community_package in os.listdir(os.path.join(aports_dir, 'community')):
    if community_package == '.rootbld-repositories':
      continue
    packages.append(('community', community_package))
  for testing_package in os.listdir(os.path.join(aports_dir, 'testing')):
    if testing_package == '.rootbld-repositories':
      continue
    packages.append(('testing', testing_package))
  return packages


def get_license(package_name, package_repository, aports_dir):
  # This assums that the package exists
  apkbuild_path = os.path.join(aports_dir, package_repository, package_name,
                               'APKBUILD')
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
