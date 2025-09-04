# tag2tag-simulator

This program is a discrete-event simulator that can be used for tag-to-tag backscattering networks intended to advance the field of Internet of Things. The program allows an adaptive approach to allow users to customized their tag's logic through a finite state machines mixed with commands that reflect a basic version of assembly. Users could upload their own state machines through json files to then create the environment they would like to simulate to retrieve any information that is being logged about scenario. 


# Installation

This program needs to be on python 3.13.1+

To get the dependencies needed to run main.py 

```pip install -r requirements.txt ```

To use the helper modulation_depth.bash script, install 

```sudo apt install jq   # Debian/Ubuntu```


# Help

Tags functionallity in this program use 3 state machines, Input machine responsible for incoming signals, Processing machine responsible for doing any logic with the inputed data, output machine to send outgoing messages. All states will need to be created on state.json config, while tags will only be define with each of the starter states IDs

To get started the environment can be loaded in as the following 

```python main.py --load example/test.txt``` 

test.txt is formatted to follow the supported console commands that can be used to define the environment. To learn more about these commands use the following command to get the help message

```python main.py --help```

# Authors 
- Ethan Numan
- Owen Avery
- Aaron Peterham
- Ingrid Rossetti
