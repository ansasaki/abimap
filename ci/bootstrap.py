#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join

if __name__ == "__main__":
    base_path = dirname(dirname(abspath(__file__)))
    print("Project path: {0}".format(base_path))
    env_path = join(base_path, ".tox", "bootstrap")
    if sys.platform == "win32":
        bin_path = join(env_path, "Scripts")
    else:
        bin_path = join(env_path, "bin")
    if not exists(env_path):
        import subprocess

        print("Making bootstrap env in: {0} ...".format(env_path))
        try:
            subprocess.check_call(["virtualenv", env_path])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, "-m", "virtualenv", env_path])
        print("Installing `jinja2` and `matrix` into bootstrap environment...")
        subprocess.check_call([join(bin_path, "pip"), "install", "jinja2", "matrix"])
    activate = join(bin_path, "activate_this.py")
    # noinspection PyCompatibility
    exec(compile(open(activate, "rb").read(), activate, "exec"), dict(__file__=activate))

    import jinja2

    import matrix

    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(join(base_path, "ci", "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

    env_names = ""
#    for (alias, conf) in matrix.from_file(join(base_path, "setup.cfg")).items():
    m = matrix.from_file(join(base_path, "setup.cfg")).items()

    print(m)

#    python_versions = conf["python_versions"]
#    coverage_flags = conf["coverage_flags"]

    python_versions = (conf["python_versions"] for (_, conf) in m)
    coverage_flags = (conf["coverage_flags"] for (_, conf) in m)
    alias = (alias for (alias, _) in m)

    tox_environments = {}
    for (alias, conf) in m:
        python = conf["python_versions"]
        tox_environments[alias] = {
            "python": "python" + python if "py" not in python else python,
            "cover": "true" if "cover" in alias else "false"
        }

    env_names = '{%s}-{%s}' %(','.join(list(set(python_versions))),
    ','.join(list(set(coverage_flags))))

    print("env_names = %s" %(env_names))

for name in os.listdir(join("ci", "templates")):
    with open(join(base_path, name), "w") as fh:
        fh.write(jinja.get_template(name).render(tox_environments=tox_environments,
        env_names = env_names))
    print("Wrote {}".format(name))
print("DONE.")
