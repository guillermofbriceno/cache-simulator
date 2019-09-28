# cache-simulator

A cache simulator capable of calcuating miss rates on an address trace with given associativity levels, block and cache sizes, and with a least-recently-used replacement policy. Python 3.6 required.

Author: Guillermo Briceno.

---

# Usage

`./cache-sim.py <options> -trace <tracefile>`

Order does not matter. Split cache is specified with separate instruction cache and data cache sizes, block sizes, and associativity levels:

`./cache-sim.py -isize 32768 -ibsize 32 -iassoc 4 -dsize 32768 -dbsize 32 -dassoc 4 -trace <tracefile>`

Specifies an instruction cache and data cache size of 32768 bytes, both with a block size of 32 bytes and associativity level of 4.

Unified cache example:

`./cache-sim.py -usize 32768 -ubsize 32 -uassoc 4 -trace <tracefile>`

The script will output the number of hits, misses as well as their rates onto the terminal.
