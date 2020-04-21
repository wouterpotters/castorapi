from setuptools import setup
setup(
    name='castorapi',         # How you named your package folder (MyLib)
    packages=['castorapi'],   # Chose the same as "name"
    version='0.1.3',      # Start with a small number and increase it with every change you make
    # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    license='MIT',
    description='Python API wrapper for Castor EDC to fetch data from you clinical study.',
    author='Wouter V. Potters',                   # Type in your name
    author_email='w.v.potters@amsterdamumc.nl',      # Type in your E-Mail
    # Provide either the link to your github or to your website
    url='https://github.com/wouterpotters/castorapi',
    # I explain this later on
    download_url='https://github.com/wouterpotters/castorapi/archive/master.zip',
    keywords=['Castor EDC', 'API', 'Castor', 'Clinical study', 'database',
              'data science'],   # Keywords that define your package best
    install_requires=[            # I get to this in a second
        'pandas>=1.0',
        'requests>=2.23',
            'progressbar2>=3.5'
    ],
    long_description=open('README.md').read(),
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        # Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3'
    ],
)
