#ifndef IVAN_BASIC_H
#define IVAN_BASIC_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>

/**
 * This is a basic example of an ivan interface.
 */
typedef struct Basic {
    int64_t (*noArgs)();
    /**
     * Find the value by searching through the specified bytes.
     *
     * Bytes is a const '&' pointer, so you're expected not to mutate it.
     * It must be valid for the duration of the call.
     *
     * The output (if any) is placed in `result`.
     * It's a `&mut` pointer, so it's expected to be mutable
     * and have no-aliasing for the duration of the call.
     */
    bool (*findInBytes)(const char* bytes, size_t start, size_t* result);
    char* (*complexLifetime)();
} Basic;

/**
 * Here is another interface
 *
 * You can have multiple ones defined
 */
typedef struct Other {
    void (*test)(double d);
} Other;

typedef struct NoMethods {
} NoMethods;

/**
 * A type defined elsewhere in user code
 */
typedef struct Example Example;

void topLevel(Example e);

// wrappers

int64_t basic_noArgs(const Basic* vtable) {
    int64_t (*func_ptr)() = vtable->noArgs;
    assert(func_ptr != NULL);
    return (*func_ptr)();
}

bool basic_findInBytes(const Basic* vtable, const char* bytes, size_t start, size_t* result) {
    bool (*func_ptr)(const char* bytes, size_t start, size_t* result) = vtable->findInBytes;
    assert(func_ptr != NULL);
    return (*func_ptr)(bytes, start, result);
}

char* basic_complexLifetime(const Basic* vtable) {
    char* (*func_ptr)() = vtable->complexLifetime;
    assert(func_ptr != NULL);
    return (*func_ptr)();
}

void other_test(Other vtable, double d) {
    void (*func_ptr)(double d) = vtable.test;
    assert(func_ptr != NULL);
    (*func_ptr)(d);
}

#endif /* IVAN_BASIC_H */
