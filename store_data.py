import os
import json
import pymongo

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



root_path = '/Users/shahpoojandikeshkumar/Desktop/SI/docker_files'
filelist = os.listdir(root_path)


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
                name = name + ':latest'
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
                        parent = parent + ':latest'
                    if parent not in name_to_id:
                        par_node = treenode(parent)
                        par_node._id = cnt
                        name_to_id[parent] = cnt
                        id_to_node[cnt] = par_node
                        cnt += 1

            id_to_node[name_to_id[name]].parent = name_to_id[parent]    # storing the parent
            id_to_node[name_to_id[parent]].children.append(name_to_id[name])   # storing the child

    id_to_node[name_to_id[name]].files.extend(deps)


root_id = name_to_id["base_img:latest"]


data = []


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






