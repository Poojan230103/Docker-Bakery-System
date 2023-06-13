import os
import json
import pymongo
import re

class treenode:
    def __init__(self, img_name):
        self._id = None
        self.img_name, self.tag = img_name.split(':')
        self.children = []
        self.parent = None
        self.sibling = None
        self.local_path = None
        self.repo_path = None
        self.components = []
        self.lastsyncedtime = None
        self.architecture = None
        self.files = []


class dependencies:
    def __init__(self, name):
        self.name = name
        self.local_path = None
        self.repo_path = None




script_path = '/Users/shahpoojandikeshkumar/Desktop/SI/repos/docker-bakery_repo1/component_repo1.sh'

import re


def parse_script(script_path):
    components = {}
    current_component = None

    with open(script_path, 'r') as script_file:
        for line in script_file:
            line = line.strip()

            # Check for component name
            component_match = re.match(r'(\S+)\)\s*$', line)
            if component_match:
                current_component = component_match.group(1)
                continue

            # Check for Dockerfile path
            dockerfile_match = re.match(r'DOCKERFILE_PATH=(.*?)\s*$', line)
            if dockerfile_match and current_component:
                dockerfile_path = dockerfile_match.group(1)
                components[current_component] = dockerfile_path
                current_component = None

    return components


components = parse_script(script_path)

# Print the component names and their associated Dockerfile paths
for component_name, dockerfile_path in components.items():
    print(f"Component: {component_name}")
    print(f"Dockerfile Path: {dockerfile_path}")
    print("-----------------------------")