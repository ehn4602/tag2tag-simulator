from state_machine import State, StateSerializer, StateMachine, TagMachine
import json


def main():

    sery = StateSerializer()
    # a = State()
    # b = State()
    # c = State()
    # d = State()
    # states = {}

    # giga = StateMachine(a, "Zero")
    # beta = StateMachine(d, "Uno")
    # output = []
    # output.append(giga), output.append(beta)

    # a.add_transition(1, ("A-> Input(1) to B", 2), b)
    # b.add_transition(0, ("B-> Input(0) back to A"), a)
    # b.add_transition(1, ("B-> Input(1) to C"), c)
    # c.add_transition(32, ("C->input(32) to D", 1, 2), d)
    # d.add_transition(12, ("d->input(12) to A"), a)
    # id = sery._map_state_to_id(a)
    # states[id] = a
    # states[sery._map_state_to_id(b)] = b
    # states[sery._map_state_to_id(c)] = c
    # states[sery._map_state_to_id(d)] = d
    # with open("test_state3.json", "w") as f:
    #     json.dump(
    #         {
    #             "state_machines": [
    #                 mach.to_dict(sery, "basic") for i, mach in enumerate(output)
    #             ],
    #             "states": sery.to_dict(),
    #         },
    #         f,
    #         indent=4,
    #     )

    with open("test_state3.json", "r") as f:
        raw_data = json.load(f)
    raw_states = raw_data.get("states", [])
    raw_machines = raw_data.get("state_machines", [])
    for state in raw_states:
        State.from_dict(state.get("id"), state, sery)
    machines = {mach["id"]: StateMachine.from_dict(sery, mach) for mach in raw_machines}
    with open("test_tags.json", "r") as f:
        raw_data = json.load(f)
    raw_tags = raw_data.get("tags", {})
    tags = {tag["id"]: TagMachine.from_dict(tag, machines) for tag in raw_tags.values()}

    # machines[0].debug = "Mach Zero"
    # machines[1].debug = "Mach Uno"
    # tag1 = TagMachine("ceres")
    # tag1.input_machine = machines[0]
    # tag1.processing_machine = machines[1]
    # tag1.output_machine = machines[0]
    # tag2 = TagMachine("luna")
    # tag2.input_machine = machines[1]
    # tag2.processing_machine = machines[0]
    # tag2.output_machine = machines[1]
    # all_tags = {}
    # all_tags["luna"] = tag2
    # all_tags["ceres"] = tag1

    with open("test_tags2.json", "w") as f:
        json.dump(
            {"format": "tag", "tags": {id: tag.to_dict() for id, tag in tags.items()}},
            f,
            indent=4,
        )

    with open("test_state2.json", "w") as f:
        json.dump(
            {
                "format": "state_machine",
                "state_machines": [
                    mach.to_dict(sery, "basic") for mach in machines.values()
                ],
                "states": sery.to_dict(),
            },
            f,
            indent=4,
        )

    print("hello")


if __name__ == "__main__":
    main()
