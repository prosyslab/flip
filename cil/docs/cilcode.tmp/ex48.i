# 1 "cilcode.tmp/ex48.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex48.c"
int main(void) {
# 1 "cilcode.tmp/ex48.c"
struct {
  int x;
  struct {
     int y, z;
     struct {
       int u, v;
     };
 };
} a;
return a.x + a.y + a.z + a.u + a.v;
}
