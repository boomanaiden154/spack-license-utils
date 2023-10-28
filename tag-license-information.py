"""A tool for tagging spack packages with collected license information"""

import logging
import os
import re

from absl import app
from absl import flags

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'spack_checkout', None,
    'The path to the spack checkout to update license information in')
flags.DEFINE_string('input_path', None,
                    'The input path to the license information CSV to use.')

flags.mark_flag_as_required('spack_checkout')
flags.mark_flag_as_required('input_path')


def main(_):
  license_pairs = utils.load_license_csv(FLAGS.input_path)
  for package_name, license in license_pairs:
    if license == 'UNKNOWN':
      continue
    print(package_name)
    package_file_path = os.path.join(
        FLAGS.spack_checkout,
        f'./var/spack/repos/builtin/packages/{package_name}/package.py')
    with open(package_file_path) as package_file:
      package_file_lines = package_file.readlines()
      line_index = 0
      to_insert_index = 0
      while line_index < len(package_file_lines):
        if package_file_lines[line_index].strip().startswith('version('):
          # Some of the version fields have (multiple) comments on them
          while package_file_lines[line_index - 1].strip().startswith('#'):
            line_index -= 1
          # Some of the version fields are packed directly between variables.
          # If that's the case, we need to create some space.
          if re.match(r'^.* = ', package_file_lines[line_index - 1].strip()):
            package_file_lines.insert(line_index, f'\n')
            line_index += 1
          # Some of the version fields are package directly under other
          # directives, particularly the maintainers directive. Again, we need
          # to create some space.
          if package_file_lines[line_index - 1].strip().startswith('maintainers('):
            package_file_lines.insert(line_index - 1, '\n')
          # Some of the version fields are under multiple layers of control
          # flow. If we detect this, just walk up to the top.
          while package_file_lines[line_index].startswith('     '):
            line_index -= 1
          assert(package_file_lines[line_index - 1].strip() == '')
          to_insert_index = line_index - 1
          break
        line_index += 1

    has_license = False

    for file_line in package_file_lines:
      if file_line.strip().startswith('license('):
        has_license = True
        break

    if has_license:
      continue

    license_string = f'    license("{license}")\n'

    if to_insert_index == len(package_file_lines):
      package_file_lines.append('\n')
      package_file_lines.append(license_string)
    else:
      package_file_lines.insert(to_insert_index + 1, license_string)
      package_file_lines.insert(to_insert_index + 2, f'\n')

    with open(package_file_path, 'w') as package_file:
      for line in package_file_lines:
        package_file.write(line)


if __name__ == '__main__':
  app.run(main)
