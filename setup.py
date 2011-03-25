from setuptools import setup, find_packages
import os

version = '1.3dev'


setup(name='zeam.form.silva',
      version=version,
      description="Integration of the Grok-based form system into Silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='grok form framework silva',
      author='Sylvain Viollon',
      author_email='thefunny@gmail.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['zeam', 'zeam.form'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'js.jquery',
        'js.jqueryui',
        'gp.fileupload',
        'infrae.layout',
        'infrae.rest',
        'martian',
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
        'zeam.form.base',
        'zeam.form.composed',
        'zeam.form.table',
        'zeam.form.viewlet',
        'zeam.form.ztk',
        'zope.component',
        'zope.i18n',
        'zope.interface',
        'zope.schema',
        ],
      entry_points="""
      # -*- Entry points: -*-
      [zeam.form.components]
      file = zeam.form.silva.widgets.file:register
      cropping = zeam.form.silva.widgets.cropping:register
      [silva.ui.resources]
      smi = zeam.form.silva.form.smi:IFormSilvaUIResources
      """,
      )
