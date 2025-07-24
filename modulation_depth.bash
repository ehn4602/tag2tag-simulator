LOGFILE="$(dirname "$0")/$(ls logs/*.json | tail -n 1)"

jq -r -s '1
map(select(.tag != null and .voltage != null)) |
sort_by(.tag) |
group_by(.tag) |
map({
  tag: .[0].tag,
  min_voltage: (map(.voltage) | min),
  max_voltage: (map(.voltage) | max)
}) |
map({
  tag: .tag,
  modulation_depth: (( .max_voltage - .min_voltage ) / (.max_voltage + .min_voltage)),
  min_voltage: .min_voltage,
  max_voltage: .max_voltage
}) |
(["tag", "modulation_depth", "min_voltage", "max_voltage"]),  # header
(.[] | [.tag, .modulation_depth, .min_voltage, .max_voltage]) # rows
| @csv
' $LOGFILE > processed.csv
