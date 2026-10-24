# High-Level Synthesis (HLS) Basics

High-Level Synthesis is the process of automatically converting an algorithm written in a
high-level language, typically C, C++ or SystemC, into a register-transfer-level (RTL)
hardware description such as Verilog or VHDL. Instead of hand-writing RTL, an engineer
describes the desired behavior in software, and the HLS tool explores scheduling,
resource allocation and binding decisions to produce hardware that meets timing, area
and throughput targets.

## Why teams use HLS

- **Faster iteration**: changing a loop bound or data type in C++ and re-running synthesis
  is much faster than re-writing RTL by hand.
- **Design space exploration**: the same source can be synthesized under different
  clock, area and latency constraints to compare trade-offs quickly.
- **Verification reuse**: a C++ testbench that validates the algorithm can often be reused
  to check the synthesized hardware via co-simulation.

## Core HLS concepts

- **Scheduling**: deciding which clock cycle each operation executes in.
- **Pipelining**: overlapping iterations of a loop so a new iteration can start before the
  previous one finishes, increasing throughput at the cost of area.
- **Resource sharing/binding**: mapping multiple operations onto a shared hardware unit
  (e.g. one multiplier used by several multiplications) to save area when throughput
  allows it.
- **Interface synthesis**: generating the hardware handshake (e.g. valid/ready signals)
  around a function's inputs and outputs so it can connect to the rest of a design.

## Directives and pragmas

Most HLS tools let engineers guide the synthesis process with directives placed in or
alongside the source code — for example marking a loop for pipelining, unrolling a loop
a fixed number of times, or partitioning an array across memory banks so multiple
elements can be accessed in the same cycle. Getting good results from HLS is often as
much about writing "synthesis-friendly" C++ and choosing the right directives as it is
about the algorithm itself.
