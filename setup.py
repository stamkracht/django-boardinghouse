from setuptools import setup, find_packages
import boardinghouse

setup(
    name="django-boardinghouse",
    version=boardinghouse.__version__,
    description="Postgres schema support in django.",
    url="https://bitbucket.org/schinckel/django-boardinghouse",
    author="Matthew Schinckel",
    author_email="matt@schinckel.net",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'django',
        'sqlparse',
        'pytz',
        # 'psycopg2',  # or psycopg2cffi under pypy
        # 'django-braces', # if you use boardinghouse.contrib.demo under django < 1.9
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    test_suite='runtests.runtests',
)
