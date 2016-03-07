# container-index
A metadata host repo consumed in the http://ci.centos.org/ infrastructure
for building and delivering containers.

## Setup
- ``pip install -r requirements.txt``
- Configure ``/etc/jenkins_jobs/jenkins_jobs.ini`` to point to an accessible
jenkins instance

## Usage
- ``python cccp-index.py``
