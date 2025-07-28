#!/usr/bin/env bash
# test.sh : ./basic_tests/test.sh http://localhost:8000 
# get crud functions from ./routes/crud.sh
current_dir=$(dirname "$0")
source "${current_dir}/routes/crud.sh"

url=$1

if [[ -z "${url}" ]]; then
    url="http://localhost:8000"
fi

auth_token=$2

if [[ -z "${auth_token}" ]]; then
    auth_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MjA2ODk0OTE5Mn0.JJcDkvd924NDS6FCFVdPIOw6ASDGsou0MYNKsdpQZcY"
fi

echo "Running basic tests against ${url}"

# all routes using this schema for testing
schema="${current_dir}/label.json"

file1="${current_dir}/dishwasher.jpg"
file2="${current_dir}/dishwasher2.jpg"
file3="${current_dir}/dishwasher3.jpg"
file4="${current_dir}/dryer_hard.jpg"
file5="${current_dir}/dryer.webp"
file6="${current_dir}/pump.jpg"
file7="${current_dir}/pump.webp"
file8="${current_dir}/pump2.jpg"
file9="${current_dir}/waterheater_easy.jpg"
file10="${current_dir}/waterheater_hard.png"
file11="${current_dir}/waterheater_medium.webp"


task_id1=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file1}" "${schema}") || exit 1
task_id2=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file2}" "${schema}") || exit 1
task_id3=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file3}" "${schema}") || exit 1
task_id4=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file4}" "${schema}") || exit 1
task_id5=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file5}" "${schema}") || exit 1
task_id6=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file6}" "${schema}") || exit 1
task_id7=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file7}" "${schema}") || exit 1
task_id8=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file8}" "${schema}") || exit 1
task_id9=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file9}" "${schema}") || exit 1
task_id10=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file10}" "${schema}") || exit 1
task_id11=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file11}" "${schema}") || exit 1

# wait 20 seconds for tasks to complete
echo "Waiting for tasks to complete..."
sleep 20

get "${auth_token}" "${url}/tasks/${task_id1}"
get "${auth_token}" "${url}/tasks/${task_id2}"
get "${auth_token}" "${url}/tasks/${task_id3}"
get "${auth_token}" "${url}/tasks/${task_id4}"
get "${auth_token}" "${url}/tasks/${task_id5}"
get "${auth_token}" "${url}/tasks/${task_id6}"
get "${auth_token}" "${url}/tasks/${task_id7}"
get "${auth_token}" "${url}/tasks/${task_id8}"
get "${auth_token}" "${url}/tasks/${task_id9}"
get "${auth_token}" "${url}/tasks/${task_id10}"
get "${auth_token}" "${url}/tasks/${task_id11}"

get "${auth_token}" "${url}/tasks"
post "${auth_token}" "${url}/clear"

echo " "
echo "All tests passed!"