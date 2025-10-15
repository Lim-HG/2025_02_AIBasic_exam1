from setuptools import setup, find_packages

setup(
    name='gradinglib',
    version='1.0.1', 
    packages=find_packages(),

    package_data={
        'gradinglib': [
            'answers.json', 
            '*.npy' 
        ]
    }, 
    description='Python assignment grading library',
    author='Lim Hyung Geun',
    author_email='mathlim@hoseo.cnehs.kr',
    include_package_data=True 
)
