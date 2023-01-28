from setuptools import setup
from os import path

base_dir = path.abspath(path.dirname(__file__))
with open(path.join(base_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sigils',
    version='0.1.1',
    description='Extract, resolve, replace and connect [SIGILS] embedded in text.',
    long_description=long_description,
    url='http://github.com/arthexis/sigils',
    download_url='https://github.com/arthexis/sigils/archive/v0.1.1.tar.gz',
    author='Rafael Jesus Guillén Osorio',
    author_email='arthexis@gmail.com',
    license='MIT',
    keywords=["UTILS", "SIGILS", "STRING", "TEXT"],
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
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    install_requires=[
        'lark-parser',
        'lru-dict'
    ],
    extras_require={  # Optional
        'dev': [
            'django',
            'pytest',
            'black',
            'pytest-cov',
        ]
    }
)
