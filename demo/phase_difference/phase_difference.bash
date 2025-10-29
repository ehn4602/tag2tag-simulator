LOGFILE="$(dirname "$0")/../../logs/$(ls ../../logs | grep '\.json$' | tail -n 1)"

jq -r -s '
map(select(.tag != null and .distance_from_sender != null and .previous_distance_from_sender != null and .previous_distance_from_sender != .distance_from_sender and .sender_frequency != null)) |
sort_by(.tag) |
group_by(.tag) |
map({
	tag: .[0].tag,
	sender_frequency: .[0].sender_frequency,
  distance_from_sender: .[0].distance_from_sender,
  previous_distance_from_sender: .[0].previous_distance_from_sender,
  lambda: (299792458 / .[0].sender_frequency),
  deltaD: ( .[0].distance_from_sender - .[0].previous_distance_from_sender )
}) |
map({
  tag: .tag,
  distance_from_sender: .distance_from_sender,
  deltaD: .deltaD,
  sender_frequency: .sender_frequency,
  phaseAngle: ((6.28318530718 * .distance_from_sender) / .lambda),
  phaseDifference: ((6.28318530718 * .deltaD) / .lambda)
}) |
(["tag", "distance_from_sender", "deltaD", "sender_frequency", "phaseAngle", "phaseDifference"]),  # header
(.[] | [.tag, .distance_from_sender, .deltaD, .sender_frequency, .phaseAngle, .phaseDifference]) # rows
| @csv
' $LOGFILE > processed.csv
