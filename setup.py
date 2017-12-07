from setuptools import setup

setup(
    name='mailextractor',
    version='0.1.0',
    author='Leif Denby',
    author_email='leif@denby.eu',
    description='CLI for IMAP mail extraction',
    long_description='',
    zip_safe=False,
    install_requires=['attrdict',],
    packages=["mailextractor"],
)
