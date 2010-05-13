from setuptools import setup, find_packages
import os

version = '1.0'


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
      url='',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['zeam', 'zeam.form'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'martian',
        'megrok.pagetemplate',
        'setuptools',
        'zeam.form.base',
        'zeam.form.composed',
        'zeam.form.ztk',
        'zeam.form.layout',
        'zope.i18n',
        ],
      )
