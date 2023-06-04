import pymongo
import json


root_id = 3

class treenode:

    def __init__(self,data):
        self.__dict__ = data

    s_id = None
    img_name = None
    tag = None
    children = []
    parent = None
    sibling = None
    local_path = None
    repo_path = None
    components = []
    lastsyncedtime = None
    architecture = None
    files = []


def create_hierarchy(data, parent_id=None):     # to create hierarchy
    hierarchy = []
    for item in data:
        if item["parent"] == parent_id:
            children = create_hierarchy(data, parent_id=item["_id"])
            item["children"] = children
            hierarchy.append(item)
    return hierarchy


if __name__ == "__main__":
    client = pymongo.MongoClient("mongodb+srv://admin:me_Poojan23@cluster0.z9bxxjw.mongodb.net/?retryWrites=true&w=majority")
    # print(client)
    db = client.get_database('myDB')
    records = db['Images']

    cursor = records.find()
    list_cursor = list(cursor)
    json_data = json.dumps(list_cursor, indent=4)

    with open('data.json', 'w') as file:
        file.write(json_data)

    data = json.loads(json_data)
    hierarchy = create_hierarchy(data)
    # print(hierarchy)
    json_data = json.dumps(hierarchy[0],indent=2)
    f = open('data.json', 'w')
    f.write(json_data)
    f.close()



