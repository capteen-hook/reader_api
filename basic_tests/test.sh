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
    auth_token=""
fi

echo "Running basic tests against ${url}"

# all routes using this schema for testing
schema="${current_dir}/schema.json"

file1="${current_dir}/pizza_recipe.txt"
file2="${current_dir}/pizza_recipe.pdf"
file3="${current_dir}/pizza_recipe.png"

get_noauth "${url}/"

get_noauth "${url}/docs"

task_id1=$(post_multipart "${auth_token}" "${url}/process/file" "${file1}" "${schema}") || exit 1

echo ""
echo "Task ID for file1: ${task_id1}"

task_id2=$(post_multipart "${auth_token}" "${url}/process/home" "${file2}" "${schema}") || exit 1

echo ""
echo "Task ID for file2: ${task_id2}"

task_id3=$(post_multipart "${auth_token}" "${url}/process/appliance" "${file3}" "${schema}") || exit 1

echo ""
echo "Task ID for file3: ${task_id3}"

json=$(jq -n \
  --arg message "Hello, are you alive" \
  --argjson form "$(cat "${schema}")" \
  '{message: $message, form: $form}')

post_json "${auth_token}" "${url}/process/text" "${json}"

post_json "${auth_token}" "${url}/chat" '{"message": "Hello, this is a chat test message."}'

post_file "${auth_token}" "${url}/process/ocr" "${file1}" "${schema}"

post_file "${auth_token}" "${url}/process/ocr" "${file2}" "${schema}"

post_file "${auth_token}" "${url}/process/ocr" "${file3}" "${schema}"

get "${auth_token}" "${url}/tasks/${task_id1}"

get "${auth_token}" "${url}/tasks/${task_id2}"

get "${auth_token}" "${url}/tasks/${task_id3}"

get "${auth_token}" "${url}/tasks"

post "${auth_token}" "${url}/clear"

echo " "
echo "All tests passed!"