# 1 "cilcode.tmp/ex48.cil.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex48.cil.c"
# 1 "cilcode.tmp/ex48.c"
struct __anonstruct____missing_field_name_109580352 {
   int u ;
   int v ;
};
# 1 "cilcode.tmp/ex48.c"
struct __anonstruct____missing_field_name_829014867 {
   int y ;
   int z ;
   struct __anonstruct____missing_field_name_109580352 __annonCompField1 ;
};
# 1 "cilcode.tmp/ex48.c"
struct __anonstruct_a_84838698 {
   int x ;
   struct __anonstruct____missing_field_name_829014867 __annonCompField2 ;
};
# 1 "cilcode.tmp/ex48.c"
int main(void)
{
  struct __anonstruct_a_84838698 a ;

  {
# 10 "cilcode.tmp/ex48.c"
  return ((((a.x + a.__annonCompField2.y) + a.__annonCompField2.z) + a.__annonCompField2.__annonCompField1.u) + a.__annonCompField2.__annonCompField1.v);
}
}
