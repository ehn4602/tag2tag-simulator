import argparse
import json
import os
import sys
from tag import Tag

CONFIG_PATH = "config.json"


def load_config():
  """ Loads config file, gaining information it needs to run

  Returns:
      List: List of information thats stored in JSON file
  """
  if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH,'r') as f:
      raw_data = json.load(f)

    raw_tags = raw_data.get("Tags", {})
    raw_actions = raw_data.get("Actions",[])
    tags = {uid: Tag.from_dict(uid, val) for uid, val in raw_tags.items()}
    actions = [action for action in raw_actions]
    return tags,actions
  else:
    return {},[]
  
def save_config(tags,actions):
  """offloads changes back to JSON file

  Args:
      tags (dict): Dictionary of the tags that are in the system
      actions (list): List of actions that simulation will peform
  """
  with open(CONFIG_PATH,"w") as f:
    json.dump(
      {
        "Tags":{uid: tag.to_dict() for uid, tag in tags.items()},
        "Actions": [action for action in actions],
      },
      f
    )


def parse_tag(vals): 
  """Ensures the tag argument has the correct values
  Args:
      vals (List): tag UID, and its coordinats

  Returns:
      _type_: _description_
  """
  uid = vals[0]
  try:
    coords = [float(v) for v in vals[1:]]
  except ValueError as e:
      print("error: coordinates given are not numerical values")
      sys.exit(1)
  return uid,coords[0],coords[1],coords[2]
  
def parse_args():
  """ Parses arguments, can be in any order

  Returns:
      ArgumentParser: Argument parser which holds values of which arguments where given
  """
  parser = argparse.ArgumentParser(description='Tag-to-Tag Network Simulator')
  parser.add_argument('--tag',nargs=4,metavar=('UID','X','Y','Z'), required=False,
                      help='place a tag with its Unique ID at coordinates X,Y,Z')
  parser.add_argument('--remove',type=str,required=False,
                      help="Remove a specific tag based on UID")
  parser.add_argument('--print',type=str,
                      help="Arguments; actions,tags")
  
  parser.add_argument('--action',nargs=3,
                      help="An action that will be simulated")
  
  return parser.parse_args()


def main():

  tags,actions = load_config()
  args = parse_args()
  if args.tag is not None:
    uid,x,y,z = parse_tag(args.tag)
    tag = Tag(uid,x,y,z)
    if uid in tags:
      print("Tag",uid,"Moved to coordinates",x,y,z)
    else:
      print("Tag",uid,"Added at coordinate",x,y,z)
    tags[uid] = tag
    
  
  if args.remove:
    if args.remove in tags:
      del tags[args.remove]
    else:
      print("unkown id")
    

  if args.print:
    if(args.print == "tags"):
      for key, value in tags.items():
        print(f"{key}: {value.to_dict()}")
    elif(args.print == "actions"):
      for index,value in enumerate(actions,start=1):
        print(index,value)

  if args.action:
    action = args.action
    if action[0] not in tags:
        print("error, unkown tag:",action[0])
    elif action[1] not in tags:
        print("error, unkown tag:",action[1])
    actions.append(args.action)
  save_config(tags,actions)

if __name__ == "__main__":
  main()




##Todo
# tag size? tags are a specific size, they can't be placed on top of each other
# 