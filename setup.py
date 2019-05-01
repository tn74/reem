from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='reem',
    version='v0.0.11',
    packages=['reem'],
    url='https://www.github.com/tn74/reem',
    license='Apache 2.0',
    author='Trishul Nagenalli',
    author_email='trishul.nagenalli@duke.edu',
    description='Redis Extendable Efficient Middleware',
    install_requires=[
        'rejson',
        'redis',
        'six',
        'numpy',
      ],
    long_description=long_description,
    long_description_content_type='text/markdown'
)
