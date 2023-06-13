import os, pymongo, json, pytz, time
import requests
from github import Github
from datetime import datetime

root_path = '/Users/shahpoojandikeshkumar/Desktop/SI/repos'
client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('myDB')
records = db['Images']
repo_name = "docker-bakery_repo12"
repo_url = f"Poojan230103/{repo_name}"       # to be taken from the config file
mygit = Github("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")
myrepo = mygit.get_repo(repo_url)


def convert_to_indian_time(utc_time_zone):
    india_timezone = pytz.timezone('Asia/Kolkata')
    india_time = pytz.utc.localize(utc_time_zone).astimezone(india_timezone)
    india_time = india_time.strftime('%Y-%m-%d %H:%M:%S')
    india_time = datetime.strptime(india_time, '%Y-%m-%d %H:%M:%S')       #  datetime object
    return india_time


def dfs(node_id):         # recursively re-building the subtree on updation of the parent node
    childnode = records.find_one({"_id": node_id})
    if childnode["component_name"]:
        # idx_child = childnode["componentfile_local_path"].rfind('/')
        # dir_path_child = childnode["componentfile_local_path"][:idx_child]
        #
        # shell_file_name_child = childnode["componentfile_local_path"][idx_child + 1:]

        # os.system(f'''
        #         cd {dir_path_child}
        #         pwd
        #         sh {shell_file_name_child} {childnode["componentname"]}
        # ''')

        parameter = {"repo_name": childnode["repo_name"], "component_name": childnode["component_name"], "tag": childnode["tag"], "branch_name": "dummy"}
        response = requests.post("http://127.0.0.1:9000/build", data=parameter)
        response = response.json()
        print(response)
        parameter = {"job_id": response["job_id"]}
        while True:
            response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
            response = response.json()
            if response["status"] == "Success" or response["status"] == "Failed":
                print(response["status"])
                break
            time.sleep(5)

        for ids_child in childnode["children"]:
            dfs(ids_child)
    else:
        # dockerfile_path_child = childnode["dockerfile_local_path"]
        # os.system(f'''
        #     cd {dockerfile_path_child}
        #     docker build -t {childnode["img_name"]} .
        # ''')
        parameter = {"dockerfile_local_path": childnode["dockerfile_local_path"],
                     "img_name": childnode["img_name"],
                     "tag": childnode["tag"],
                     "branch_name": "dummy"}

        response = requests.post("http://127.0.0.1:9000/build_no_comp", data=parameter)
        response = response.json()
        print(response)
        parameter = {"job_id": response["job_id"]}
        while True:
            response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
            response = response.json()
            if response["status"] == "Success" or response["status"] == "Failed":
                print(response["status"])
                break
            time.sleep(5)

        for ids_child in childnode["children"]:
            dfs(ids_child)

    records.update_one(
        {"_id": childnode["_id"]}, {"$set": {"last_updated_time": str(datetime.now().replace(microsecond=0))}}
    )
    records.update_one(
        {"_id": childnode["_id"]}, {"$set": {"last_synced_time": str(datetime.now().replace(microsecond=0))}}
    )



# Below is the code to sync the specified repository. The repo may contain multiple Components, hence syncing each of them.
# extracting all the nodes built from this repository
nodes_cursor = records.find({"repo_name": repo_name})
nodes_list_cursor = list(nodes_cursor)
nodes_json_data = json.dumps(nodes_list_cursor, indent=4)
nodes_data = json.loads(nodes_json_data)

for node in nodes_data:
    #check for docker file
    var = node["dockerfile_repo_path"]         # docker file
    commits = myrepo.get_commits(path=var)
    flag = False
    utc_time = commits[0].commit.committer.date
    t = convert_to_indian_time(utc_time)
    last_sync_time = node["last_synced_time"]     # in string format
    last_sync_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')

    if t > last_sync_time:
        flag = True
        file_contents = myrepo.get_contents(path=node["dockerfile_repo_path"]).decoded_content.decode()
        f = open(node["dockerfile_local_path"], 'w')
        f.write(file_contents)
        f.close()

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
            file_contents = myrepo.get_contents(path=var).decoded_content.decode()
            f = open(dep["deps_local_path"], 'w')
            f.write(file_contents)
            f.close()

    if flag and node["component_name"]:
        parameter = {"repo_name": node["repo_name"],
                     "component_name": node["component_name"],
                     "tag": node["tag"]
                     }

        response = requests.post("http://127.0.0.1:9000/build", data=parameter)
        response = response.json()
        print(response)
        parameter = {"job_id": response["job_id"]}
        while True:
            response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
            response = response.json()
            if response["status"] == "Success" or response["status"] == "Failed":
                print(response["status"])
                break
            time.sleep(5)

        for ids in node["children"]:
            dfs(ids)
        records.update_one(
            {"_id": node["_id"]}, {"$set": {"last_updated_time": str(datetime.now().replace(microsecond=0))}}
        )

    elif flag:
        parameter = {"dockerfile_local_path": node["dockerfile_local_path"],
                     "img_name": node["img_name"],
                     "tag": node["tag"],
                     "branch_name": "dummy"}

        response = requests.post("http://127.0.0.1:9000/build_no_comp", data=parameter)
        response = response.json()
        print(response)
        parameter = {"job_id": response['job_id']}
        while True:
            response = requests.post("http://127.0.0.1:9000/poll", data=parameter)
            response = response.json()
            if response["status"] == "Success" or response["status"] == "Failed":
                print(response["status"])
                break
            time.sleep(5)

        for ids in node["children"]:
            dfs(ids)
        # os.system(f'''
        #     cd {dockerfile_path}
        #     docker build -t {node["img_name"]}:{node["tag"]} .
        # ''')
    records.update_one({"_id": node["_id"]}, {"$set": {"last_synced_time": str(datetime.now().replace(microsecond=0))}})




