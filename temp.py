import json


def create_hierarchy(data, parent_id=None):
    hierarchy = []
    for item in data:
        if item["parent"] == parent_id:
            children = create_hierarchy(data, parent_id=item["_id"])
            item["children"] = children
            hierarchy.append(item)
    return hierarchy


# Parse the JSON data
data = json.loads('')

# Convert the JSON data to hierarchy format
hierarchy = create_hierarchy(data)
hierarchy = json.dumps(hierarchy,indent=4)
f = open('data.json','w')
f.write(hierarchy)
f.close()