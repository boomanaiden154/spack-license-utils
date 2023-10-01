"""This script gets a list of spack packages and writes them to a CSV.
"""

import spack.repo
import spack.spec

from absl import flags
from absl import app

FLAGS = flags.FLAGS

flags.DEFINE_string('output_file', None, 'The path to the output CSV file')

flags.mark_flag_as_required('output_file')


def main(_):
    packages = spack.repo.all_package_names(include_virtuals=False)

    with open(FLAGS.output_file, 'w') as output_file:
        for package in packages:
            pkg_class = spack.repo.PATH.get_pkg_class(package)
            pkg = pkg_class(spack.spec.Spec(package))
            output_file.write(f'{pkg.name},UNKNOWN\n')


if __name__ == '__main__':
    app.run(main)
