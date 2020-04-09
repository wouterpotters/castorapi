from setuptools import setup
setup(
  name = 'castorapi',         # How you named your package folder (MyLib)
  packages = ['castorapi'],   # Chose the same as "name"
  version = '0.1.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Python API wrapper for Castor EDC to fetch data from you clinical study.',
  author = 'Wouter V. Potters',                   # Type in your name
  author_email = 'w.v.potters@amsterdamumc.nl',      # Type in your E-Mail
  url = 'https://github.com/wouterpotters/castorapi',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/wouterpotters/castorapi/archive/master.zip',    # I explain this later on
  keywords = ['Castor EDC', 'API', 'Castor','Clinical study','database','data science'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
            'io',
            'json',
            'os',
            'pandas',
            'requests',
            'progressbar',
            'logging'
      ],
  long_description=open('README.md').read(),
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3'      #Specify which pyhton versions that you want to support
  ],
)
