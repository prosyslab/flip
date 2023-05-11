# 1 "cilcode.tmp/ex4.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex4.c"
int main() {
  struct foo {
        int x; } foo;
  {
     struct foo {
        double d;
     };
     return foo.x;
  }
}
