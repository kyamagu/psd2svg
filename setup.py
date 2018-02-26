#!/usr/bin/env python
from setuptools import setup
import os
import sys


def get_version():
    curdir = os.path.dirname(__file__)
    filename = os.path.join(curdir, 'src', 'psd2svg', 'version.py')
    with open(filename, 'rb') as fp:
        return fp.read().decode('utf8').split('=')[1].strip(" \n'")


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='psd2svg',
    version=get_version(),
    description='Convert PSD file to SVG file',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
    ],
    keywords='photoshop psd svg',
    url='https://github.com/kyamagu/psd2svg',
    author='Kota Yamaguchi',
    author_email='KotaYamaguchi1984@gmail.com',
    license='MIT License',
    package_dir={'': 'src'},
    packages=[
        'psd2svg',
        'psd2svg.converter',
        'psd2svg.utils',
        'psd2svg.rasterizer'
    ],
    install_requires=[
        'pillow',
        'svgwrite',
        'numpy',
        'psd-tools2>=1.7.3',
        'future',
    ],
    extras_require = {
        'hdfs': [
            'snakebite'],
        'kerberos': [
            'python-krbV',
            'sasl'],
        's3': [
            'boto3']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['psd2svg=psd2svg.__main__:main']
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    )
