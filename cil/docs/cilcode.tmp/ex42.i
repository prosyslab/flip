# 1 "cilcode.tmp/ex42.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex42.c"
static void *jtab[2];
static int doit(int x){

  static int jtab_init = 0;
  if(!jtab_init) {
    jtab[0] = &&lbl1;
    jtab[1] = &&lbl2;
    jtab_init = 1;
  }
  goto *jtab[x];
lbl1:
  return 0;
lbl2:
  return 1;
}

int main(void){
  if (doit(0) != 0) exit(1);
  if (doit(1) != 1) exit(1);
  exit(0);
}
