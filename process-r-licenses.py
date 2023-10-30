"""This script pulls license information from CRAN and adds it to the CSV
containing package license mappings.
"""

import os
import logging

from absl import flags
from absl import app

from spack_license_utils import utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_file', None, 'The path to the input CSV file.')
flags.DEFINE_string('output_file', None, 'The path to the output file.')
flags.DEFINE_string(
    'r_licenses_file', None,
    'The path to the file containing license information from CRAN')

flags.mark_flag_as_required('input_file')
flags.mark_flag_as_required('output_file')
flags.mark_flag_as_required('r_licenses_file')


def canonicalize_license(license_text):
  match license_text:
    case "GPL (>= 2)" | "GPL" | "GPL (> 2)" | "GPL (>= 2.0)" | "GNU General Public License" | "GNU General Public License (>= 2)":
      return "GPL-2.0-or-later"
    case "GPL-3" | "GNU General Public License version 3":
      return "GPL-3.0-only"
    case "MIT + file LICENSE" | "MIT License + file LICENSE" | "MIT + file LICENCE":
      return "MIT"
    case "GPL-2" | "GPL (== 2)":
      return "GPL-2.0-only"
    case "GPL (>= 3)" | "GPL (>= 3.0)" | "GNU General Public License (>= 3)" | "GPL (> 3)" | "GPL (>= 3.0.0)":
      return "GPL-3.0-or-later"
    case "file LICENSE" | "file LICENCE":
      return "custom"
    case "LGPL (>= 2)" | "LGPL" | "LGPL (>= 2.0)" | "LGPL (>= 2":
      return "LGPL-2.0-or-later"
    case "Apache License (>= 2)" | "Apache License (>= 2.0)":
      return "Apache-2.0+"
    case "Apache License (== 2)" | "Apache License Version 2.0":
      return "Apache-2.0"
    case "EUPL":
      return "EUPL-1.2"
    case "Apache License":
      return "Apache-1.1+"
    case "CC BY-NC 4.0":
      return "CC-BY-NC-4.0"
    case "LGPL (>= 2.1)":
      return "LGPL-2.1-or-later"
    case "LGPL (>= 3)" | "LGPL (>= 3.0)":
      return "LGPL-3.0-or-later"
    case "BSD_3_clause + file LICENSE" | "BSD 3-clause License + file LICENSE" | "BSD_3_clause + file LICENCE":
      return "BSD-3-Clause"
    case "BSD_2_clause + file LICENSE" | "BSD 2-clause License + file LICENSE" | "BSD_2_clause + file LICENCE":
      return "BSD-2-Clause"
    case "Apache License (== 2.0)" | "Apache License 2.0":
      return "Apache-2.0"
    case "AGPL-3" | "AGPL-3 + file LICENSE":
      return "AGPL-3.0-only"
    case "CC0":
      return "CC0-1.0"
    case "Creative Commons Attribution 4.0 International License" | "CC BY 4.0":
      return "CC-BY-4.0"
    case "CC BY-NC-SA 4.0":
      return "CC-BY-NC-SA-4.0"
    case "ACM":
      # This is the ACM license which isn't recognized by SPDX currently.
      # In addition, this license isn't used very commonly.
      return "custom"
    case "Unlimited":
      # This seems to be a license specifically to CRAN for distribution.
      # also not recognized by SPDX, and the specific terms are unclear.
      return "custom"
    case "CC BY-SA 4.0" | "CC BY-SA 4.0 + file LICENSE":
      return "CC-BY-SA-4.0"
    case "AGPL (>= 3)":
      return "AGPL-3.0-or-later"
    case "CeCILL-2":
      return "CECILL-2.0"
    case "CeCILL (>= 2)":
      return "CECILL-2.0+"
    case "CECILL-2.1":
      return "CECILL-2.1"
    case "LGPL-3" | "LGPL-3 + file LICENSE":
      return "LGPL-3.0-only"
    case "Artistic-2.0" | "Artistic License 2.0":
      return "Artistic-2.0"
    case "LGPL-2.1":
      return "LGPL-2.1-only"
    case "MPL":
      return "MPL-1.0+"
    case "BSL-1.0" | "BSL":
      return "BSL-1.0"
    case "LGPL-2":
      return "LGPL-2.0-only"
    case "AGPL" | "AGPL + file LICENSE":
      return "AGPL-1.0-or-later"
    case "FreeBSD":
      return "BSD-2-Clause"
    case "EUPL (>= 1.2)":
      return "EUPL-1.2+"
    case "GPL (>= 2.15.1)" | "GPL (>= 2.10)" | "GPL (>= 2.1)":
      # Seems like this is a typo somewhere
      return "GPL-2.0-or-later"
    case "GPL (>= 3.2)" | "GPL (>= 3.3.2)" | "GPL (>= 3.5.0)":
      # Also seems like this is a typo
      return "GPL-3.0-or-later"
    case "GPL (<= 2)" | "GPL (<= 2.0)":
      # Another seeming to be typo...
      return "GPL-2.0-only"
    case "Mozilla Public License 2.0" | "MPL-2.0" | "MPL-2.0" | "MPL (== 2.0)" | "Mozilla Public License Version 2.0":
      return "MPL-2.0"
    case "CeCILL":
      return "CeCILL-2.0+"
    case "GPL-3 + file LICENSE":
      return "GPL-3.0-only"
    case "GNU General Public License version 2":
      return "GPL-2.0-only"
    case "EPL":
      return "EPL-1.0"
    case "MPL (>= 2)" | "MPL (>= 2.0)":
      return "MPL-2.0+"
    case "EUPL-1.1":
      return "EUPL-1.1"
    case "MPL-1.1" | "Mozilla Public License 1.1":
      return "MPL-1.1"
    case "Common Public License Version 1.0" | "CPL-1.0":
      return "CPL-1.0"
    case "Lucent Public License":
      return "LPL-1.02"
    case "GNU Lesser General Public License":
      return "LGPL-2.1-or-later"
    case "CPL (>= 2)":
      # Seems to be a typo, there is no CPL-2.0
      return "CPL-1.0+"
    case _:
      return "unrecognized"


def canonicalize_license_expression(license_expression):
  license_parts = license_expression.split('|')
  canon_license_parts = [
      canonicalize_license(license_part.strip())
      for license_part in license_parts
  ]
  license_expression = ""
  for index, canon_license_part in enumerate(canon_license_parts):
    if index == len(canon_license_parts) - 1:
      license_expression += canon_license_part
    else:
      license_expression += canon_license_part + " OR "
  return license_expression


def main(_):
  r_licenses = {}

  with open(FLAGS.r_licenses_file) as r_licenses_file:
    r_package_licenses = r_licenses_file.readlines()
    for r_package_license in r_package_licenses[1:]:
      package_license_parts = r_package_license.split(',')
      license_text = package_license_parts[2][1:-2]
      r_licenses[license_text] = canonicalize_license_expression(license_text)

  for r_license in r_licenses:
    print(f'{r_license},{r_licenses[r_license]}')


if __name__ == '__main__':
  app.run(main)
