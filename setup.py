from os import path

from setuptools import setup, find_packages

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='odoo_modules_newbiiz',
    version='1.0.1',
    author='ZOOU Qinn',
    author_email='qinn.zou@newbiiz.com',
    description='Odoo Modules from Newbiiz',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='http://www.newbiiz.com',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    install_requires=[],
    python_requires='>=3',
    packages=find_packages(),
)
