# sery isn a serializer
# loads states correctly from json
with open("test_state.json", "r") as f:
    raw_data = json.load(f)
    raw_states = raw_data.get("states", {})
    states = {
        id: State.from_dict(int(id), data, sery) for id, data in raw_states.items()
    }
# writes states into json correctly
with open("test_state2.json", "w") as f:
    json.dump(
        {"states": {id: state.to_dict(sery) for id, state in states.items()}},
        f,
        indent=4,
    )


# b = State()
# c = State()
# states = {}
# id = sery._map_state_to_id(a)
# states[id] = a
# states[sery._map_state_to_id(b)] = b
# states[sery._map_state_to_id(c)] = c

# a.add_transition(1, ("transit", 2), b)
# b.add_transition(0, ("transit"), a)
# b.add_transition(1, ("transit"), c)

# with open("test_state.json", "w") as f:
#     json.dump(
#         {"states": {id: state.to_dict(sery) for id, state in states.items()}},
#         f,
#         indent=4,
#     )

# with open("test_state.json", "r") as f:
#     raw_data = json.load(f)
#     raw_states = raw_data.get("states", {})
#     states = {
#         id: State.from_dict(int(id), data, sery) for id, data in raw_states.items()
#     }

#     # if raw_data.get("Format") == "config":
#     #     raw_objects = raw_data.get("Objects", {})
#     #     raw_events = raw_data.get("events", [])

#     #     default = raw_data.get("Default")
#     #     tags = {uid: Tag.from_dict(uid, val) for uid, val in raw_objects.items()}
#     #     events = [event for event in raw_events]
#     #     return None, tags, events, default
# print("hello")
# with open("test_state2.json", "w") as f:
#     json.dump(
#         {"states": {id: state.to_dict(sery) for id, state in states.items()}},
#         f,
#         indent=4,
#     )
