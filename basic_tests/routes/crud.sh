#!/usr/bin/env bash
is_200() {
    local response="$1"

    # Fetch only the HTTP status code
    if [[ "$response" =~ ^HTTP/[0-9\.]+\ 200 ]]; then
        return 0
    else
        return 1
    fi
}

post() { # no body  
    local auth_token=$1
    local route=$2
    local response

    response=$(curl -s -i -X POST -H "Authorization: Bearer ${auth_token}" "${route}")

    if is_200 "${response}"; then
        echo -n "."
    else
        echo ""
        echo "POST ${route} failed: ${response}"
        exit 1
    fi
}

post_json() { # json body
    local auth_token=$1
    local route=$2
    local body=$3
    local response

    response=$(curl -s -i -X POST -H "Authorization: Bearer ${auth_token}" -H "Content-Type: application/json" -d "${body}" "${route}")

    if is_200 "${response}"; then
        echo -n "."
    else
        echo ""
        echo "POST ${route} with body ${body} failed: ${response}"
        exit 1
    fi
}

post_multipart() { # file and json schema
    local auth_token=$1
    local route=$2
    local file=$3
    local schema=$4
    local response
    
    response=$(curl -s -i -X POST -H "Authorization: Bearer ${auth_token}" -F "file=@${file}" -F "form=@${schema}" "${route}")

    if is_200 "${response}"; then
        local task_id
        task_id=$(echo "${response}" | grep -oP '(?<=task_id":")[^"]*')
        if [[ -n "${task_id}" ]]; then
            echo -n "${task_id}"
        else
            echo "No task ID found in response: ${response}" >&2
            exit 1
        fi
    else
        echo "" >&2
        echo "POST ${route} with file ${file} and schema ${schema} failed: ${response}" >&2
        exit 1
    fi
}


post_file() { # file and json schema
    local auth_token=$1
    local route=$2
    local file=$3
    local response

    response=$(curl -s -i -X POST -H "Authorization: Bearer ${auth_token}" -F "file=@${file}" "${route}")

    if is_200 "${response}"; then
        echo -n "."
    else
        echo ""
        echo "POST ${route} with file ${file} failed: ${response}"
        exit 1
    fi
}

get() { 
    local auth_token=$1
    local route=$2
    local response

    response=$(curl -s -i -X GET -H "Authorization: Bearer ${auth_token}" "${route}")
    if is_200 "${response}"; then
        echo -n "."
        echo "${response}"
    else
        echo ""
        echo "GET ${route} failed: ${response}"
        exit 1
    fi
}

get_noauth() { 
    local route=$1
    local response

    response=$(curl -s -i -X GET "${route}")

    if is_200 "${response}"; then
        echo -n "."
    else
        echo ""
        echo "GET ${route} failed: ${response}"
        exit 1
    fi
}