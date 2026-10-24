# Verifying HLS Designs

Verification is usually the most time-consuming part of an HLS-based flow, because a
design has to be checked at two levels: does the untimed C++ behave correctly, and does
the synthesized, cycle-accurate RTL behave the same way.

## C/RTL co-simulation

A common flow runs the same testbench twice: once against the original C++ function,
and once against the generated RTL through a simulator, feeding in the same inputs and
comparing outputs cycle by cycle where relevant. Mismatches usually point to either an
unsupported C++ construct, an incorrect directive, or a genuine bug that untimed C++
simulation didn't catch (for example, an array access that is fine in software but
violates a memory port's bandwidth in hardware).

## Common sources of C/RTL mismatch

- Uninitialized variables that behave deterministically in software but not in hardware.
- Floating point operations synthesized with different precision than expected.
- Race conditions introduced by pipelining that weren't visible in sequential C++ execution.
- Array partitioning or reshaping that changes access patterns in ways the testbench
  doesn't exercise.

## Regression testing for HLS flows

Because a single source change can affect scheduling, resource usage and timing all at
once, HLS teams typically run broad regression suites on every commit: functional
correctness (does the output match a reference), performance regression (did latency or
throughput get worse), and resource regression (did area or memory usage increase
unexpectedly). Automating this in CI, and making failures easy to triage, is a
significant part of maintaining a healthy HLS toolchain.
