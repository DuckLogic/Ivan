#ifndef DUCKLOGIC_SHAPE_H
#define DUCKLOGIC_SHAPE_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>


/**
 * An opaque object managed by DuckVM.
 *
 * All pointers to these objects are garbage collected
 */
typedef struct DuckObject DuckObject;

/**
 * A legacy (reference-counted) python object
 */
typedef struct PyObject PyObject;

/**
 * The shape of a DuckObject
 */
@GenerateWrappers(prefix="object")
typedef struct PyShape {
    /*
     * View the underlying legacy representation of this DuckObject.
     * Return NULL if there is no associated PyObject*.
     *
     * This is an optional method - a NULL function means this shape
     * never has an associated PyObject
     */
    PyObject* (*view_legacy_repr)(const DuckObject* obj);
} PyShape;

// wrappers

/*
 * View the underlying legacy representation of this DuckObject.
 * Return NULL if there is no associated PyObject*.
 *
 * This is an optional method - a NULL function means this shape
 * never has an associated PyObject
 */
PyObject* object_view_legacy_repr(const PyShape* vtable, const DuckObject* obj) {
    bool (*func_ptr)(const DuckObject* obj) = vtable->view_legacy_repr;
    if (func_ptr == NULL) {
        return NULL;
    } else {
        return (*func_ptr)(obj);
    }
}

#endif /* DUCKLOGIC_SHAPE_H */
