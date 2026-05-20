# Northwind Robotics — laptop provisioning

New employees are issued a Northwind-managed laptop on their start date. Contractors may use their own hardware subject to the BYOD policy.

## Standard laptop options

- MacBook Pro 14" (M-series) — default for engineering and design
- ThinkPad X1 Carbon — default for general business use
- ThinkPad P-series — for engineering workloads requiring discrete GPU

Request alternative hardware via the IT self-service portal. Approval requires manager sign-off.

## Imaging and software

All managed laptops ship with the Northwind base image:
- OS: macOS 14 or Windows 11 Enterprise
- MDM agent (Jamf for Mac, Intune for Windows)
- EDR agent (CrowdStrike Falcon)
- Standard productivity suite (Microsoft 365)
- VPN client (GlobalConnect)

Do not disable or uninstall any agent. Doing so will trigger an automated alert and may result in the device being remotely locked.

## Returns

Laptops must be returned to IT within 5 business days of departure. Return shipping is arranged via the offboarding workflow.
