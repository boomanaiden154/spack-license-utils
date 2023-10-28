"""A tool for tagging spack packages with collected license information"""

import logging
import os

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

directives = [
    'version(', 'conflicts(', 'depends_on(', 'extends(', 'maintainers(',
    'license(', 'provides(', 'patch(', 'variant(', 'resource(', 'build_system(',
    'requires('
]


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
        for directive in directives:
          if package_file_lines[line_index].strip().startswith(directive):
            while line_index < len(package_file_lines) and package_file_lines[
                line_index].strip() != '':
              line_index += 1
            to_insert_index = line_index
            break
        line_index += 1

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
