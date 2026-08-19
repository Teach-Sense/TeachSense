# TeachSense: Endpoint Error Responses (Concise Reference)

This file provides concrete examples of error responses developers will see from the backend for common endpoints. Use these to render errors in the frontend exactly as returned.

---

## Conventions
- Successful responses follow `APIResponse` wrapper: { success, message, data }
- Error responses follow `APIResponse.validation_error` or `APIResponse.error` wrappers:
  - `{ success: false, message: "...", errors: { field: ["error"] } }`
  - `{ success: false, message: "...", errors: { "non_field_errors": ["..."] } }`
- DRF default validation may also return `{ field: ["error message"] }` without `errors` wrapper.

---

## Auth: Register (`POST /api/auth/register/`)

- Missing email / invalid email:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "email": ["Email is required."]
  }
}
```

- Password mismatch (server-side):

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "password": ["Passwords do not match."]
  }
}
```

- Email already exists:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "email": ["A user with this email already exists."]
  }
}
```

- Generic validation (DRF style):

```json
{
  "username": ["This field may not be blank."],
  "email": ["Enter a valid email address."]
}
```

---

## Auth: Login (`POST /api/auth/login/`)

- Invalid credentials:

```json
{
  "success": false,
  "message": "Login failed.",
  "errors": {
    "non_field_errors": ["Invalid username or password."]
  }
}
```

---

## Sessions / Resources (e.g., `PATCH /api/sessions/{id}/`)

- Not found:

```json
{
  "success": false,
  "message": "Resource not found",
  "errors": {}
}
```

- Permission denied:

```json
{
  "success": false,
  "message": "Access denied",
  "errors": {}
}
```

- Business rule (conflict):

```json
{
  "success": false,
  "message": "Resource conflict",
  "errors": {
    "detail": "Session already ended"
  }
}
```

---

## Devices (`POST /api/devices/`)

- Missing required field:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "device_key": ["This field is required."]
  }
}
```

- Device authentication failed:

```json
{
  "success": false,
  "message": "Unauthorized access",
  "errors": {}
}
```

---

## Transcripts / Questions / Responses
- Validation errors follow the same pattern as above:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "session_id": ["This field is required."],
    "content": ["This field may not be blank."]
  }
}
```

---

## Rate Limit (429)
- When rate limited, HTTP status 429 is returned with message:

```json
{
  "success": false,
  "message": "Request was throttled. Expected available in 60 seconds.",
  "errors": {}
}
```

`Retry-After` header is set on the response.

---

## Server Error (500)
```json
{
  "success": false,
  "message": "Internal server error. Please try again later.",
  "errors": {}
}
```

---

## How Frontend Should Render
- Prefer rendering `errors` object verbatim when present.
- If `errors` absent, fall back to `message`, `detail`, or DRF-style field keys.
- For field-level errors, display the field label and each message on separate lines.

---

*This file is a concise companion to `ERROR_HANDLING.md` (more detailed rules and recovery strategies).*
