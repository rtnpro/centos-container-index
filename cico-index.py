#!/usr/bin/python
import git
import os
import shutil
import subprocess
import tempfile
import warnings
import yaml


# TODO: Make this configurable elsewhere
jjb_defaults_file = 'configurator/project-defaults.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobname', 'git_url', 'ci_project', 'jobs']
duffy_keys = {}

# TODO: Pull this directly from duffy


def load_duffy_keys():
    """Load duffy keys"""
    with open('keystore.yml') as f:
        keys = yaml.load(f)
    return keys


class AttributeWarning(UserWarning):
    pass


def lint(data):
    for idx, block in enumerate(data):
        for section in block:
            if section != 'project':
                raise AttributeError(
                    "Sections of type other than project are not supported "
                    "at this time")

            for attr in block[section]:
                if attr in overwritten_attrs:
                    warnings.warn_explicit(
                        '{attr} will be overwritten!'.format(
                            **locals()), AttributeWarning, 'block', idx)

            for attr in required_attrs:
                if attr not in block[section]:
                    raise AttributeError(
                        "Required Attribute {attr} not found in "
                        "{block}!".format(**locals()))


def get_duffy_key(project):
    return duffy_keys[project]


def projectify(data, project, giturl):
    lint(data)

    for idx, block in enumerate(data):
        for section in block:
            block[section]['namespace'] = project
            block[section]['jobname'] = block[section]['name']
            block[section]['ci_project'] = project
            block[section]['git_url'] = giturl
            block[section]['jobs'] = ['ci.centos.org-rundotsh-job']

            if 'rundotshargs' not in block[section]:
                block[section]['rundotshargs'] = ''
            elif block[section]['rundotshargs'] is None:
                block[section]['rundotshargs'] = ''
    return data


def main(projects):
    for projectname in projects:
        print "{} {} {}".format("="*10, projectname, "="*10)

        for giturl in projects[projectname]:
            try:
                t = tempfile.mkdtemp()
                print "creating: {}".format(t)

                # clone the repo from the indx
                git.Repo.clone_from(giturl, t)

                # read in the ci defs from the yaml file in their project root
                with open(os.path.join(t, 'ci.centos.org.yaml')) as datafile:
                    data = yaml.load(datafile)

                generated_filename = os.path.join(
                    t,
                    'ci.centos.org_GENERATED.yaml'
                )

                # overwrite any attributes we care about see: projectify
                with open(generated_filename, 'w') as outfile:
                    yaml.dump(projectify(data, projectname, giturl), outfile)

                # run jenkins job builder
                myargs = ['jenkins-jobs',
                          '--ignore-cache',
                          'update',
                          ':'.join([jjb_defaults_file, generated_filename])
                          ]
                print myargs
                proc = subprocess.Popen(myargs,
                                        stdout=subprocess.PIPE)
                proc.communicate()
            finally:
                print "Removing {}".format(t)
                shutil.rmtree(t)


if __name__ == '__main__':
    with open('project-index.yaml') as projectfile:
        projects = yaml.load(projectfile)
        main(projects)
