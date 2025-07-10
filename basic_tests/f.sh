
curl -i -X POST -H \
    "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MjA2NzQwNDYxMX0.Q1uSm1aKmTq-PxwM8P6CK5jjKM_caD5cY4aijvRRZmU" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, world!", "form": {"properties": {"response": {"type": "string"}}}}' \
    "https://shipshape.companionintelligence.org/process/text"

curl -i -X POST -H \
    "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MjA2NzQwNDYxMX0.Q1uSm1aKmTq-PxwM8P6CK5jjKM_caD5cY4aijvRRZmU" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, world!"}' \
    "https://shipshape.companionintelligence.org/chat"