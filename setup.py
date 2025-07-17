#!/usr/bin/env python

from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(name='product_management',
          packages=find_packages(where='src/main/python'),
          package_dir={'': 'src/main/python'},
          zip_safe=False)