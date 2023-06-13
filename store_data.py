import datetime
import os
import json
import pymongo
import re
import datetime


class treenode:
    def __init__(self, img_name):
        self._id = None
        self.img_name, self.tag = img_name.split(':')
        self.children = []
        self.parent = None
        self.sibling = None
        self.local_path = None
        self.repo_path = None
        self.git_repo_url = None
        self.lastupdatedtime = None
        self.componentname = None
        self.componentfile_local_path = None
        self.componentfile_repo_path = None
        self.lastsyncedtime = str(datetime.datetime.now())
        self.architecture = None
        self.files = []


class dependencies:
    def __init__(self, name):
        self.name = name
        self.local_path = None
        self.repo_path = None

class component_details:
    def __init__(self,name):
        self.comp_name = name
        self.comp_local_path = None
        self.comp_repo_path = None


root_path = '/Users/shahpoojandikeshkumar/Desktop/SI/docker_files'
filelist = os.listdir(root_path)
# print(filelist)


if __name__ == "__main__":
    client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
    # print(client)
    db = client.get_database('myDB')
    records = db['Images']


name_to_id = {}
id_to_node = {}
name_to_last_tag = {}
cnt = 0


for folder in filelist:
    folder_path = root_path + '/' + folder
    if folder == '.DS_Store':
        continue
    files = os.listdir(folder_path)
    deps = []
    name = "dummy"
    for f in files:
        path = folder_path + '/' + f
        if f != '.DS_Store' and f != 'Dockerfile':
            new_dep = dependencies(f)
            new_dep.local_path = path
            deps.append(new_dep)        # adding dependencies
        elif f == 'Dockerfile':     # reading the docker file
            file = open(path, 'r')
            name = file.readline().split()[1]
            if name.find(':') == -1:
                name = name + ':1.0'
            if name not in name_to_id.keys():
                new_node = treenode(name)
                new_node._id = cnt
                name_to_id[name] = cnt
                id_to_node[cnt] = new_node
                cnt += 1

            id_to_node[name_to_id[name]].local_path = path
            parent = None

            for lines in file:
                if lines.startswith('FROM'):
                    parent = lines.split()[1]
                    if parent.find(':') == -1:
                        parent = parent + ':1.0'
                    if parent not in name_to_id:
                        par_node = treenode(parent)
                        par_node._id = cnt
                        name_to_id[parent] = cnt
                        id_to_node[cnt] = par_node
                        cnt += 1


            id_to_node[name_to_id[name]].parent = name_to_id[parent]    # storing the parent
            id_to_node[name_to_id[parent]].children.append(name_to_id[name])   # storing the child

            tmp_name = name.split(':')[0]  # storing the name so that we don't have to split it again & again
            if tmp_name in name_to_last_tag.keys():     # for child node
                prev_name = tmp_name + ':' + name_to_last_tag[tmp_name]
                id_to_node[name_to_id[prev_name]].sibling = name
            name_to_last_tag[tmp_name] = name.split(':')[1]

    id_to_node[name_to_id[name]].files.extend(deps)


root_id = name_to_id["base_img:1.0"]


data = []


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


def make_tree(node_id):
    queue = []
    queue.append(node_id)
    while len(queue):
        sz = len(queue)
        for i in range(sz):
            node = id_to_node[queue[0]]
            data.append(node)
            # print(node.img_name,)
            queue.pop(0)
            for j in node.children:
                queue.append(j)
        # print('\n')


# COMPONENT PART BEGINS HERE    ###########################


main_path = '/Users/shahpoojandikeshkumar/Desktop/SI/repos'     # contains list of repos
path_list = os.listdir(main_path)
# print(path_list)


for reponame in path_list:
    # print(repos)            # list of all repos
    if reponame != '.DS_Store':
        path_repo = main_path + '/' + reponame     # repo path
        for relpath, dirs, files in os.walk(path_repo):     # parsing one repo
            for file in files:
                if file.endswith('.sh'):
                    script_path = os.path.join(main_path, relpath, file)
                    # print(script_path)
                    components = parse_script(script_path)
                    for keys in components.keys():
                        idx = script_path.rfind('/')
                        currpath = script_path[:idx] + components[keys][1:]     # local path of dockerfile
                        name = 'docker-bakery-system/' + keys + ':1.0'
                        file = open(currpath, 'r')      # reading the dockerfile
                        if name not in name_to_id.keys():
                            new_node = treenode(name)
                            new_node._id = cnt
                            name_to_id[name] = cnt
                            id_to_node[cnt] = new_node
                            cnt += 1
                        id_to_node[name_to_id[name]].git_repo_url = f"Poojan230103/{reponame}"  # path of repository
                        id_to_node[name_to_id[name]].local_path = currpath
                        id_to_node[name_to_id[name]].repo_path = currpath.split(reponame)[1]   # this path is relative to the root path of repo.
                        id_to_node[name_to_id[name]].componentname = keys
                        id_to_node[name_to_id[name]].componentfile_local_path = script_path
                        # print(script_path)
                        id_to_node[name_to_id[name]].componentfile_repo_path = currpath.split(reponame)[1]   # this path is relative to the root path of repo.
                        parent = None
                        req_path = None
                        for lines in file:
                            if lines.startswith('FROM'):
                                parent = lines.split()[1]
                                if parent.find(':') == -1:
                                    parent = parent + ':1.0'
                            match = re.match(r'COPY\s+([^\s]+/requirements.txt)\s+\.', lines)
                            if match:
                                req_path = match.group(1)

                        if parent not in name_to_id:        # executing this block of code outside for loop to cover multi-stage docker build
                            par_node = treenode(parent)
                            par_node._id = cnt
                            name_to_id[parent] = cnt
                            id_to_node[cnt] = par_node
                            cnt += 1
                        id_to_node[name_to_id[name]].parent = name_to_id[parent]  # storing the parent
                        if req_path:            # this path is relative to the .sh file
                            new_dep = dependencies("requirements.txt")
                            idx = script_path.rfind('/')
                            req_currpath = script_path[:idx] + req_path[1:]     # requirements.txt local path
                            new_dep.local_path = req_currpath
                            new_dep.repo_path = req_currpath.split(reponame)[1]     # requirements.txt path relative to root path of the repo
                            id_to_node[name_to_id[name]].files.append(new_dep)
                        id_to_node[name_to_id[parent]].children.append(name_to_id[name])  # storing the child


                        tmp_name = name.split(':')[0]  # storing the name so that we don't have to split it again & again
                        if tmp_name in name_to_last_tag.keys():  # for child node
                            prev_name = tmp_name + ':' + name_to_last_tag[tmp_name]
                            id_to_node[name_to_id[prev_name]].sibling = name
                        name_to_last_tag[tmp_name] = name.split(':')[1]

                # id_to_node[name_to_id[name]].files.extend(deps)


make_tree(root_id)
id_to_node[root_id].parent = None


json_data = json.dumps(data, default=lambda o: o.__dict__, indent=4)
mongo_data = open('/Users/shahpoojandikeshkumar/Desktop/SI/virtual_project/mongodata.json', 'w')
mongo_data.write(json_data)
mongo_data.close()


with open('mongodata.json') as file:
    file_data = json.load(file)

records.insert_many(file_data)
# records.delete_many({})





