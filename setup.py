# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 18:49:43 2019

@author: fakeles
""" 

""" $ python setup.py bdist_egg """

from setuptools import setup, find_packages

setup(
    name='tcmb',
    version='0.1.0',
    description='A data scraper for importing XML files from tcmb.gov.tr',
    long_description='I would just open("README.md").read() here',
    author='Fatih Keles',
    author_email='fatihkeles@gmail.com',
    url='https://github.com/fatih-keles/scrapy-tcmb',
    #packages=find_packages(exclude=['*tests*']),
    packages=find_packages(),
    entry_points={'scrapy': ['settings = tcmb.settings']},
)
