# 1 "cilcode.tmp/ex45.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex45.c"
union u {
   int i;
   struct s {
      int i1, i2;
   } s;
};

union u x = (union u)6;

int main() {
  struct s y = {1, 2};
  union u z = (union u)y;
}
