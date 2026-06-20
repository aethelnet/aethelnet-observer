# Backend Configuration API Specification

**Date:** January 2, 2025  
**Status:** 📋 **SPECIFICATION** - Ready for Backend Implementation  
**Purpose:** Define the `/api/config` endpoint for frontend to send API keys and configuration to backend

---

## Overview

The frontend Settings view allows users to input API keys (Binance API key, secret key, admin tokens, etc.), but currently these are only saved to browser localStorage. This specification defines the backend endpoint that will allow the frontend to securely send these configuration values to the backend for storage and use.

---

## Endpoint Specification

### **POST `/api/config`**

**Purpose:** Update backend configuration values (API keys, tokens, etc.)

**Authentication:** Required (see Security section)

**Request Format:**
```json
{
  "binance_api_key": "your_binance_api_key",
  "binance_secret_key": "your_binance_secret_key",
  "admin_token": "your_admin_token",
  "api_key": "your_api_key"
}
```

**Response Format (Success):**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "updated_fields": ["binance_api_key", "binance_secret_key"]
}
```

**Response Format (Error):**
```json
{
  "error": true,
  "status": 400,
  "detail": "Invalid Binance API key: Connection test failed"
}
```

---

## Supported Configuration Fields

The frontend may send any of these fields:

| Field Name | Type | Description | Validation Required |
|------------|------|-------------|---------------------|
| `binance_api_key` | string | Binance exchange API key | ✅ Yes - Test connection |
| `binance_secret_key` | string | Binance exchange secret key | ✅ Yes - Test with API key |
| `admin_token` | string | Administrative token for system control | ⚠️ Optional - Validate format |
| `api_key` | string | General API key for backend authentication | ⚠️ Optional - Validate format |

**Note:** The frontend may send one field at a time or multiple fields in a single request.

---

## Security Requirements

### 1. **Authentication/Authorization**

The endpoint MUST verify that the requester is authorized to update configuration:

**Option A: Admin Token in Request**
- Check if `admin_token` is provided in the request
- Validate against stored admin token (from `.env` or config)
- If valid, allow update

**Option B: Authorization Header**
- Check `Authorization: Bearer <token>` header
- Validate token against authorization system
- If valid, allow update

**Option C: User Authorization**
- Check if current user (from session/auth) has admin permissions
- Use existing authorization system (beta_rat, is_authorized, etc.)
- If authorized, allow update

**Recommendation:** Support Option A (admin_token in request) as it's simplest and matches the frontend's current design.

### 2. **Input Validation**

- **Required:** Validate all input fields before processing
- **Sanitization:** Remove whitespace, validate format
- **Length Limits:** Enforce reasonable length limits for keys/tokens

### 3. **Sensitive Data Handling**

- **Encryption:** Store API keys encrypted at rest (not plain text in `.env`)
- **Logging:** DO NOT log API keys or secrets in plain text
- **Transmission:** Use HTTPS in production (already handled by FastAPI)

---

## Validation Requirements

### **Binance API Keys**

When `binance_api_key` and/or `binance_secret_key` are provided:

1. **Test Connection:**
   - Attempt to connect to Binance API using provided credentials
   - Verify the keys are valid and have appropriate permissions
   - If test fails, return error with details

2. **Permission Check:**
   - Verify keys have trading permissions (if required)
   - Verify keys are not restricted (IP whitelist, etc.)

3. **Error Handling:**
   - If validation fails, return clear error message
   - Do NOT save invalid keys

**Example Validation:**
```python
def validate_binance_keys(api_key: str, secret_key: str) -> tuple[bool, str]:
    """
    Validate Binance API keys by testing connection.
    Returns: (is_valid, error_message)
    """
    try:
        # Test connection to Binance API
        # Return (True, "") if valid, (False, error_msg) if invalid
        pass
    except Exception as e:
        return (False, f"Binance API validation failed: {str(e)}")
```

### **Admin Token**

When `admin_token` is provided:
- Validate format (if there's a specific format)
- Optionally check against existing admin token
- Store securely

### **General API Key**

When `api_key` is provided:
- Validate format (if there's a specific format)
- Store securely

---

## Storage Implementation

### **Option 1: Update `.env` File (Recommended for Development)**

- Read current `.env` file
- Update or add configuration values
- Write back to `.env` file
- **Note:** Backend may need restart to load new values

**Pros:**
- Simple implementation
- Works with existing configuration system
- Easy to verify

**Cons:**
- Requires file write permissions
- May need backend restart

### **Option 2: Runtime Configuration Update**

- Store configuration in memory/runtime config
- Update settings object without file modification
- Configuration persists until backend restart

**Pros:**
- No file I/O required
- Immediate effect (no restart needed)

**Cons:**
- Configuration lost on restart
- May need to persist to file anyway

### **Option 3: Separate Config File**

- Store API keys in separate encrypted config file (e.g., `api_keys.json.encrypted`)
- Load on startup
- Update via API

**Pros:**
- Better security (encrypted)
- Separate from `.env` file
- Can reload without restart

**Cons:**
- More complex implementation
- Need encryption/decryption logic

**Recommendation:** Start with Option 1 (update `.env` file) for simplicity, with clear documentation that backend restart may be required.

---

## Error Handling

### **HTTP Status Codes**

| Status Code | Scenario |
|-------------|----------|
| `200 OK` | Configuration updated successfully |
| `400 Bad Request` | Invalid input (missing fields, validation failed) |
| `401 Unauthorized` | Authentication/authorization failed |
| `403 Forbidden` | User not authorized to update config |
| `500 Internal Server Error` | Server error (file write failed, etc.) |

### **Error Response Format**

```json
{
  "error": true,
  "status": 400,
  "detail": "Invalid Binance API key: Connection test failed. Please verify your API key and secret key."
}
```

### **Common Error Scenarios**

1. **Missing Authorization:**
   ```json
   {
     "error": true,
     "status": 401,
     "detail": "Authentication required. Please provide admin_token or valid authorization."
   }
   ```

2. **Invalid Binance Keys:**
   ```json
   {
     "error": true,
     "status": 400,
     "detail": "Binance API validation failed: Invalid API key or secret key."
   }
   ```

3. **File Write Error:**
   ```json
   {
     "error": true,
     "status": 500,
     "detail": "Failed to update configuration file. Check file permissions."
   }
   ```

4. **Invalid Field Name:**
   ```json
   {
     "error": true,
     "status": 400,
     "detail": "Unknown configuration field: 'invalid_field'. Supported fields: binance_api_key, binance_secret_key, admin_token, api_key"
   }
   ```

---

## Implementation Checklist

- [ ] Create `/api/config` POST endpoint
- [ ] Implement authentication/authorization check
- [ ] Add input validation for all fields
- [ ] Implement Binance API key validation (test connection)
- [ ] Add secure storage (encrypted or secure file)
- [ ] Implement error handling with proper HTTP status codes
- [ ] Add logging (without sensitive data)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Document in API docs

---

## Testing Requirements

### **Unit Tests**

1. **Authentication Tests:**
   - Test with valid admin_token → should succeed
   - Test without admin_token → should return 401
   - Test with invalid admin_token → should return 401

2. **Validation Tests:**
   - Test with valid Binance keys → should succeed
   - Test with invalid Binance keys → should return 400
   - Test with missing required fields → should return 400

3. **Storage Tests:**
   - Test updating single field → should update correctly
   - Test updating multiple fields → should update all
   - Test file write permissions → should handle errors

### **Integration Tests**

1. **End-to-End Test:**
   ```bash
   # Test full flow
   curl -X POST http://localhost:8000/api/config \
     -H "Content-Type: application/json" \
     -d '{
       "admin_token": "valid_token",
       "binance_api_key": "test_key",
       "binance_secret_key": "test_secret"
     }'
   ```

2. **Verify Configuration Updated:**
   - Check that `.env` file or config file is updated
   - Verify values are correct
   - Test that backend can use new keys

---

## Frontend Integration

The frontend is already set up to use this endpoint:

**Frontend Code Location:**
- `src/shared/api.js` - `updateSystemConfig()` function
- `src/views/SettingsView.vue` - `saveConfig()` function

**Current Frontend Behavior:**
1. User enters API key in Settings view
2. Frontend calls `updateSystemConfig({ binance_api_key: "..." })`
3. Frontend expects response from `/api/config`
4. If successful, shows "saved successfully"
5. If error, falls back to localStorage and shows "saved locally"

**No frontend changes needed** - it's already implemented and ready to use once the backend endpoint exists.

---

## Example Implementation (Python/FastAPI)

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/api", tags=["config"])

class ConfigUpdate(BaseModel):
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    admin_token: Optional[str] = None
    api_key: Optional[str] = None

def verify_admin_token(admin_token: Optional[str] = None) -> bool:
    """Verify admin token from request or environment."""
    if admin_token:
        # Check against stored admin token
        stored_token = os.getenv("ADMIN_TOKEN")
        return admin_token == stored_token
    return False

def validate_binance_keys(api_key: str, secret_key: str) -> tuple[bool, str]:
    """Validate Binance API keys by testing connection."""
    try:
        # TODO: Implement Binance API connection test
        # from binance.client import Client
        # client = Client(api_key, secret_key)
        # client.ping()  # Test connection
        return (True, "")
    except Exception as e:
        return (False, f"Binance API validation failed: {str(e)}")

@router.post("/config")
async def update_config(config: ConfigUpdate):
    """
    Update backend configuration (API keys, tokens, etc.).
    Requires admin_token for authorization.
    """
    # Verify authorization
    if not verify_admin_token(config.admin_token):
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide valid admin_token."
        )
    
    updated_fields = []
    errors = []
    
    # Validate and update Binance keys
    if config.binance_api_key or config.binance_secret_key:
        if not config.binance_api_key or not config.binance_secret_key:
            raise HTTPException(
                status_code=400,
                detail="Both binance_api_key and binance_secret_key must be provided together."
            )
        
        is_valid, error_msg = validate_binance_keys(
            config.binance_api_key,
            config.binance_secret_key
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Update .env file or config
        # TODO: Implement secure storage
        updated_fields.extend(["binance_api_key", "binance_secret_key"])
    
    # Update other fields
    if config.admin_token:
        # TODO: Update admin token
        updated_fields.append("admin_token")
    
    if config.api_key:
        # TODO: Update API key
        updated_fields.append("api_key")
    
    if not updated_fields:
        raise HTTPException(
            status_code=400,
            detail="No valid configuration fields provided."
        )
    
    return {
        "success": True,
        "message": "Configuration updated successfully",
        "updated_fields": updated_fields
    }
```

---

## Security Best Practices

1. **Never log sensitive data:**
   ```python
   # ❌ BAD
   logger.info(f"Received API key: {api_key}")
   
   # ✅ GOOD
   logger.info("Received binance_api_key (length: {})".format(len(api_key)))
   ```

2. **Encrypt at rest:**
   - Use encryption library (e.g., `cryptography`) to encrypt API keys before storing
   - Store encryption key securely (environment variable, key management service)

3. **Rate limiting:**
   - Add rate limiting to prevent brute force attacks
   - Limit to X requests per minute per IP

4. **Input sanitization:**
   - Remove whitespace, validate format
   - Reject suspicious patterns

---

## Migration Path

If the backend already has API keys in `.env`:

1. **On first API call:**
   - Read existing values from `.env`
   - Return them to frontend (if GET endpoint is added)
   - Allow frontend to update via POST

2. **Backward compatibility:**
   - Support both `.env` file and API-based configuration
   - `.env` file takes precedence on startup
   - API updates override runtime values

---

## Open Questions for Backend Agent

1. **Where should API keys be stored?**
   - `.env` file (simple, but requires restart)
   - Separate encrypted config file (better security)
   - Database (most flexible, but more complex)

2. **Should configuration reload without restart?**
   - Yes: More user-friendly, but requires runtime config reload
   - No: Simpler, but requires backend restart

3. **How to handle existing `.env` values?**
   - Overwrite with API values?
   - Merge with API values?
   - Keep `.env` as fallback?

4. **Should there be a GET endpoint?**
   - `GET /api/config` to retrieve current config (masked values)
   - Useful for frontend to show current values

---

## Success Criteria

The implementation is complete when:

1. ✅ Frontend can successfully send API keys to `/api/config`
2. ✅ Backend validates Binance API keys before saving
3. ✅ Backend stores keys securely (encrypted or secure file)
4. ✅ Backend can use new API keys for trading
5. ✅ Error messages are clear and helpful
6. ✅ All tests pass
7. ✅ Documentation is updated

---

## References

- **Frontend Implementation:**
  - `src/shared/api.js` - `updateSystemConfig()` function
  - `src/views/SettingsView.vue` - Settings view with API key inputs

- **Related Endpoints:**
  - `GET /api/dashboard/status` - Returns current system status
  - `GET /api/trading/config` - Returns trading configuration

---

**Last Updated:** January 2, 2025  
**Status:** Ready for Backend Implementation

