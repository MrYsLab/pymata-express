from setuptools import setup

with open('pypi_desc.md', "r") as f:
    long_description = f.read()

setup(
    name='pymata-express',
    version='1.17',
    packages=['pymata_express'],
    install_requires=['pyserial'],
    url='https://mryslab.github.io/pymata-express/',
    download_url='https://github.com/MrYsLab/pymata-express',
    license='GNU Affero General Public License v3 or later (AGPLv3+)',
    author='Alan Yorinks',
    author_email='MisterYsLab@gmail.com',
    description='A Python Protocol Abstraction Library For Arduino Firmata using Python asyncio',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['Firmata', 'Arduino', 'Protocol', 'Python', 'asyncio'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
        'Topic :: Education',
        'Topic :: Home Automation',
    ],
)

