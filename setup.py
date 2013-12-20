# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
from setuptools import setup, find_packages
import os

version = '2.0.5'

tests_require = [
    'zope.testing',
    'zeam.form.ztk [test]'
]

setup(name='zeam.form.silva',
      version=version,
      description="Integration of the Grok-based Zeam Form system into Silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='grok form framework silva',
      author='Sylvain Viollon',
      author_email='thefunny@gmail.com',
      url='https://github.com/silvacms/zeam.form.silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['zeam', 'zeam.form'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'infrae.fileupload',
        'grokcore.layout',
        'grokcore.security',
        'infrae.rest',
        'js.jquery',
        'js.jqueryui',
        'martian',
        'grokcore.chameleon',
        'megrok.pagetemplate',
        'setuptools',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.layout',
        'silva.core.messages',
        'silva.core.views',
        'silva.fanstatic',
        'silva.translations',
        'silva.ui',
        'zeam.component',
        'zeam.form.base',
        'zeam.form.composed',
        'zeam.form.table',
        'zeam.form.viewlet',
        'zeam.form.ztk [fanstatic]',
        'zope.configuration',
        'zope.component',
        'zope.interface',
        'zope.publisher',
        'zope.traversing',
        'zope.security',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require,},
      entry_points="""
      [zeam.form.components]
      file = zeam.form.silva.widgets.file:register
      cropping = zeam.form.silva.widgets.cropping:register
      id = zeam.form.silva.widgets.id:register
      [silva.ui.resources]
      smi = zeam.form.silva.form.smi:IFormSilvaUIResources
      """,
      )
