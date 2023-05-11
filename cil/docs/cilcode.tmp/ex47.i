# 1 "cilcode.tmp/ex47.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex47.c"
    static int bar(int x, char y) {
      return x + y;
    }


    int foo(int x, char y) __attribute__((alias("bar")));
