import setuptools

# Set version number
release = '3.2.10'

# Save version to version.txt
with open('version.txt','w') as newfile:
    newfile.write(release)

with open("README.md", "r") as fh:
    long_description = fh.read()

# Save proversion to version.txt
with open('version.txt','w') as newfile:
    newfile.write(release)

setuptools.setup(
  name = 'fredpy',
  packages = ['fredpy'],
  version = release,
  description = 'A package for downloading and working with data from Federal Reserve Economic Data',
  author = 'Brian C. Jenkins',
  author_email = 'bcjenkin@uci.edu',
  url = 'https://github.com/letsgoexploring/fredpy-package',
  # download_url = '',
  keywords = ['fred', 'economics','data','federal reserve'],
  classifiers = [],
  license_file="LICENSE",
)