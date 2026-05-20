# Northwind Robotics — VPN access guide

All employees use the Northwind GlobalConnect VPN to access internal systems while working remotely.

## Initial setup

1. Download the GlobalConnect client from the IT self-service portal.
2. Enter the gateway address: `vpn.northwind-robotics.internal`.
3. Authenticate with your Northwind SSO credentials.
4. The first connection will prompt you to enrol your device with MDM. Approve the prompt.

## Troubleshooting

If the client reports "authentication failed", first verify SSO works at sso.northwind-robotics.internal. If SSO works but VPN does not, your account may not be in the `vpn-users` group. Contact the helpdesk.

If the client connects but you cannot reach internal sites, check that split tunneling is disabled in client settings. Northwind requires full-tunnel mode for all traffic.

## Password reset

Self-service password reset is available at password.northwind-robotics.internal. You will need access to your registered MFA device.
