# Notes on Compiling Guarded Atomic Actions

## Generate Ports
* add an `en` wire for each method
* add a `rdy` wire for each action method and connect to `firing`
* **TODO**: how should we wire up the return value?

## Generate Register Updates
* generate multiplexers for register updates from different rules
  and connect to the `firing` wires from the rules assuming that
  only one will ever be asserted in the same cycle
* any more efficient way to implement this?

## Generate Scheduler
* Input Wires: `can_fire` for each _internal_ rule
* Output Wires: `firing` for each _internal_ rule
* Information needed:
    * read sets
    * write sets
    * guards in order to determine mutual exclusion
    
## Generate Rule Body
* Input Wires:
    * all state elements, i.e. registers
    * wires from methods that are called (and not inlined)
* Output Wires:
    * updates to registers
    * wires to methods that are called (and not inlined)
* Information needed:
    * updates and methods of the rule
* Generates a wire for each update
    
## Generate Rule Guard
* Input Wires:
    * all state elements, i.e. registers
    * enable wires from methods that are called (and not inlined)
* Output Wires:
    * `can_fire` for this rule
* Information needed:
    * guard of rule and all methods called
