# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['flameshow', 'flameshow.pprof_parser', 'flameshow.render']

package_data = \
{'': ['*']}

install_requires = \
['cffi>=1.15.1,<2.0.0',
 'click>=8.1.7,<9.0.0',
 'textual>=0.37.1,<0.38.0',
 'typing-extensions>=4.7.1,<5.0.0']

entry_points = \
{'console_scripts': ['flameshow = flameshow.main:main']}

setup_kwargs = {
    'name': 'flameshow',
    'version': '0.1.1',
    'description': '',
    'long_description': '',
    'author': 'laixintao',
    'author_email': 'laixintaoo@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.10,<4.0',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
