"""Some utilities for the license collection infra."""


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
