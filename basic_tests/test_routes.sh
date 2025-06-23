#!/bin/bash

# Shared function to handle POST requests
post_request() {
  local url=$1
  local file=$2
  local json=$3

  curl -X POST "$url" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$file" \
    -F "json=$json" \
    -w "\nHTTP Status: %{http_code}\n"
}

# Base URL
BASE_URL="http://localhost:8000"

# Test /pdf route
test_pdf() {
  echo "Testing /pdf route..."
  post_request "$BASE_URL/pdf" "G:/reader_api/basic_tests/pizza_recipe.pdf" '{"form": {}}'
  post_request "$BASE_URL/pdf" "G:/reader_api/basic_tests/report_easy.pdf" '{"form": {}}'
}

# Test /home route
test_home() {
  echo "Testing /home route..."
  post_request "$BASE_URL/home" "G:/reader_api/basic_tests/report_easy.pdf" '{"form": {"address": "string", "latlon": "array[number]"}}'
}

# Test /appliance route
test_appliance() {
  echo "Testing /appliance route..."
  post_request "$BASE_URL/appliance" "G:/reader_api/basic_tests/waterheater_easy.jpg" '{"form": {"serial_number": "string", "manufacturer": "string"}}'
  post_request "$BASE_URL/appliance" "G:/reader_api/basic_tests/waterheater_hard.png" '{"form": {"serial_number": "string", "manufacturer": "string"}}'
  post_request "$BASE_URL/appliance" "G:/reader_api/basic_tests/waterheater_medium.webp" '{"form": {"serial_number": "string", "manufacturer": "string"}}'
}

# Run tests
test_pdf
test_home
test_appliance