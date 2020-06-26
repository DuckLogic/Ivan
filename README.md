Ivan
====
A DSL for declaring C-Compatible FFI bindings.

## Features
- Can auto-generate C and Rust FFI declarations
- Support interfaces through the use of Virtual Method Tables
  - This is just a structure filled with function pointers

## Pointers
Ivan supports declaring four different types of pointers.
This clarifies the intended lifetime of the pointer.
None of these should be null unless explicitly stated in the type.

This pointer system is meerly a convention that reflects common use cases.
Unlike Rust's lifetime system it doesn't completely attempt to support all the
pointers that users will need. However, these are likely to work in at least 3/4 of your
use cases. This draws attention away from those common cases and towards
the more complex cases (managed with `&raw T` pointers).

1. Immutable pointers (`&Target`) - These are the default. They allow reading the data but not modifying it
   - When used in the argument to a function, they should be valid for the entire call
2. Mutable pointers (`&mut Target`) - Pointers that let you mutate data.
   - Like Rust's mutable references, they guarantee **exclusive** access
   - Violating this aliasing rule can trigger Undefined Behavior
   - Must also be valid for the lifetime of the call
3. Owned pointers (`&own Target`) - An owned pointer to a value
   - Like Rust's `Box<T>`, although without an automatic system for destructors
   - The caller has the right to free this data, mutate it, or use it in any other way
4. Raw pointers (`&raw Target`) - These are like C pointers. They have a complex
    lifetime which doesn't map to any of the other pointer types.
   - Ivan's pointer system is not designed for complete safety like Rust.
   - Raw pointers will be fairly common. They're just designed to draw a little more 
     attention than "normal" pointers.