from setuptools import setup, find_packages

setup(
    name='scholastic',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
        # e.g., 'requests', 'numpy',
    ],
    author='Rich JAmes',
    author_email='github@richdutton.org.uk',
    description='Aggregate and dedupe Google Scholar emails'
)
