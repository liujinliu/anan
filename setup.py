# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def _setup():
    setup(
        name='cruiser',
        version='0.0.1',
        description='data collection from redis, then feeding to graphite',
        url='https://github.com/liujinliu/anan',
        install_requires=[],
        packages=find_packages('src'),
        package_dir={'': 'src'},
        classifiers=[
            'Development Status :: 4 - Beta Development Status',
            'Environment :: Console',
            'Topic :: Utilities',
        ],
    )


def main():
    _setup()


if __name__ == '__main__':
    main()
