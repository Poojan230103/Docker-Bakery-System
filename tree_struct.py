import os
import json
import pymongo

class treenode:
    def __init__(self, img_name):
        self._id = None
        self.img_name = img_name.split()[0]
        self.tag = None
        if len(img_name.split()) > 1:
            self.tag = img_name.split()[1]
        else:
            self.tag = "latest"
        self.children = []
        self.parent = None
        self.sibling = None
        self.local_path = None
        self.repo_path = None
        self.components = []
        self.lastsyncedtime = None
        self.architecture = None
        self.files = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)


class dependencies:
    def __init__(self, name):
        self.name = name
        self.local_path = None
        self.repo_path = None





root_path = '/Users/shahpoojandikeshkumar/Desktop/SI/docker_files'
filelist = os.listdir(root_path)


dictionary = {}

for currpath in filelist:

    if currpath != '.DS_Store':
        up_path = root_path + '/' + currpath
        files = os.listdir(up_path)
        deps = []
        name = 'dummy'
        for filename in files:
            path = up_path + '/' + filename
            new_dep = None
            if filename != '.DS_Store':
                new_dep = dependencies(filename)
                new_dep.local_path = path
                deps.append(new_dep)        # dockerfile too will be added in dependencies
            if filename == 'Dockerfile':
                deps.pop(len(deps)-1)  # to remove the Dockerfile from the dependencies
                f = open(path, 'r')
                name = f.readline().split()[1]      # as of now assuming no multistage docker build
                # also this name will be unique for all the images
                if name not in dictionary.keys():
                    dictionary[name] = treenode(name)


                parent = 'dummy'   # assigning parent to dummy to avoid error.

                for lines in f:
                    if lines.startswith('FROM'):
                        parent = lines.split()[1]

                dictionary[name].parent = parent
                dictionary[name].local_path = path
                if parent not in dictionary.keys():
                    dictionary[parent] = treenode(parent)
                # dictionary[parent].children.append(dictionary[name])
                dictionary[parent].children.append(name)

        dictionary[name].files.extend(deps)
        deps.clear()

data = []

def print_tree(node, cnt):

    queue = []
    queue.append(node)
    while len(queue):
        sz = len(queue)
        for i in range(sz):
            node = queue[0]
            node._id = cnt
            cnt += 1
            data.append(node)
            print(node.img_name,)
            queue.pop(0)
            for j in node.children:
                queue.append(dictionary[j])
        print('\n')


print_tree(dictionary['base_img'], 0)


tree_json = json.dumps(dictionary['base_img'].__dict__, default=lambda o: o.__dict__, indent=4)
json_data = json.dumps(data, default=lambda o: o.__dict__, indent=4)
tree_data = open('/Users/shahpoojandikeshkumar/Desktop/SI/virtual_project/treedata.json', 'w')
mongo_data = open('/Users/shahpoojandikeshkumar/Desktop/SI/virtual_project/mongodata.json', 'w')
tree_data.write(tree_json)
mongo_data.write(json_data)
tree_data.close()
mongo_data.close()


# json_data = json.dumps(dictionary['base_img'].files, default=lambda o: o.__dict__, indent=4)
# print(json_data)


# Connecting mongodb database

if __name__ == "__main__":
    client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
    # print(client)
    db = client.get_database('myDB')
    records = db['Images']

    with open('mongodata.json') as file:
        file_data = json.load(file)

    records.insert_many(file_data)
    # records.delete_many({})
