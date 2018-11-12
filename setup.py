"""Hue platform for MPF."""

from setuptools import setup

setup(

    name='mpf_hue_platform',
    version='1.0',
    description='Mission Pinball Framework External Platform',
    long_description='''Use Hue lights in MPF''',

    url='http://missionpinball.org',
    author='The Mission Pinball Framework Team',
    author_email='jab@missionpinball.org',
    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Topic :: Artistic Software',
        'Topic :: Games/Entertainment :: Arcade'

    ],

    keywords='pinball',

    include_package_data=True,

    # MANIFEST.in picks up the rest
    packages=['mpf_hue_platform'],

    install_requires=['mpf'],

    tests_require=[],

    entry_points='''
    [mpf.platforms]
    hue_platform=mpf_hue_platform.platform:HueHardwarePlatform
    '''
)
