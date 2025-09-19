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


To see an example environment being loaded by a text file, test.txt can be viewed in the exampls subdirectory. This file is only meant to show different arguments that can be used both via tha command line or in a test file, Loading this file won't show any meaningful results if simulated. 

To get more information about these commands use the following command to get the help message 

```python main.py --help```


# Demo & How to run

To be able to run this program you will need to have your working directory in as ./src
getting started, the environment can be loaded in as the following 

```python main.py --load ../demo/tags_in_a_line/load_json.txt``` 

This will load in a demonstration that was set up to show phase cancellation

to run the simulation rerun the program without any additional arguments

```python main.py```

This will run the demonstration that was loaded in. The results will be sent to the log directory outside of src. If you would like to see a plot for this demo,
you can set the working directory into the demo itself and do the following commands


```bash modulation_depth.bash```

```python plot_modulation_depth.py``` 

The bash script reconfigures the most recent log file into a csv that plot_modulation_depth.py will 
use to plot the results. This plot shows how phase cancellation can occur from backscattering tags

# Authors 
- Ethan Numan
- Owen Avery
- Aaron Peterham
- Ingrid Rossetti
