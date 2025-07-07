#!/usr/bin/env bash
# test.sh
# get crud functions from ./routes/crud.sh
current_dir=$(dirname "$0")
source "${current_dir}/routes/crud.sh"

url=$1

if [[ -z "${url}" ]]; then
    url="http://localhost:8000"
fi

auth_token=$2

if [[ -z "${auth_token}" ]]; then
    auth_token=""eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MjA2NzIxMjg3NX0.mF5-1ILTbi2S6nbDX36heDr-3NH7LdVhxr4B3QWnN0E" "
fi

echo "Running basic tests against ${url}"

# all routes using this schema for testing
schema="${current_dir}/schema.json"

file1="${current_dir}/pizza_recipe.txt"
file2="${current_dir}/pizza_recipe.pdf"
file3="${current_dir}/pizza_recipe.png"

ls -la "${current_dir}/openapi_spec.yaml"

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

post_file "${auth_token}" "${url}/process/ocr" "${file1}" "${schema}"

post_file "${auth_token}" "${url}/process/ocr" "${file2}" "${schema}"

post_file "${auth_token}" "${url}/process/ocr" "${file3}" "${schema}"

get "${auth_token}" "${url}/tasks/${task_id1}"

get "${auth_token}" "${url}/tasks/${task_id2}"

get "${auth_token}" "${url}/tasks/${task_id3}"]

get "${auth_token}" "${url}/tasks"

post "${auth_token}" "${url}/clear"

echo " "
echo "All tests passed!"