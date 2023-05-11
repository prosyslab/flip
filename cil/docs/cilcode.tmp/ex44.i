# 1 "cilcode.tmp/ex44.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex44.c"
extern inline foo(void) { return 1; }
int firstuse(void) { return foo(); }


int foo(void) { return 2; }

int main() {
    return foo() + firstuse();
}
