from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='reem',
    version='0.1.1',
    packages=['reem'],
    url='https://www.github.com/krishauser/reem',
    license='Apache 2.0',
    author='Trishul Nagenalli and Kris Hauser',
    author_email='hauser.kris@gmail.com',
    description='Redis Extendable Efficient Middleware',
    install_requires=[
        'rejson',
        'redis',
        'six',
        'numpy',
      ],
    long_description=long_description,
    long_description_content_type='text/markdown',
)
