# Threat Model

## Overview

This document outlines security considerations for the Security Incident Triage Dashboard.

## Assets

1. **Alert Data**: Security alerts containing sensitive information
2. **Incident Data**: Correlated incidents with analyst notes
3. **Audit Logs**: Record of system actions
4. **User Sessions**: (Future) Authentication tokens

## Threat Categories

### T1: Unauthorized Access

**Threat**: Unauthorized users accessing the dashboard

**Current State**: 
- No authentication implemented (development mode)
- CORS restricted to localhost origins

**Mitigations for Production**:
- Implement OAuth2/OIDC authentication
- Add role-based access control (RBAC)
- Use secure session management
- Enable HTTPS

### T2: Data Injection

**Threat**: Malicious data in uploaded alert files

**Current Mitigations**:
- File type validation (JSON/CSV only)
- UTF-8 encoding validation
- JSON parsing with error handling
- Pydantic schema validation
- SQLAlchemy parameterized queries (prevents SQL injection)

**Additional Recommendations**:
- Add file size limits
- Implement content scanning
- Sanitize HTML in descriptions

### T3: Information Disclosure

**Threat**: Sensitive data exposed through API or logs

**Current Mitigations**:
- No secrets in repository
- Structured error responses (no stack traces in production)
- Raw alert data stored but not exposed by default

**Recommendations**:
- Implement field-level access control
- Add data masking for PII
- Audit log sensitive operations

### T4: Denial of Service

**Threat**: System overwhelmed by large uploads or requests

**Current Mitigations**:
- Pagination on list endpoints
- Async file processing

**Recommendations**:
- Implement rate limiting (stub exists)
- Add request size limits
- Queue large operations

### T5: Cross-Site Scripting (XSS)

**Threat**: Malicious scripts injected via alert data

**Current Mitigations**:
- React escapes output by default
- No `dangerouslySetInnerHTML` usage

**Recommendations**:
- Content Security Policy headers
- Input sanitization for rich text fields

### T6: Cross-Site Request Forgery (CSRF)

**Threat**: Unauthorized actions via forged requests

**Current Mitigations**:
- CORS configuration restricts origins
- State-changing operations require POST/PATCH

**Recommendations**:
- Add CSRF tokens for production
- Use SameSite cookies

## Security Controls

### Input Validation

| Input | Validation |
|-------|------------|
| File uploads | Type check, UTF-8 encoding, JSON/CSV parsing |
| Alert data | Pydantic schema validation |
| Incident updates | Enum validation for status |
| Query parameters | Type coercion, bounds checking |

### Audit Logging

Logged actions:
- `data_import`: File uploads and demo data loading
- `status_change`: Incident status updates
- `report_export`: Report generation

Log fields:
- Action type
- Entity type and ID
- Request details (JSON)
- Client IP address
- Timestamp

### Secure Headers (Recommended)

```python
# Add to FastAPI middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

## Risk Matrix

| Threat | Likelihood | Impact | Risk Level | Status |
|--------|------------|--------|------------|--------|
| T1: Unauthorized Access | High | High | Critical | Needs Auth |
| T2: Data Injection | Medium | Medium | Medium | Mitigated |
| T3: Information Disclosure | Medium | High | High | Partial |
| T4: Denial of Service | Low | Medium | Low | Partial |
| T5: XSS | Low | Medium | Low | Mitigated |
| T6: CSRF | Low | Medium | Low | Partial |

## Production Checklist

- [ ] Implement authentication (OAuth2/OIDC)
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Configure security headers
- [ ] Set up log aggregation
- [ ] Implement backup strategy
- [ ] Add monitoring and alerting
- [ ] Conduct security review
- [ ] Set up WAF (optional)
