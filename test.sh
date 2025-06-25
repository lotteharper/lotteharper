#!/bin/bash
string="example.string+with.dots"
result="${string%%+*}"
echo "$result"  # Output: example
