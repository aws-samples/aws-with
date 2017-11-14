from setuptools import setup
import sys
import aws_with

install_requires = [
    "boto3 >= 1.4.6",
    "pyyaml",
]

if sys.version_info[:2] < (2, 7):
    install_requires += [
        "argparse",
    ]

setup(
    name=aws_with.__title__,
    version=aws_with.__version__,
    description=aws_with.__summary__,
    long_description=open("README.rst").read(),
    license=aws_with.__license__,
    url=aws_with.__uri__,
    author=aws_with.__author__,
    author_email=aws_with.__email__,
    packages=["aws_with"],
    install_requires=install_requires,
    extras_require={},
    data_files = [("", ["LICENSE.txt"])],
    entry_points={'console_scripts': ['aws_with = aws_with.main:main']},
    classifiers=[
                    'Development Status :: 4 - Beta',
                    'Environment :: Console',
                    'Intended Audience :: Developers',
                    'Intended Audience :: End Users/Desktop',
                    'Intended Audience :: Information Technology',
                    'Intended Audience :: System Administrators',
                    'License :: OSI Approved :: Apache Software License',
                    'Operating System :: POSIX',
                    'Operating System :: Microsoft :: Windows',
                    'Operating System :: MacOS :: MacOS X',
                    'Topic :: System :: Systems Administration',
                    'Topic :: Utilities',
                    'Programming Language :: Python',
                    'Programming Language :: Python :: 2.6',
                    'Programming Language :: Python :: 2.7',
                    'Programming Language :: Python :: 3.4',
                    'Programming Language :: Python :: 3.5',
                    'Programming Language :: Python :: 3.6',
                    'Programming Language :: Python :: 3.7'
                ],

)
