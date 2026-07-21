# PB-100 Q2 Vendor Response Record 2026-07-21

Status: `RECEIVED / NON-QUALIFYING` — reroute through Infineon MyCases

## Traceability

- Infineon subject identifier: `IFX-260721-2228076`.
- CRM identifier: `CRM0032570008656`.
- Sender: `support@infineon.com`.
- Received: 2026-07-21 17:49 as displayed by the recipient mailbox; the
  message itself must remain the authoritative timestamp record.
- Original request:
  `PB-100-q2-vendor-support-request.md`.

## Response Disposition

Infineon did not provide a `VDS(t)` / `ID(t)` trajectory, a maximum
gate-discharge bound, a corner model, hot linear-mode SOA confirmation,
process/temperature/lot coverage, guardband, residual-current criterion, or an
FAE engineering statement. The response redirected the sender to Infineon's
other support options and urgent-support hotline.

This is a traceable vendor response, but it is not qualification evidence.
`Q2Q-010` through `Q2Q-015` remain open and are now `PENDING EMPIRICAL` under
the approved project qualification route; `Q2Q-016` records the non-qualifying
response identifiers; `Q2Q-017` becomes `PARALLEL REROUTE REQUIRED`.
PBREL-007 remains `Conditional`, aggregate PB-100 authorization remains
`BLOCKED`, and PB-100 board import remains prohibited.

## Required Reroute

1. Open an Infineon MyCases **Technical Support** case at
   <https://mycases.infineon.com>.
2. Reference both `IFX-260721-2228076` and `CRM0032570008656` and request
   routing to Automotive MOSFET Applications or product engineering.
3. Attach or paste the reviewed request and the qualification ledger. Ask for
   either the requested maximum-bound artifact or a written statement that
   Infineon cannot provide a production maximum for this use case.
4. Execute the separately approved component-level empirical route in
   `PB-100-q2-empirical-qualification-plan.md` without calling its results a
   manufacturer maximum. MyCases continues in parallel and may supersede the
   empirical route only if its artifact passes the same evidence review.

Infineon's official technical-support guidance identifies MyCases as its
direct channel to application engineers. Registration with a corporate-domain
email is recommended by Infineon but does not change the electrical acceptance
contract.

## Layout Boundary

Controlled FB-100 layout may continue under its independent `LAYOUT-ONLY`
authorization. This response does not authorize `PB-100.kicad_pcb`, PB-100
placement/routing, prototype manufacturing, production release, or field use.
