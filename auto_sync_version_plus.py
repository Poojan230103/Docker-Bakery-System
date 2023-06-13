import os
import json
import pymongo
from github import Github
from datetime import datetime
import pytz

client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('myDB')
records = db['Images']
repo_url = "Poojan230103/docker-bakery_repo10"
mygit = Github("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")
myrepo = mygit.get_repo(repo_url)


def convert_to_indian_time(utc_time_zone):
    india_timezone = pytz.timezone('Asia/Kolkata')
    india_time = pytz.utc.localize(utc_time_zone).astimezone(india_timezone)
    india_time = india_time.strftime('%Y-%m-%d %H:%M:%S')
    india_time = datetime.strptime(india_time, '%Y-%m-%d %H:%M:%S')       #  datetime object
    return india_time


def dfs(node_id, old_par_name, new_par_name):         # recursively re-building the subtree on updation of the parent node

    childnode = records.find_one({"_id": node_id})

    # Parsing the docker file and updating the Parent node
    f_child = open(childnode["local_path"], 'r')
    f_contents = f_child.read()
    f_contents = f_contents.replace(old_par_name, new_par_name)
    f_child.close()
    f_child = open(childnode["local_path"], 'w')
    f_child.write(f_contents)
    f_child.close()
    new_tag = childnode["tag"]
    major, minor = int(new_tag.split('.')[0]), int(new_tag.split('.')[1])
    major += 1
    new_tag = str(major) + '.' + str(minor)

    if childnode["componentname"]:
        idx_child = childnode["componentfile_local_path"].rfind('/')
        dir_path_child = childnode["componentfile_local_path"][:idx_child]
        shell_file_name_child = childnode["componentfile_local_path"][idx_child + 1:]
        os.system(f'''
                cd {dir_path_child}
                pwd
                sh {shell_file_name_child} {childnode["componentname"]} {new_tag}
        ''')

    else:
        os.system(f'''
            cd {childnode["local_path"]} -t {childnode["img_name"]}:{new_tag} .
            docker build -t 
        ''')

    childnode["lastupdatedtime"] = str(datetime.now())
    for ids_child in childnode["children"]:
        old_parent = childnode["img_name"] + ":" + childnode["tag"]
        new_parent = childnode["img_name"] + ":" + new_tag
        dfs(ids_child, old_parent, new_parent)

    records.update_one(
        {"_id": childnode["_id"]}, {"$set": {"lastupdatedtime": str(datetime.now().replace(microsecond=0)),
                                              "lastsyncedtime": str(datetime.now().replace(microsecond=0)),
                                              "tag": new_tag}})
    return


# Below is the code to sync the specified repository. The repo may contain multiple Components, hence syncing each of them.

# extracting all the nodes built from this repository
nodes_cursor = records.find({"git_repo_url": repo_url})
nodes_list_cursor = list(nodes_cursor)
nodes_json_data = json.dumps(nodes_list_cursor, indent=4)
nodes_data = json.loads(nodes_json_data)

for node in nodes_data:
    # check for docker file
    var = node["repo_path"]   # docker file
    commits = myrepo.get_commits(path=var)
    flag = False

    utc_time = commits[0].commit.committer.date
    indian_time = convert_to_indian_time(utc_time)
    last_sync_time = node["lastsyncedtime"]   # in string format
    last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')

    if indian_time > last_sync_time:        # updating the dockerfile
        flag = True
        file_contents = myrepo.get_contents(path=node["repo_path"]).decoded_content.decode()
        f = open(node["local_path"], 'w')
        f.write(file_contents)
        f.close()

    # check for requirements.txt and other dependencies
    for dep in node["files"]:
        var = dep["repo_path"]
        commits = myrepo.get_commits(path=var)
        utc_time = commits[0].commit.committer.date
        indian_time = convert_to_indian_time(utc_time)
        last_sync_time = node["lastsyncedtime"]  # in string format
        last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')

        if indian_time > last_sync_time:
            flag = True             #updating the dependencies
            file_contents = myrepo.get_contents(path=var).decoded_content.decode()
            f = open(dep["local_path"], 'w')
            f.write(file_contents)
            f.close()

    # rebuilding the image
    if flag and node["componentname"]:
        new_tag = node["tag"]
        major, minor = int(new_tag.split('.')[0]), int(new_tag.split('.')[1])
        major += 1
        new_tag = str(major) + '.' + str(minor)
        idx = node["componentfile_local_path"].rfind('/')
        dir_path = node["componentfile_local_path"][:idx]

        shell_file_name = node["componentfile_local_path"][idx+1:]

        os.system(f'''
            cd {dir_path}
            pwd
            sh {shell_file_name} {node["componentname"]} {new_tag}
        ''')

        for ids in node["children"]:
            old_name = node["img_name"] + ':' + node["tag"]
            new_name = node["img_name"] + ':' + new_tag
            dfs(ids, old_name, new_name)
        records.update_one(
            {"_id": node["_id"]}, {"$set": {"lastupdatedtime": str(datetime.now().replace(microsecond=0)),
                                            "tag": new_tag}}
        )
    elif flag:
        new_tag = node["tag"]
        major, minor = int(new_tag.split('.')[0]), int(new_tag.split('.')[1])
        major += 1
        new_tag = str(major) + '.' + str(minor)
        os.system(f'''
            cd {node["repo_path"]}
            docker build -t {node["img_name"]}:{new_tag} .
        ''')
        for ids in node["children"]:
            old_name = node["img_name"] + ':' + node["tag"]
            new_name = node["img_name"] + ':' + new_tag
            dfs(ids, old_name, new_name)

    records.update_one({"_id": node["_id"]}, {"$set": {"lastsyncedtime": str(datetime.now().replace(microsecond=0))}})

