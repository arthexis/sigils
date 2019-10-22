from setuptools import setup
from os import path

base_dir = path.abspath(path.dirname(__file__))
with open(path.join(base_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sigils',
    version='0.0.4',
    description='Extract, resolve and replace [SIGILS] embedded in text.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='http://github.com/arthexis/sigils',
    download_url='https://github.com/arthexis/sigils/archive/v0.0.4.tar.gz',
    author='Rafael Guillén',
    author_email='arthexis@gmail.com',
    license='MIT',
    keywords=["UTILS", "SIGIL", "STRING", "TEXT"],
    packages=['sigils'],
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=[
        'lark-parser',
    ],
    extras_require={
        'django': [
            'django',
        ],
        'dev': [
            'pytest',
            'black',
            'pytest-cov',
        ]
    }
)
