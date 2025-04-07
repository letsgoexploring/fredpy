import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'fredpy',
  packages = ['fredpy'],
  version = '3.2.9',
  description = 'A package for downloading and working with data from Federal Reserve Economic Data',
  author = 'Brian C. Jenkins',
  author_email = 'bcjenkin@uci.edu',
  url = 'https://github.com/letsgoexploring/fredpy-package',
  # download_url = '',
  keywords = ['fred', 'economics','data','federal reserve'],
  classifiers = [],
)