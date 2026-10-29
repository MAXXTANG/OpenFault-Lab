# Working on OpenFault Lab

- Keep this repository independent. Do not search, read, copy, or import unrelated private projects, protocols, customer data, or sibling workspace directories.
- Keep application contact details, shipping addresses, phone numbers, credentials, and submission screenshots out of the repository.
- Begin with feasibility research. Do not generate substantial STM32 firmware before verifying the exact board, MCU peripherals, pins, toolchain, and HAL version against official documentation.
- Separate verified facts, design decisions, estimates, and untested assumptions. Cite the official source and version for hardware and API claims.
- Never invent HAL APIs or claim builds or hardware tests were run when they were not. Update docs/VALIDATION.md with commands, versions, and evidence when verification actually occurs.
- Use guarded, low-voltage bench equipment and safe controlled operating variations. Do not propose destructive fault injection or mains wiring.
- Describe unconfirmed conditions as anomalies rather than diagnosed faults. Keep training/test splits separated by recording session or device.
- Normal monitoring must not store or transmit raw audio. Review permissions and dataset licensing before publishing recordings.
- Original code and documentation use MIT. Preserve and identify third-party licenses; dataset licensing is separate.
- Use English for public documentation and code. Explain work to the maintainer in Traditional Chinese (Taiwan).
