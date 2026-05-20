# Northwind Robotics — multi-factor authentication

All Northwind systems require MFA. Enrolment happens during the first SSO login.

## Supported methods

- **Authenticator app** (preferred): Microsoft Authenticator, Google Authenticator, 1Password, or any TOTP-compatible app.
- **Hardware key**: YubiKey 5-series. Required for engineering staff with production access.
- **SMS**: available as a backup only. Not permitted as the sole MFA method.

## Lost device

If you lose your MFA device, contact the helpdesk immediately. The recovery flow requires identity verification with HR (employee badge photo and start date confirmation). Recovery typically takes 1 business day.

Do not share recovery codes with anyone, including IT staff. IT will never ask for your codes.

## Adding a second method

You can register up to three MFA methods at mfa.northwind-robotics.internal. We strongly recommend registering at least two — one authenticator app and one hardware key — so a lost phone does not lock you out.
