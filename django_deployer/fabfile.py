# -*- coding: utf-8 -*-
import yaml
import os

from jinja2 import Environment, PackageLoader

from fabric.api import *
from fabric.colors import green, red, yellow


DEPLOY_YAML = os.path.join(os.getcwd(), 'deploy.yml')

template_env = Environment(loader=PackageLoader('django_deployer', 'paas_templates'))


#
# Tasks
#

def init():
    _green("We need to ask a few questions before we can deploy your Django app")
    pyversion = prompt("What version of Python does your app need?", default="Python 2.7")
    database = prompt("What database does your app use?", default="PostgreSQL")
    # TODO: identify the project dir based on where we find the settings.py or urls.py
    project_name = None
    while not project_name:
        project_name = prompt("What is your Django project's name?")
    django_settings = prompt("What is your Django settings module?", default="%s.settings" % project_name)
    requirements = prompt("Where is your requirements.txt file?", default="requirements.txt")

    _green("Tell us where your static files and uploaded media files are located")

    # TODO: get these values by reading the settings.py file
    static_url = prompt("What is your STATIC_URL?", default="/static/")
    media_url = prompt("What is your MEDIA_URL?", default="/media/")

    return {'pyversion': pyversion,
            'database': database,
            'project_name': project_name,
            'django_settings': django_settings,
            'requirements': requirements,
            'static_url': static_url,
            'media_url': media_url,
            }

def deploy(provider=None):
    site = init()

    if not provider:
        provider = prompt("Which provider would you like to deploy to?", default="stackato")

    _create_deploy_yaml(site, provider)
    _create_provider_configs()


#
# Helpers
#

def _create_deploy_yaml(site, provider):
    _green("Creating a deploy.yml with your app's deploy info...")
    site_yaml_dict = site
    site_yaml_dict['provider'] = provider
    file = _join(os.getcwd(), 'deploy.yml')
    if os.path.exists(file):
        _red("Detected an existing deploy.yml file.")
        overwrite = prompt("Overwrite your existing deploy.yml file?", default="No")
        if overwrite == "No":
            exit()

    _write_file(file, yaml.safe_dump(site_yaml_dict, default_flow_style=False))
    _green("Created %s" % file)

def _create_provider_configs():
    site = yaml.safe_load(_read_file(DEPLOY_YAML))
    provider = site['provider']

    yaml_template_name = os.path.join(provider, '%s.yml' % provider)
    _render_config('%s.yml' % provider, yaml_template_name, site)

    settings_template_name = os.path.join(provider, 'settings_%s.py' % provider)
    settings_path = site['django_settings'].replace('.', '/') + '_%s.py' % provider
    _render_config(settings_path, settings_template_name, site)

def _render_config(dest, template_name, template_args):
    """
    Renders and writes a template_name to a dest given some template_args.
    """
    template = template_env.get_template(template_name)
    contents = template.render(**template_args)
    _write_file(dest, contents)

#
# utils
#
 
def _write_file(path, contents):
    file = open(path, 'w')
    file.write(contents)
    file.close()

def _read_file(path):
    file = open(path, 'r')
    contents = file.read()
    file.close()
    return contents

def _join(*args):
    """Convenience wrapper around os.path.join to make the rest of our
    functions more readable."""
    return os.path.join(*args)


#
# Pretty colors
#

def _green(text):
    print green(text)

def _red(text):
    print red(text)

def _yellow(text):
    print yellow(text)