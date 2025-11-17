# Admin Self-Registration Setup Guide

This guide explains how to set up and use the new invitation-based admin self-registration system with OTP verification and password reset functionality.

## Overview

The system now supports:
1. **Admin Invitations**: Existing admins can invite new admins via email
2. **OTP Verification**: Email verification codes for signup and password reset
3. **Secure Signup**: Invited admins can self-register with OTP verification
4. **Password Reset**: Users can reset their passwords using OTP codes

## Setup Instructions

### 1. Install Dependencies

Install the new Python packages:

```bash
cd fastapi-backend
pip install -r requirements.txt
```

New dependencies added:
- `aiosmtplib==3.0.1` - Async SMTP email sending
- `email-validator==2.1.0` - Email validation
- `slowapi==0.1.9` - Rate limiting (for future use)

### 2. Email Service Configuration

Configure your email service in the `.env` file:

```bash
# SMTP Configuration
SMTP_HOST=smtp.sendgrid.net          # Your SMTP server
SMTP_PORT=587                         # SMTP port (587 for TLS, 465 for SSL)
SMTP_USER=apikey                      # SMTP username
SMTP_PASSWORD=your_smtp_password      # SMTP password/API key
SMTP_USE_TLS=true                     # Use TLS (true/false)
EMAIL_FROM=noreply@yourdomain.com     # Sender email address

# Frontend URL (for invitation links)
FRONTEND_URL=http://localhost:8001    # Your frontend URL
```

### Email Service Options

#### Option A: SendGrid (Recommended for Production)
1. Create a SendGrid account at https://sendgrid.com
2. Create an API key
3. Configure:
   ```
   SMTP_HOST=smtp.sendgrid.net
   SMTP_USER=apikey
   SMTP_PASSWORD=<your_sendgrid_api_key>
   ```

#### Option B: AWS SES
1. Configure SES in AWS Console
2. Verify sender email
3. Configure:
   ```
   SMTP_HOST=email-smtp.us-east-1.amazonaws.com
   SMTP_USER=<ses_smtp_username>
   SMTP_PASSWORD=<ses_smtp_password>
   ```

#### Option C: Gmail (Development Only)
⚠️ **Not recommended for production**
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app_password>  # Use App Password, not regular password
```

#### Option D: Local Testing (No Email)
For development, if `SMTP_HOST=localhost`, the system will log emails to console instead of sending them.

### 3. Database Migration

Run the Alembic migration to create the new tables:

```bash
cd fastapi-backend
alembic upgrade head
```

This creates:
- `admin_invitations` table
- `otp_tokens` table

### 4. Start the Server

```bash
cd fastapi-backend
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Usage Guide

### Inviting a New Admin

**API Endpoint**: `POST /auth/admin/invite`

**Authentication**: Requires admin Bearer token

**Request**:
```json
{
  "email": "newadmin@example.com"
}
```

**Response**:
```json
{
  "message": "Invitation sent successfully",
  "email": "newadmin@example.com",
  "expires_at": "2025-01-24T12:00:00Z"
}
```

**Example using curl**:
```bash
curl -X POST http://localhost:8001/auth/admin/invite \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "newadmin@example.com"}'
```

The system will:
1. Create an invitation record
2. Send an email with a signup link
3. Link expires in 48 hours

### Admin Signup Flow

1. **Receive Invitation Email**
   - Admin receives email with signup link
   - Link format: `http://your-domain/dashboard/signup.html?token=<invitation_token>`

2. **Visit Signup Page**
   - Opens `signup.html` with invitation token
   - Email is pre-filled from invitation

3. **Verify Email (OTP)**
   - Click "Send Code" to receive OTP
   - Enter 6-digit code from email
   - Code expires in 10 minutes

4. **Complete Registration**
   - Enter full name
   - Enter password (min 8 chars, uppercase, lowercase, number)
   - Submit to create account

5. **Login**
   - Redirected to login page
   - Login with email and new password

### Password Reset Flow

1. **Request Reset**
   - On login page, click "Forgot password?"
   - Enter email address
   - System sends OTP code to email

2. **Enter OTP**
   - Check email for 6-digit code
   - Enter code when prompted

3. **Set New Password**
   - Enter new password (same requirements as signup)
   - Password is updated
   - Login with new password

### API Endpoints

#### Get Invitation Details
```
GET /auth/invitation/{token}
```
Returns invitation email and expiration date.

#### Send OTP
```
POST /auth/send-otp
Body: { "email": "user@example.com", "purpose": "signup" | "password_reset" }
```
Sends OTP code to email.

#### Verify OTP
```
POST /auth/verify-otp
Body: { "email": "user@example.com", "otp_code": "123456", "purpose": "signup" }
```
Verifies OTP code.

#### Complete Signup
```
POST /auth/signup
Body: { "invitation_token": "...", "full_name": "...", "password": "..." }
```
Creates admin account (requires verified OTP).

#### Forgot Password
```
POST /auth/forgot-password
Body: { "email": "user@example.com" }
```
Sends password reset OTP.

#### Reset Password
```
POST /auth/reset-password
Body: { "email": "user@example.com", "otp_code": "123456", "new_password": "..." }
```
Updates password (requires verified OTP).

## Security Features

### Rate Limiting
- **OTP Requests**: Max 3 requests per email per hour
- **OTP Verification**: Max 3 failed attempts before code is invalidated
- **OTP Expiration**: 10 minutes

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Security Best Practices
- OTP codes are hashed before storage (like passwords)
- Invitation tokens are cryptographically secure random strings
- Email enumeration prevention (password reset doesn't reveal if email exists)
- Invitations expire after 48 hours
- Single-use invitation tokens

## Troubleshooting

### Emails Not Sending

1. **Check SMTP Configuration**
   - Verify credentials in `.env`
   - Test with `telnet smtp.sendgrid.net 587` (or your SMTP host)

2. **Check Logs**
   - Look for email errors in application logs
   - In dev mode with `SMTP_HOST=localhost`, emails are logged to console

3. **Firewall/Network**
   - Ensure SMTP port (587/465) is not blocked
   - Check if VPN/proxy is interfering

### OTP Not Received

1. **Check Spam Folder**
   - Email might be filtered

2. **Rate Limiting**
   - Wait 1 hour if rate limit was exceeded
   - Check logs for rate limit messages

3. **Email Service Status**
   - Verify email service is operational
   - Check SendGrid/AWS SES status page

### Invitation Token Invalid

1. **Check Expiration**
   - Invitations expire after 48 hours
   - Request a new invitation

2. **Already Used**
   - Each invitation can only be used once
   - Request a new invitation if account already created

### Signup Fails

1. **OTP Not Verified**
   - Must verify OTP before completing signup
   - OTP expires after 10 minutes

2. **Password Requirements**
   - Ensure password meets all requirements
   - Check error message for specific requirement

3. **User Already Exists**
   - Email might already be registered
   - Try logging in instead

## Frontend Integration

### Dashboard Admin UI (Future Enhancement)

You can add an admin UI to send invitations from the dashboard:

```javascript
// Example: Send invitation from dashboard
async function inviteAdmin(email) {
    const token = sessionStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/auth/admin/invite`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
    });
    return response.json();
}
```

## Migration from Old System

If you have existing admins created via scripts:

1. **Keep Scripts Working**
   - Old registration scripts still work
   - Bootstrap registration (first user) still creates admin

2. **Gradual Migration**
   - New admins use invitation system
   - Existing admins continue using their accounts
   - No action needed for existing users

3. **Remove Bootstrap Warning** (Optional)
   - After first admin is created, you can disable bootstrap registration
   - Modify `/auth/register` endpoint if desired

## Testing

### Test Invitation Flow

1. **Create Admin Token** (if needed):
   ```bash
   python fastapi-backend/scripts/get_admin_token.py --email admin@test.com --password testpass
   ```

2. **Send Invitation**:
   ```bash
   curl -X POST http://localhost:8001/auth/admin/invite \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{"email": "newadmin@test.com"}'
   ```

3. **Check Email** (or logs if using localhost SMTP)

4. **Complete Signup** via `signup.html?token=<token>`

### Test Password Reset

1. Request reset via login page "Forgot password?" link
2. Check email for OTP
3. Enter OTP and new password
4. Login with new password

## Production Checklist

- [ ] Configure production SMTP service (SendGrid/AWS SES)
- [ ] Set `EMAIL_FROM` to verified sender address
- [ ] Set `FRONTEND_URL` to production domain
- [ ] Run database migrations
- [ ] Test invitation flow end-to-end
- [ ] Test password reset flow
- [ ] Monitor email delivery rates
- [ ] Set up email service alerts
- [ ] Review and adjust rate limits if needed
- [ ] Update documentation for your team

## Support

For issues or questions:
1. Check application logs for errors
2. Verify email service configuration
3. Test with localhost SMTP first (development)
4. Review security best practices

