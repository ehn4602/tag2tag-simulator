# May need to use git bash if on windows

cd ../..

# Terminate if command fails
set -euo pipefail 

# TODO: Implement multiple executions and log routing within the program
# Easy method until structure of sim changed
rm demo/7_tag_experiment/zero_helpers/logs/*
rm demo/7_tag_experiment/one_helper/logs/*
rm demo/7_tag_experiment/two_helpers/logs/*
rm demo/7_tag_experiment/three_helpers/logs/*
rm demo/7_tag_experiment/four_helpers/logs/*
rm demo/7_tag_experiment/five_helpers/logs/*

echo "Executing simulation with no helper"
python3 src/main.py --load demo/7_tag_experiment/zero_helpers.txt --run
sleep 1
cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/zero_helpers/logs/
sleep 1


echo "Executing Passive CoBa with one helper"
for ((i=1; i<=5; i++)); do
 	echo "Running config #$i..."
	# Remove
	rm demo/7_tag_experiment/one_helper/config.json
	# Copy
	cp demo/7_tag_experiment/one_helper/config_jsons/config$i.json demo/7_tag_experiment/one_helper/config.json
	python3 src/main.py --load demo/7_tag_experiment/one_helper.txt --run
	# Sleep
	sleep 1
	cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/one_helper/logs/
done

echo "Executing Passive CoBa with two helpers"
for ((i=1; i<=10; i++)); do
 	echo "Running config #$i..."
	rm demo/7_tag_experiment/two_helpers/config.json
	cp demo/7_tag_experiment/two_helpers/config_jsons/config$i.json demo/7_tag_experiment/two_helpers/config.json
	python3 src/main.py --load demo/7_tag_experiment/two_helpers.txt --run
	sleep 1
	cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/two_helpers/logs/
done

echo "Executing Passive CoBa with three helpers"
for ((i=1; i<=10; i++)); do
 	echo "Running config #$i..."
	rm demo/7_tag_experiment/three_helpers/config.json
	cp demo/7_tag_experiment/three_helpers/config_jsons/config$i.json demo/7_tag_experiment/three_helpers/config.json
	python3 src/main.py --load demo/7_tag_experiment/three_helpers.txt --run
	sleep 1
	cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/three_helpers/logs/
done

echo "Executing Passive CoBa with four helpers"
for ((i=1; i<=5; i++)); do
 	echo "Running config #$i..."
	rm demo/7_tag_experiment/four_helpers/config.json
	cp demo/7_tag_experiment/four_helpers/config_jsons/config$i.json demo/7_tag_experiment/four_helpers/config.json
	python3 src/main.py --load demo/7_tag_experiment/four_helpers.txt --run
	sleep 1
	cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/four_helpers/logs/
done



echo "Executing Passive CoBa with five helpers"
python3 src/main.py --load demo/7_tag_experiment/five_helpers.txt --run
sleep 1
cp logs/$(ls logs | grep json | tail -n 1) demo/7_tag_experiment/five_helpers/logs/

