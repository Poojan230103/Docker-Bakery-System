import os, copy
import json
import pymongo
from github import Github
from datetime import datetime
import pytz, time, requests


class treenode:
    def __init__(self, img_name):
        self._id = None
        self.img_name, self.tag = img_name.split(':')
        self.children = []
        self.parent = None
        self.sibling = None
        self.dockerfile_local_path = None
        self.dockerfile_repo_path = None
        self.repo_name = None
        self.created_time = self.last_updated_time = self.last_synced_time = str(datetime.now().replace(microsecond=0))
        self.component_name = None
        self.architecture = "arm" if "arm" in img_name else "intel"
        self.files = []


class dependencies:
    def __init__(self, name):
        self.name = name
        self.deps_local_path = None
        self.deps_repo_path = None


def convert_to_indian_time(utc_time_zone):
    india_timezone = pytz.timezone('Asia/Kolkata')
    india_time = pytz.utc.localize(utc_time_zone).astimezone(india_timezone)
    india_time = india_time.strftime('%Y-%m-%d %H:%M:%S')
    india_time = datetime.strptime(india_time, '%Y-%m-%d %H:%M:%S')       #  datetime object
    return india_time


root_path = '/Users/shahpoojandikeshkumar/Desktop/SI/repos'
client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('myDB')
records = db['Images']

repo_name = "docker-bakery_repo10"
component_name = "test-component1_repo10"
repo_url = f"Poojan230103/{repo_name}"       # to be taken from the config file
mygit = Github("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")
myrepo = mygit.get_repo(repo_url)
old_to_mirror = {}
next_id = records.count_documents({}) + 1


# create a new node
nodes_cursor = records.find({"repo_name": repo_name, "component_name": component_name})
nodes_list_cursor = list(nodes_cursor)
nodes_json_data = json.dumps(nodes_list_cursor, indent=4)
nodes_data = json.loads(nodes_json_data)

# finding the one which was created last
node = None
Time = datetime.min
Time = convert_to_indian_time(Time)
for img in nodes_data:
    time_t = datetime.strptime(img["created_time"], '%Y-%m-%d %H:%M:%S')
    if time_t > Time:
        node = img
        Time = time_t

# Now I have the node with the given repo_name, component_name and with the maximum value of the tag.


# traverse the old nodes children and create a new node and add them to the new node's children
def dfs(old_child_id, old_par_node, new_par_node):       # building the whole tree structure.
    old_child_node = records.find_one({"_id": old_child_id})
    new_child_node = copy.deepcopy(old_child_node)
    global next_id
    new_child_node["_id"] = next_id               # assigned id to the new child
    old_to_mirror[old_child_id] = new_child_node["_id"]
    next_id += 1
    # updating the dockerfile
    f = open(new_child_node["dockerfile_local_path"], 'r')
    content = f.readlines()
    line_num = -1, cnt = 0
    for line in content:
        if line.__contains__("FROM"):
            line_num = cnt
        cnt += 1
    if line_num != -1:
        content[line_num].replace(content[line_num].split()[1], (new_par_node["name"] + ':' + new_par_node["tag"]))
    f.close()
    f = open(new_child_node["dockerfile_local_path"], 'w')
    f.writelines(content)
    f.close()
    new_child_node["parent"] = new_par_node["_id"]             # assigned parent to the new child node
    new_par_node["children"].append(new_child_node["_id"])     # appending child to the new parent node
    old_tag = (old_child_node["tag"].split('.'))
    major, minor = int(old_tag[0]), int(old_tag[1])
    minor += 1
    new_child_node["tag"] = str(major) + '.' + str(minor)
    new_child_node["children"].clear()
    parameter = {
        "repo_name": new_child_node["repo_name"],
        "component_name": new_child_node["component_name"],
        "tag": new_child_node["tag"],
    }

    response = requests.post("http://127.0.0.1:9000/build", data=parameter)
    response = response.json()
    print(response)
    # polling every 10 seconds
    parameter = {"job_id": response["job_id"]}
    while True:
        response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
        response = response.json()
        if response["status"] == "Success" or response["status"] == "Failed":
            print(response["status"])
            break
        time.sleep(10)
    new_child_node["created_time"] = new_child_node["last_synced_time"] = new_child_node["last_updated_time"] = str(datetime.now().replace(microsecond=0))
    for child in old_child_node["children"]:
        dfs(child, old_child_node, new_child_node)

    if new_child_node["sibling"]:
        new_child_node["sibling"] = old_to_mirror[new_child_node["sibling"]]    # establishing parent child relation in new images
    records.insert_one(new_child_node)


# node --> the node with the highest tag

var = node["dockerfile_repo_path"]         # docker file
commits = myrepo.get_commits(path=var)
flag = False
utc_time = commits[0].commit.committer.date
t = convert_to_indian_time(utc_time)
last_sync_time = node["last_synced_time"]     # in string format
last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')     # in datetime format

if t > last_sync_time:
    flag = True

# check for requirements.txt
for dep in node["files"]:
    var = dep["deps_repo_path"]
    commits = myrepo.get_commits(path=var)
    utc_time = commits[0].commit.committer.date
    t = convert_to_indian_time(utc_time)
    last_sync_time = node["last_synced_time"]  # in string format
    last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')

    if t > last_sync_time:
        flag = True

if flag:
    os.system(f'''
        cd {root_path}/{repo_name}
        git pull origin
    ''')

# we now have the updated repo on our local machine
new_node = copy.deepcopy(node)
new_node["created_time"] = new_node["last_synced_time"] = new_node["last_updated_time"] = str(datetime.now().replace(microsecond=0))
new_node["_id"] = next_id
next_id += 1
old_to_mirror[node["_id"]] = new_node["_id"]
old_tag = (node["tag"].split('.'))
major, minor = int(old_tag[0]), int(old_tag[1])
minor += 1
new_node["tag"] = str(major) + '.' + str(minor)                 # updating the tag of the image

# building new docker image
parameter = {
                "repo_name": new_node["repo_name"],
                "component_name": new_node["component_name"],
                "tag": new_node["tag"],
            }
response = requests.post("http://127.0.0.1:9000/build", data=parameter)
response = response.json()
print(response)
# polling every 10 seconds
parameter = {"job_id": response["job_id"]}
while True:
    response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
    response = response.json()
    if response["status"] == "Success" or response["status"] == "Failed":
        print(response["status"])
        break
    time.sleep(10)

new_node["sibling"] = node["_id"]          # assigning sibling
parent_node = records.find_one({"_id": node["parent"]})
parent_node["children"].append(new_node["_id"])
new_node["parent"] = parent_node["_id"]
new_node["children"].clear()


# recursively building the children
for children in node["children"]:
    dfs(children, node, new_node)

records.insert_one(new_node)
records.replace_one({"_id": parent_node["_id"]}, parent_node)








