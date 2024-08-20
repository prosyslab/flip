let preamble src_dir mode =
  String.concat ""
    ([
       "/* COVERAGE :: INSTRUMENTATION :: START */\n";
       "typedef struct _IO_FILE FILE;\n";
       "typedef long __off_t;\n";
       "typedef unsigned long size_t;\n";
       "struct _IO_FILE *__inst_stream ;\n";
       "int __inst_stream_fd;\n";
       "int __inst_mmap_size = 0;\n";
       "char *__inst_mmap;\n";
       "char *__env_signal;\n";
       "extern FILE *fopen(char const   * __restrict  __filename , char \
        const   * __restrict  __modes ) ;\n";
       "extern int fclose(FILE *__stream ) ;\n";
       "extern int open (const char *__file, int __oflag, ...);\n";
       "extern void *mmap (void *__addr, size_t __len, int __prot, int \
        __flags, int __fd, __off_t __offset);\n";
       "extern int ftruncate (int __fd, __off_t __length);\n";
       "extern char *getenv (const char *__name);\n";
       "static void coverage_ctor (void) __attribute__ ((constructor));\n";
       "static void coverage_ctor (void) {\n";
     ]
    @ (if mode = "output" then
       [ "__inst_stream = fopen(\"" ^ src_dir ^ "/output.txt\", \"a\");\n" ]
      else
        [
          (if
           !Cmdline.instrument = Cmdline.ErrorInject
           || !Cmdline.instrument = Cmdline.ErrorCoverage
          then "  __env_signal = getenv(\"__ENV_SIGNAL\");\n"
          else "");
          "  int pid = getpid();\n";
          "  char filename[64];\n";
          "  sprintf(filename, \"" ^ src_dir ^ "/coverage_data" ^ "/tmp/" ^ mode
          ^ "-%d.txt\", pid);\n";
          "  __inst_stream = fopen(filename, \"a\");\n";
          (if !Cmdline.mmap then
           "  __inst_stream_fd = open(filename, 66);\n"
           ^ "  ftruncate(__inst_stream_fd, 1999999);\n"
           ^ "  __inst_mmap = (char *)mmap((void *)0, 1999999, 3, 1, \
              __inst_stream_fd, 0);\n"
          else "");
        ])
    @ [
        "}\n";
        "static void coverage_dtor (void) __attribute__ ((destructor));\n";
        "static void coverage_dtor (void) {\n";
        "  fclose(__inst_stream);\n";
        "}\n";
        (if !Cmdline.mmap then
         "void append_coverage (int check_var, const char *cov_data, int \
          cov_data_len) {\n" ^ "  if (!check_var) {\n"
         ^ "    strcpy(__inst_mmap, cov_data);\n"
         ^ "    __inst_mmap += cov_data_len;\n" ^ "  }\n" ^ "}\n"
        else "");
        "/* COVERAGE :: INSTRUMENTATION :: END */\n";
      ])

let found_type = ref None
let found_gvar = ref None

class findTypeVisitor name =
  object
    inherit Cil.nopCilVisitor

    method! vglob g =
      match g with
      | GCompTag (ci, _) ->
          if ci.Cil.cname = name then found_type := Some ci;
          SkipChildren
      | _ -> SkipChildren
  end

class findGVarVisitor name =
  object
    inherit Cil.nopCilVisitor

    method! vglob g =
      match g with
      | GVarDecl (vi, _) ->
          if vi.Cil.vname = name then found_gvar := Some vi;
          SkipChildren
      | _ -> SkipChildren
  end

let append_constructor work_dir filename mode =
  let read_whole_file filename =
    let ch = open_in filename in
    let s = really_input_string ch (in_channel_length ch) in
    close_in ch;
    s
  in
  let code = read_whole_file filename in
  if
    String.length code > 42
    && String.equal (String.sub code 0 42)
         "/* COVERAGE :: INSTRUMENTATION :: START */"
  then ()
  else
    let instr_c_code = preamble work_dir mode ^ read_whole_file filename in
    let oc = open_out filename in
    Printf.fprintf oc "%s" instr_c_code;
    close_out oc

module Coverage = struct
  module VarSet = Set.Make (String)

  (* let glob_var_whole_set = ref VarSet.empty *)

  let location_of_instr = function
    | Cil.Set (_, _, l) | Cil.Call (_, _, _, l) | Cil.Asm (_, _, _, _, _, l) ->
        l

  let printf_of printf stream loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var printf, Cil.NoOffset),
        [
          Cil.Lval (Cil.Var stream, Cil.NoOffset);
          Cil.Const (Cil.CStr "%s:%d\n");
          Cil.Const (Cil.CStr loc.Cil.file);
          Cil.integer loc.Cil.line;
        ],
        loc )

  let flush_of flush stream loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var flush, Cil.NoOffset),
        [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
        loc )

  let printf_value_of printf stream loc name exp =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var printf, Cil.NoOffset),
        [
          Cil.Lval (Cil.Var stream, Cil.NoOffset);
          Cil.Const (Cil.CStr "%s:%d\n");
          Cil.Const (Cil.CStr name);
          exp;
        ],
        loc )

  let flush_value_of flush stream loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var flush, Cil.NoOffset),
        [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
        loc )

  let strcpy_of strcpy mmap loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
        [
          Cil.Lval (Cil.Var mmap, Cil.NoOffset);
          Cil.Const
            (Cil.CStr
               (loc.Cil.file ^ ":" ^ (loc.Cil.line |> string_of_int) ^ "\n"));
        ],
        loc )

  let ftruncate_of ftruncate fd mmap_size loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var ftruncate, Cil.NoOffset),
        [
          Cil.Lval (Cil.Var fd, Cil.NoOffset);
          Cil.Lval (Cil.Var mmap_size, Cil.NoOffset);
        ],
        loc )

  let append_coverage_of append_coverage check_var loc =
    Cil.Call
      ( None,
        Cil.Lval (Cil.Var append_coverage, Cil.NoOffset),
        [
          Cil.Lval (Cil.Var check_var, Cil.NoOffset);
          Cil.Const
            (Cil.CStr
               (loc.Cil.file ^ ":" ^ (loc.Cil.line |> string_of_int) ^ "\n"));
          Cil.Const
            (Cil.CInt64
               ( (loc.Cil.file |> String.length)
                 + (loc.Cil.line |> string_of_int |> String.length)
                 + 2
                 |> Int64.of_int,
                 Cil.IInt,
                 None ));
        ],
        loc )

  class instrumentVisitor printf flush stream strcpy mmap mmap_size stream_fd
    ftruncate append_coverage glob_check_vars =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        if fd.Cil.svar.vname = "bugzoo_ctor" then SkipChildren
        else if !Cmdline.fun_level then (
          (* let funname = fd.svar.vname in *)
          let funloc = fd.svar.vdecl in
          let call =
            (if !Cmdline.mmap then strcpy_of strcpy mmap funloc
            else printf_of printf stream funloc)
            |> Cil.mkStmtOneInstr
          in
          let mmap_inc =
            Cil.Set
              ( (Cil.Var mmap, Cil.NoOffset),
                Cil.BinOp
                  ( Cil.PlusPI,
                    Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                    Cil.Const
                      (Cil.CInt64
                         ( (funloc.file |> String.length)
                           + (funloc.Cil.line |> string_of_int |> String.length)
                           + 2
                           |> Int64.of_int,
                           Cil.IInt,
                           None )),
                    Cil.intType ),
                funloc )
            |> Cil.mkStmtOneInstr
          in
          (* let check_var_name = "__funvar_" ^ funname in *)
          let check_var_name =
            "__"
            ^ (funloc.file
              |> String.map (fun c ->
                     if c = '/' || c = '.' || c = '-' then '_' else c))
            ^ "_"
            ^ (funloc.line |> string_of_int)
          in
          let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
          if !Cmdline.mmap then
            glob_check_vars := VarSet.add check_var_name !glob_check_vars;
          let var_used =
            Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, funloc)
            |> Cil.mkStmtOneInstr
          in
          let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
          let call =
            if !Cmdline.mmap then
              Cil.If
                ( Cil.UnOp
                    ( Cil.LNot,
                      Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                      Cil.intType ),
                  [ call; mmap_inc; var_used ]
                  |> Cil.compactStmts |> Cil.mkBlock,
                  empty_block,
                  funloc )
              |> Cil.mkStmt
            else call
          in
          let flush = flush_of flush stream funloc |> Cil.mkStmtOneInstr in
          if !Cmdline.mmap then fd.sbody.bstmts <- call :: fd.sbody.bstmts
          else if !Cmdline.no_seg then
            fd.sbody.bstmts <- call :: fd.sbody.bstmts
          else fd.sbody.bstmts <- call :: flush :: fd.sbody.bstmts;
          SkipChildren)
        else DoChildren

      method! vblock blk =
        if !Cmdline.block_level then (
          let block_loc =
            if blk.bstmts = [] then Cil.locUnknown
            else Cil.get_stmtLoc (blk.bstmts |> List.hd).skind
          in
          if block_loc.line < 0 || block_loc = Cil.locUnknown then
            Cil.DoChildren
          else
            let call =
              (if !Cmdline.mmap then
               Cil.Call
                 ( None,
                   Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                   [
                     Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                     Cil.Const
                       (Cil.CStr
                          (block_loc.Cil.file ^ ":"
                          ^ (block_loc.Cil.line |> string_of_int)
                          ^ "\n"));
                   ],
                   Cil.locUnknown )
              else
                Cil.Call
                  ( None,
                    Cil.Lval (Cil.Var printf, Cil.NoOffset),
                    [
                      Cil.Lval (Cil.Var stream, Cil.NoOffset);
                      Cil.Const (Cil.CStr "%s:%d\n");
                      Cil.Const (Cil.CStr block_loc.Cil.file);
                      Cil.integer block_loc.Cil.line;
                    ],
                    Cil.locUnknown ))
              |> Cil.mkStmtOneInstr
            in
            let mmap_inc =
              Cil.Set
                ( (Cil.Var mmap, Cil.NoOffset),
                  Cil.BinOp
                    ( Cil.PlusPI,
                      Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                      Cil.Const
                        (Cil.CInt64
                           ( (block_loc.file |> String.length)
                             + (block_loc.Cil.line |> string_of_int
                              |> String.length)
                             + 2
                             |> Int64.of_int,
                             Cil.IInt,
                             None )),
                      Cil.intType ),
                  Cil.locUnknown )
              |> Cil.mkStmtOneInstr
            in
            let check_var_name =
              "__"
              ^ (block_loc.file
                |> String.map (fun c ->
                       if c = '/' || c = '.' || c = '-' then '_' else c))
              ^ "_"
              ^ (block_loc.line |> string_of_int)
            in
            let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
            if !Cmdline.mmap then
              glob_check_vars := VarSet.add check_var_name !glob_check_vars;
            let var_used =
              Cil.Set
                ((Cil.Var check_var, Cil.NoOffset), Cil.one, Cil.locUnknown)
              |> Cil.mkStmtOneInstr
            in
            let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
            let call =
              if !Cmdline.mmap then
                Cil.If
                  ( Cil.UnOp
                      ( Cil.LNot,
                        Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                        Cil.intType ),
                    [ call; mmap_inc; var_used ]
                    |> Cil.compactStmts |> Cil.mkBlock,
                    empty_block,
                    Cil.locUnknown )
                |> Cil.mkStmt
              else call
            in
            let fflush =
              Cil.Call
                ( None,
                  Cil.Lval (Cil.Var flush, Cil.NoOffset),
                  [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                  Cil.locUnknown )
              |> Cil.mkStmtOneInstr
            in
            if !Cmdline.mmap then blk.bstmts <- call :: blk.bstmts
            else if !Cmdline.no_seg then blk.bstmts <- call :: blk.bstmts
            else blk.bstmts <- call :: fflush :: blk.bstmts;
            Cil.DoChildren)
        else Cil.DoChildren

      method! vstmt stmt =
        let loc = Cil.get_stmtLoc stmt.Cil.skind in
        if
          (not (String.ends_with ~suffix:".c" loc.file))
          || loc.line < 0 || loc = Cil.locUnknown
        then Cil.DoChildren
        else if !Cmdline.block_level then
          let action stmt =
            match stmt.Cil.skind with
            | If (exp, thenb, elseb, l) ->
                let thenb_loc =
                  if thenb.bstmts = [] then Cil.locUnknown
                  else Cil.get_stmtLoc (thenb.bstmts |> List.hd).skind
                in
                (if thenb_loc.line < 0 || thenb_loc = Cil.locUnknown then ()
                else
                  let call =
                    (if !Cmdline.mmap then
                     Cil.Call
                       ( None,
                         Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                         [
                           Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                           Cil.Const
                             (Cil.CStr
                                (thenb_loc.Cil.file ^ ":"
                                ^ (thenb_loc.Cil.line |> string_of_int)
                                ^ "\n"));
                         ],
                         Cil.locUnknown )
                    else
                      Cil.Call
                        ( None,
                          Cil.Lval (Cil.Var printf, Cil.NoOffset),
                          [
                            Cil.Lval (Cil.Var stream, Cil.NoOffset);
                            Cil.Const (Cil.CStr "%s:%d\n");
                            Cil.Const (Cil.CStr thenb_loc.Cil.file);
                            Cil.integer thenb_loc.Cil.line;
                          ],
                          Cil.locUnknown ))
                    |> Cil.mkStmtOneInstr
                  in
                  let mmap_inc =
                    Cil.Set
                      ( (Cil.Var mmap, Cil.NoOffset),
                        Cil.BinOp
                          ( Cil.PlusPI,
                            Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                            Cil.Const
                              (Cil.CInt64
                                 ( (thenb_loc.file |> String.length)
                                   + (thenb_loc.Cil.line |> string_of_int
                                    |> String.length)
                                   + 2
                                   |> Int64.of_int,
                                   Cil.IInt,
                                   None )),
                            Cil.intType ),
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  let check_var_name =
                    "__"
                    ^ (thenb_loc.file
                      |> String.map (fun c ->
                             if c = '/' || c = '.' || c = '-' then '_' else c))
                    ^ "_"
                    ^ (thenb_loc.line |> string_of_int)
                  in
                  let check_var =
                    Cil.makeGlobalVar check_var_name Cil.intType
                  in
                  if !Cmdline.mmap then
                    glob_check_vars :=
                      VarSet.add check_var_name !glob_check_vars;
                  let var_used =
                    Cil.Set
                      ( (Cil.Var check_var, Cil.NoOffset),
                        Cil.one,
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
                  let call =
                    if !Cmdline.mmap then
                      Cil.If
                        ( Cil.UnOp
                            ( Cil.LNot,
                              Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                              Cil.intType ),
                          [ call; mmap_inc; var_used ]
                          |> Cil.compactStmts |> Cil.mkBlock,
                          empty_block,
                          Cil.locUnknown )
                      |> Cil.mkStmt
                    else call
                  in
                  let fflush =
                    Cil.Call
                      ( None,
                        Cil.Lval (Cil.Var flush, Cil.NoOffset),
                        [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  if !Cmdline.mmap then thenb.bstmts <- call :: thenb.bstmts
                  else if !Cmdline.no_seg then
                    thenb.bstmts <- call :: thenb.bstmts
                  else thenb.bstmts <- call :: fflush :: thenb.bstmts);
                let elseb_loc =
                  if elseb.bstmts = [] then Cil.locUnknown
                  else Cil.get_stmtLoc (elseb.bstmts |> List.hd).skind
                in
                (if elseb_loc.line < 0 || elseb_loc = Cil.locUnknown then ()
                else
                  let call =
                    (if !Cmdline.mmap then
                     Cil.Call
                       ( None,
                         Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                         [
                           Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                           Cil.Const
                             (Cil.CStr
                                (elseb_loc.Cil.file ^ ":"
                                ^ (elseb_loc.Cil.line |> string_of_int)
                                ^ "\n"));
                         ],
                         Cil.locUnknown )
                    else
                      Cil.Call
                        ( None,
                          Cil.Lval (Cil.Var printf, Cil.NoOffset),
                          [
                            Cil.Lval (Cil.Var stream, Cil.NoOffset);
                            Cil.Const (Cil.CStr "%s:%d\n");
                            Cil.Const (Cil.CStr elseb_loc.Cil.file);
                            Cil.integer elseb_loc.Cil.line;
                          ],
                          Cil.locUnknown ))
                    |> Cil.mkStmtOneInstr
                  in
                  let mmap_inc =
                    Cil.Set
                      ( (Cil.Var mmap, Cil.NoOffset),
                        Cil.BinOp
                          ( Cil.PlusPI,
                            Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                            Cil.Const
                              (Cil.CInt64
                                 ( (elseb_loc.file |> String.length)
                                   + (elseb_loc.Cil.line |> string_of_int
                                    |> String.length)
                                   + 2
                                   |> Int64.of_int,
                                   Cil.IInt,
                                   None )),
                            Cil.intType ),
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  let check_var_name =
                    "__"
                    ^ (elseb_loc.file
                      |> String.map (fun c ->
                             if c = '/' || c = '.' || c = '-' then '_' else c))
                    ^ "_"
                    ^ (elseb_loc.line |> string_of_int)
                  in
                  let check_var =
                    Cil.makeGlobalVar check_var_name Cil.intType
                  in
                  if !Cmdline.mmap then
                    glob_check_vars :=
                      VarSet.add check_var_name !glob_check_vars;
                  let var_used =
                    Cil.Set
                      ( (Cil.Var check_var, Cil.NoOffset),
                        Cil.one,
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
                  let call =
                    if !Cmdline.mmap then
                      Cil.If
                        ( Cil.UnOp
                            ( Cil.LNot,
                              Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                              Cil.intType ),
                          [ call; mmap_inc; var_used ]
                          |> Cil.compactStmts |> Cil.mkBlock,
                          empty_block,
                          Cil.locUnknown )
                      |> Cil.mkStmt
                    else call
                  in
                  let fflush =
                    Cil.Call
                      ( None,
                        Cil.Lval (Cil.Var flush, Cil.NoOffset),
                        [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                        Cil.locUnknown )
                    |> Cil.mkStmtOneInstr
                  in
                  if !Cmdline.mmap then elseb.bstmts <- call :: elseb.bstmts
                  else if !Cmdline.no_seg then
                    elseb.bstmts <- call :: elseb.bstmts
                  else elseb.bstmts <- call :: fflush :: elseb.bstmts);
                stmt.skind <- Cil.If (exp, thenb, elseb, l);
                let call =
                  if !Cmdline.mmap then
                    strcpy_of strcpy mmap loc |> Cil.mkStmtOneInstr
                  else printf_of printf stream loc |> Cil.mkStmtOneInstr
                in
                let mmap_inc =
                  Cil.Set
                    ( (Cil.Var mmap, Cil.NoOffset),
                      Cil.BinOp
                        ( Cil.PlusPI,
                          Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                          Cil.Const
                            (Cil.CInt64
                               ( (loc.Cil.file |> String.length)
                                 + (loc.Cil.line |> string_of_int
                                  |> String.length)
                                 + 2
                                 |> Int64.of_int,
                                 Cil.IInt,
                                 None )),
                          Cil.intType ),
                      loc )
                  |> Cil.mkStmtOneInstr
                in
                let check_var_name =
                  "__"
                  ^ (loc.file
                    |> String.map (fun c ->
                           if c = '/' || c = '.' || c = '-' then '_' else c))
                  ^ "_"
                  ^ (loc.line |> string_of_int)
                in
                let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
                if !Cmdline.mmap && loc.Cil.line >= 0 then
                  glob_check_vars := VarSet.add check_var_name !glob_check_vars;
                let var_used =
                  Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                  |> Cil.mkStmtOneInstr
                in
                let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
                let call =
                  if !Cmdline.mmap then
                    Cil.If
                      ( Cil.UnOp
                          ( Cil.LNot,
                            Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                            Cil.intType ),
                        [ call; mmap_inc; var_used ]
                        |> Cil.compactStmts |> Cil.mkBlock,
                        empty_block,
                        loc )
                    |> Cil.mkStmt
                  else call
                in
                let fflush = flush_of flush stream loc |> Cil.mkStmtOneInstr in
                let result =
                  if !Cmdline.mmap then [ stmt; call ]
                  else if !Cmdline.no_seg then [ stmt; call; fflush ]
                  else [ stmt; call ]
                in
                Cil.Block (result |> Cil.mkBlock) |> Cil.mkStmt
            | _ -> stmt
          in
          Cil.ChangeDoChildrenPost (stmt, action)
        else
          let action s =
            let call =
              if !Cmdline.mmap then
                strcpy_of strcpy mmap loc |> Cil.mkStmtOneInstr
              else printf_of printf stream loc |> Cil.mkStmtOneInstr
            in
            let mmap_inc =
              Cil.Set
                ( (Cil.Var mmap, Cil.NoOffset),
                  Cil.BinOp
                    ( Cil.PlusPI,
                      Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                      Cil.Const
                        (Cil.CInt64
                           ( (loc.Cil.file |> String.length)
                             + (loc.Cil.line |> string_of_int |> String.length)
                             + 2
                             |> Int64.of_int,
                             Cil.IInt,
                             None )),
                      Cil.intType ),
                  loc )
              |> Cil.mkStmtOneInstr
            in
            let check_var_name =
              "__"
              ^ (loc.file
                |> String.map (fun c ->
                       if c = '/' || c = '.' || c = '-' then '_' else c))
              ^ "_"
              ^ (loc.line |> string_of_int)
            in
            let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
            if !Cmdline.mmap && loc.Cil.line >= 0 then
              glob_check_vars := VarSet.add check_var_name !glob_check_vars;
            let var_used =
              Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
              |> Cil.mkStmtOneInstr
            in
            let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
            let call =
              if !Cmdline.mmap then
                Cil.If
                  ( Cil.UnOp
                      ( Cil.LNot,
                        Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                        Cil.intType ),
                    [ call; mmap_inc; var_used ]
                    |> Cil.compactStmts |> Cil.mkBlock,
                    empty_block,
                    loc )
                |> Cil.mkStmt
              else call
            in
            let result =
              if (not !Cmdline.no_seg) && !Cmdline.mmap then [ call; s ]
              else if (not !Cmdline.no_seg) && not !Cmdline.mmap then
                let flush = flush_of flush stream loc |> Cil.mkStmtOneInstr in
                [ call; flush; s ]
              else if !Cmdline.mmap then [ call; s ]
              else [ call; s ]
            in
            Cil.Block (result |> Cil.mkBlock) |> Cil.mkStmt
          in
          Cil.ChangeDoChildrenPost (stmt, action)

      method! vinst instr =
        let action is =
          if !Cmdline.block_level then is
          else
            match is with
            | [ i ] ->
                let loc = Cil.get_instrLoc i in
                if
                  (not (String.ends_with ~suffix:".c" loc.file))
                  || loc.Cil.line < 0
                then [ i ]
                else
                  let check_var_name =
                    "__"
                    ^ (loc.file
                      |> String.map (fun c ->
                             if c = '/' || c = '.' || c = '-' then '_' else c))
                    ^ "_"
                    ^ (loc.line |> string_of_int)
                  in
                  let check_var =
                    Cil.makeGlobalVar check_var_name Cil.intType
                  in
                  if !Cmdline.mmap && loc.Cil.line >= 0 then
                    glob_check_vars :=
                      VarSet.add check_var_name !glob_check_vars;
                  let call =
                    if !Cmdline.mmap then
                      append_coverage_of append_coverage check_var loc
                    else printf_of printf stream loc
                  in
                  let var_used =
                    Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                  in
                  if (not !Cmdline.no_seg) && !Cmdline.mmap then
                    [ call; var_used; i ]
                  else if (not !Cmdline.no_seg) && not !Cmdline.mmap then
                    let flush = flush_of flush stream loc in
                    [ call; flush; i ]
                  else if !Cmdline.mmap then [ call; var_used; i ]
                  else [ call; i ]
            | _ -> is
        in
        Cil.ChangeDoChildrenPost ([ instr ], action)
    end

  let instrument work_dir origin_file_opt pt_file =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let _ = print_endline pt_file in
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Instrument Coverage %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let printf =
          Cil.findOrCreateFunc cil "fprintf"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("stream", fileptr, []); ("format", Cil.charPtrType, []) ],
                 true,
                 [] ))
        in
        let flush =
          Cil.findOrCreateFunc cil "fflush"
            (Cil.TFun (Cil.voidType, Some [ ("stream", fileptr, []) ], false, []))
        in
        let append_coverage =
          Cil.findOrCreateFunc cil "append_coverage"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [
                     ("check_var", Cil.intType, []);
                     ("cov_data", Cil.charConstPtrType, []);
                     ("cov_data_len", Cil.intType, []);
                   ],
                 false,
                 [] ))
        in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        let mmap = Cil.makeGlobalVar "__inst_mmap" Cil.charPtrType in
        let mmap_size = Cil.makeGlobalVar "__inst_mmap_size" Cil.intType in
        let stream_fd = Cil.makeGlobalVar "__inst_stream_fd" Cil.intType in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        cil.globals <- Cil.GVarDecl (mmap, Cil.locUnknown) :: cil.globals;
        cil.globals <- Cil.GVarDecl (mmap_size, Cil.locUnknown) :: cil.globals;
        cil.globals <- Cil.GVarDecl (stream_fd, Cil.locUnknown) :: cil.globals;
        let strcpy =
          Cil.findOrCreateFunc cil "strcpy"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [
                     ("dest", Cil.charPtrType, []);
                     ("src", Cil.charConstPtrType, []);
                   ],
                 false,
                 [] ))
        in
        let ftruncate =
          Cil.findOrCreateFunc cil "ftruncate"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("__fd", Cil.intType, []); ("__length", Cil.longType, []) ],
                 false,
                 [] ))
        in
        let glob_check_vars = ref VarSet.empty in
        Cil.visitCilFile
          (new instrumentVisitor
             printf flush stream strcpy mmap mmap_size stream_fd ftruncate
             append_coverage glob_check_vars)
          cil;
        VarSet.iter
          (fun v ->
            let tmp_glob_var = Cil.makeGlobalVar v Cil.intType in
            tmp_glob_var.vstorage <- Cil.Static;
            cil.globals <-
              Cil.GVar
                ( tmp_glob_var,
                  { init = Some (Cil.SingleInit Cil.zero) },
                  Cil.locUnknown )
              :: cil.globals)
          !glob_check_vars;
        Unix.system
          ("cp " ^ origin_file ^ " "
          ^ Filename.remove_extension origin_file
          ^ ".origin.c")
        |> ignore;
        (if List.mem (Filename.basename origin_file) [ "proc_open.c"; "cast.c" ]
        then ()
        else
          let oc = open_out origin_file in
          Cil.dumpFile !Cil.printerForMaincil oc "" cil;
          close_out oc);
        if
          List.mem
            (Unix.realpath origin_file)
            [
              "/experiment/src/gzip.c";
              "/experiment/src/libtiff/tif_unix.c";
              "/experiment/src/libtiff/mkg3states.c";
              "/experiment/src/src/http_auth.c";
              "/experiment/src/main/main.c";
              "/experiment/src/main.c";
              "/experiment/src/Modules/main.c";
              "/experiment/src/Parser/tokenizer_pgen.c";
              "/experiment/src/src/egrep.c";
              "/experiment/src/src/kwsearch.c";
              "/experiment/src/find/find.c";
            ]
        then append_constructor work_dir origin_file "coverage"

  let read_value_map value_map_file =
    let value_map_json = Yojson.Basic.from_file value_map_file in
    Yojson.Basic.Util.to_assoc value_map_json
    |> List.map (fun (s, x) ->
           ( s,
             x |> Yojson.Basic.Util.to_assoc
             |> List.map (fun (s, x) ->
                    ( s,
                      x |> Yojson.Basic.Util.to_assoc
                      |> List.map (fun (s, x) ->
                             ( s,
                               x |> Yojson.Basic.Util.to_list
                               |> List.map (fun x ->
                                      x |> Yojson.Basic.Util.to_string
                                      |> int_of_string) )) )) ))

  class signalChecker signal_table file line score cov_list =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        List.iter
          (fun s ->
            match s.Cil.skind with
            | Cil.If (exp, thenb, elseb, ifloc) when ifloc.Cil.line = line ->
                let loc = Cil.get_stmtLoc (fd.sbody.bstmts |> List.hd).skind in
                print_endline
                  ("ifloc line: " ^ ifloc.Cil.file ^ ":"
                  ^ (ifloc.Cil.line |> string_of_int));

                Pretty.sprint ~width:10
                  (Cil.printExp Cil.defaultCilPrinter () exp)
                |> print_endline;

                let score =
                  if !Cmdline.fun_signal then
                    let _, fun_pos = List.assoc (loc.file, loc.line) cov_list in
                    let _, pos = List.assoc (ifloc.file, ifloc.line) cov_list in
                    let pos = pos *. (1. -. score) in
                    (fun_pos -. pos) /. fun_pos
                  else score
                in
                Hashtbl.add signal_table (file, line, score) true
            | _ -> ())
          fd.Cil.sallstmts;
        if fd.Cil.svar.vname = "bugzoo_ctor" then SkipChildren else DoChildren

      method! vblock blk = Cil.DoChildren
    end

  class conditionCollector printf flush stream line condition_table =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        if fd.Cil.svar.vname = "bugzoo_ctor" then SkipChildren else DoChildren

      method! vblock blk =
        let rec vname_of lv =
          match lv with
          | Cil.Var vi, Cil.NoOffset -> vi.Cil.vname
          | Cil.Var vi, Cil.Field (f, o) -> vi.Cil.vname ^ "." ^ f.Cil.fname
          | Cil.Var vi, Cil.Index (e, o) ->
              vi.Cil.vname ^ "["
              ^ Pretty.sprint 10 (Cil.printExp Cil.defaultCilPrinter () e)
              ^ "]"
          | Cil.Mem exp, Cil.NoOffset -> var_names_of exp |> List.hd |> fst
          | Cil.Mem exp, Cil.Field (f, o) ->
              (var_names_of exp |> List.hd |> fst) ^ "->" ^ f.Cil.fname
          | Cil.Mem exp, Cil.Index (e, o) -> failwith "5"
        and var_names_of exp =
          match exp with
          | Cil.Const c -> [ ("", None) ]
          | Cil.Lval lv -> [ (vname_of lv, Some lv) ]
          | Cil.SizeOfE e -> var_names_of e
          | Cil.AlignOfE e -> var_names_of e
          | Cil.UnOp (_, e, _) -> var_names_of e
          | Cil.BinOp (_, e1, e2, _) ->
              List.rev_append (var_names_of e1) (var_names_of e2)
          | Cil.Question (e1, e2, e3, _) ->
              List.rev_append
                (List.rev_append (var_names_of e1) (var_names_of e2))
                (var_names_of e3)
          | Cil.CastE (_, e) -> var_names_of e
          | _ -> []
        in
        let bstmts, conditions =
          List.fold_left
            (fun (bstmts, conds) s ->
              match s.Cil.skind with
              | Cil.If (exp, thenb, elseb, ifloc) when ifloc.Cil.line = line ->
                  let loc = Cil.get_stmtLoc s.Cil.skind in
                  print_endline
                    ("ifloc line: " ^ ifloc.Cil.file ^ ":"
                    ^ (ifloc.Cil.line |> string_of_int));
                  Pretty.sprint 10 (Cil.printExp Cil.defaultCilPrinter () exp)
                  |> print_endline;
                  let vars = var_names_of exp in
                  List.fold_left
                    (fun (bstmts, conds) (vname, var) ->
                      match var with
                      | Some v -> (bstmts, conds)
                      | None -> (bstmts, conds))
                    (bstmts, exp :: conds)
                    vars
                  |> fun (bstmts, conds) -> (s :: bstmts, conds)
              | _ -> (s :: bstmts, conds))
            ([], []) blk.Cil.bstmts
          |> fun (bstmts, conds) -> (bstmts |> List.rev, conds |> List.rev)
        in

        List.iter
          (fun cond ->
            List.iter
              (fun (vname, exp) ->
                print_endline ("vname: " ^ vname);
                if Hashtbl.mem condition_table vname then ()
                else Hashtbl.add condition_table vname exp)
              (var_names_of cond))
          conditions;

        Cil.DoChildren
    end

  class assumeInjector printf flush stream assume_line_list condition_table
    is_pos strcpy strcmp mmap env_signal append_coverage glob_check_vars =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        if fd.Cil.svar.vname = "bugzoo_ctor" then SkipChildren
        else
          let strcmp_result =
            Cil.makeLocalVar fd "__strcmp_result" Cil.intType
          in
          if !Cmdline.fun_level then (
            (* let funname = fd.svar.vname in *)
            let funloc = fd.svar.vdecl in
            let call =
              (if !Cmdline.mmap then strcpy_of strcpy mmap funloc
              else printf_of printf stream funloc)
              |> Cil.mkStmtOneInstr
            in
            let mmap_inc =
              Cil.Set
                ( (Cil.Var mmap, Cil.NoOffset),
                  Cil.BinOp
                    ( Cil.PlusPI,
                      Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                      Cil.Const
                        (Cil.CInt64
                           ( (funloc.file |> String.length)
                             + (funloc.Cil.line |> string_of_int
                              |> String.length)
                             + 2
                             |> Int64.of_int,
                             Cil.IInt,
                             None )),
                      Cil.intType ),
                  funloc )
              |> Cil.mkStmtOneInstr
            in
            let check_var_name =
              "__"
              ^ (funloc.file
                |> String.map (fun c ->
                       if c = '/' || c = '.' || c = '-' then '_' else c))
              ^ "_"
              ^ (funloc.line |> string_of_int)
            in
            let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
            if !Cmdline.mmap then
              glob_check_vars := VarSet.add check_var_name !glob_check_vars;
            let var_used =
              Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, funloc)
              |> Cil.mkStmtOneInstr
            in
            let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
            let call =
              if !Cmdline.mmap then
                Cil.If
                  ( Cil.UnOp
                      ( Cil.LNot,
                        Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                        Cil.intType ),
                    [ call; mmap_inc; var_used ]
                    |> Cil.compactStmts |> Cil.mkBlock,
                    empty_block,
                    funloc )
                |> Cil.mkStmt
              else call
            in
            let flush = flush_of flush stream funloc |> Cil.mkStmtOneInstr in
            if !Cmdline.mmap then fd.sbody.bstmts <- call :: fd.sbody.bstmts
            else if !Cmdline.no_seg then
              fd.sbody.bstmts <- call :: fd.sbody.bstmts
            else fd.sbody.bstmts <- call :: flush :: fd.sbody.bstmts;
            DoChildren)
          else DoChildren

      method! vblock blk =
        if !Cmdline.block_level then (
          let block_loc =
            if blk.bstmts = [] then Cil.locUnknown
            else Cil.get_stmtLoc (blk.bstmts |> List.hd).skind
          in
          if block_loc.line < 0 || block_loc = Cil.locUnknown then
            Cil.DoChildren
          else
            let call =
              (if !Cmdline.mmap then
               Cil.Call
                 ( None,
                   Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                   [
                     Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                     Cil.Const
                       (Cil.CStr
                          (block_loc.Cil.file ^ ":"
                          ^ (block_loc.Cil.line |> string_of_int)
                          ^ "\n"));
                   ],
                   Cil.locUnknown )
              else
                Cil.Call
                  ( None,
                    Cil.Lval (Cil.Var printf, Cil.NoOffset),
                    [
                      Cil.Lval (Cil.Var stream, Cil.NoOffset);
                      Cil.Const (Cil.CStr "%s:%d\n");
                      Cil.Const (Cil.CStr block_loc.Cil.file);
                      Cil.integer block_loc.Cil.line;
                    ],
                    Cil.locUnknown ))
              |> Cil.mkStmtOneInstr
            in
            let mmap_inc =
              Cil.Set
                ( (Cil.Var mmap, Cil.NoOffset),
                  Cil.BinOp
                    ( Cil.PlusPI,
                      Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                      Cil.Const
                        (Cil.CInt64
                           ( (block_loc.file |> String.length)
                             + (block_loc.Cil.line |> string_of_int
                              |> String.length)
                             + 2
                             |> Int64.of_int,
                             Cil.IInt,
                             None )),
                      Cil.intType ),
                  Cil.locUnknown )
              |> Cil.mkStmtOneInstr
            in
            let check_var_name =
              "__"
              ^ (block_loc.file
                |> String.map (fun c ->
                       if c = '/' || c = '.' || c = '-' then '_' else c))
              ^ "_"
              ^ (block_loc.line |> string_of_int)
            in
            let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
            if !Cmdline.mmap then
              glob_check_vars := VarSet.add check_var_name !glob_check_vars;
            let var_used =
              Cil.Set
                ((Cil.Var check_var, Cil.NoOffset), Cil.one, Cil.locUnknown)
              |> Cil.mkStmtOneInstr
            in
            let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
            let call =
              if !Cmdline.mmap then
                Cil.If
                  ( Cil.UnOp
                      ( Cil.LNot,
                        Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                        Cil.intType ),
                    [ call; mmap_inc; var_used ]
                    |> Cil.compactStmts |> Cil.mkBlock,
                    empty_block,
                    Cil.locUnknown )
                |> Cil.mkStmt
              else call
            in
            let fflush =
              Cil.Call
                ( None,
                  Cil.Lval (Cil.Var flush, Cil.NoOffset),
                  [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                  Cil.locUnknown )
              |> Cil.mkStmtOneInstr
            in
            if !Cmdline.mmap then blk.bstmts <- call :: blk.bstmts
            else if !Cmdline.no_seg then blk.bstmts <- call :: blk.bstmts
            else blk.bstmts <- call :: fflush :: blk.bstmts;
            Cil.DoChildren)
        else Cil.DoChildren

      method! vstmt stmt =
        let action s =
          let result =
            match s.Cil.skind with
            | Cil.If (exp, thenb, elseb, ifloc)
              when List.mem ifloc.Cil.line assume_line_list ->
                let loc = Cil.get_stmtLoc s.Cil.skind in
                print_endline
                  ("ifloc line: " ^ ifloc.Cil.file ^ ":"
                  ^ (ifloc.Cil.line |> string_of_int));
                (* failwith "assume if"; *)
                Pretty.sprint 10 (Cil.printExp Cil.defaultCilPrinter () exp)
                |> print_endline;

                let tr = Cil.Const (Cil.CInt64 (1L, Cil.IInt, None)) in
                let fl = Cil.Const (Cil.CInt64 (0L, Cil.IInt, None)) in
                let new_s =
                  if !Cmdline.instrument = AssumeInject then (
                    s.skind <-
                      (Cil.If ((if is_pos then tr else fl), thenb, elseb, ifloc)
                      |> Cil.mkStmt)
                        .skind;
                    s)
                  else
                    let strcmp_result =
                      Cil.makeVarinfo false "__strcmp_result" Cil.intType
                    in
                    let strcmp_call =
                      Cil.Call
                        ( Some (Cil.Var strcmp_result, Cil.NoOffset),
                          Cil.Lval (Cil.Var strcmp, Cil.NoOffset),
                          [
                            Cil.Lval (Cil.Var env_signal, Cil.NoOffset);
                            Cil.Const
                              (Cil.CStr
                                 (Filename.basename loc.Cil.file
                                 ^ ":"
                                 ^ (loc.Cil.line |> string_of_int)));
                          ],
                          Cil.locUnknown )
                      |> Cil.mkStmtOneInstr
                    in
                    let ternary_cond =
                      Cil.Question
                        ( Cil.Lval (Cil.Var strcmp_result, Cil.NoOffset),
                          exp,
                          (if is_pos then tr else fl),
                          Cil.intType )
                    in
                    s.skind <-
                      (Cil.Block
                         ([
                            strcmp_call;
                            Cil.If (ternary_cond, thenb, elseb, ifloc)
                            |> Cil.mkStmt;
                          ]
                         |> Cil.mkBlock)
                      |> Cil.mkStmt)
                        .skind;
                    s
                in

                (* let loc = Cil.get_stmtLoc s.Cil.skind in *)
                if
                  (not (String.ends_with ~suffix:".c" loc.file))
                  || loc.line < 0 || loc = Cil.locUnknown
                then [ new_s ]
                else if !Cmdline.block_level then
                  let action_tmp stmt =
                    match stmt.Cil.skind with
                    | If (exp, thenb, elseb, l) ->
                        let thenb_loc =
                          if thenb.bstmts = [] then Cil.locUnknown
                          else Cil.get_stmtLoc (thenb.bstmts |> List.hd).skind
                        in
                        (if thenb_loc.line < 0 || thenb_loc = Cil.locUnknown
                        then ()
                        else
                          let call =
                            (if !Cmdline.mmap then
                             Cil.Call
                               ( None,
                                 Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                                 [
                                   Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                                   Cil.Const
                                     (Cil.CStr
                                        (thenb_loc.Cil.file ^ ":"
                                        ^ (thenb_loc.Cil.line |> string_of_int)
                                        ^ "\n"));
                                 ],
                                 Cil.locUnknown )
                            else
                              Cil.Call
                                ( None,
                                  Cil.Lval (Cil.Var printf, Cil.NoOffset),
                                  [
                                    Cil.Lval (Cil.Var stream, Cil.NoOffset);
                                    Cil.Const (Cil.CStr "%s:%d\n");
                                    Cil.Const (Cil.CStr thenb_loc.Cil.file);
                                    Cil.integer thenb_loc.Cil.line;
                                  ],
                                  Cil.locUnknown ))
                            |> Cil.mkStmtOneInstr
                          in
                          let mmap_inc =
                            Cil.Set
                              ( (Cil.Var mmap, Cil.NoOffset),
                                Cil.BinOp
                                  ( Cil.PlusPI,
                                    Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                    Cil.Const
                                      (Cil.CInt64
                                         ( (thenb_loc.file |> String.length)
                                           + (thenb_loc.Cil.line
                                            |> string_of_int |> String.length)
                                           + 2
                                           |> Int64.of_int,
                                           Cil.IInt,
                                           None )),
                                    Cil.intType ),
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let check_var_name =
                            "__"
                            ^ (thenb_loc.file
                              |> String.map (fun c ->
                                     if c = '/' || c = '.' || c = '-' then '_'
                                     else c))
                            ^ "_"
                            ^ (thenb_loc.line |> string_of_int)
                          in
                          let check_var =
                            Cil.makeGlobalVar check_var_name Cil.intType
                          in
                          if !Cmdline.mmap then
                            glob_check_vars :=
                              VarSet.add check_var_name !glob_check_vars;
                          let var_used =
                            Cil.Set
                              ( (Cil.Var check_var, Cil.NoOffset),
                                Cil.one,
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let empty_block =
                            [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                          in
                          let call =
                            if !Cmdline.mmap then
                              Cil.If
                                ( Cil.UnOp
                                    ( Cil.LNot,
                                      Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                      Cil.intType ),
                                  [ call; mmap_inc; var_used ]
                                  |> Cil.compactStmts |> Cil.mkBlock,
                                  empty_block,
                                  Cil.locUnknown )
                              |> Cil.mkStmt
                            else call
                          in
                          let fflush =
                            Cil.Call
                              ( None,
                                Cil.Lval (Cil.Var flush, Cil.NoOffset),
                                [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          if !Cmdline.mmap then
                            thenb.bstmts <- call :: thenb.bstmts
                          else if !Cmdline.no_seg then
                            thenb.bstmts <- call :: thenb.bstmts
                          else thenb.bstmts <- call :: fflush :: thenb.bstmts);
                        let elseb_loc =
                          if elseb.bstmts = [] then Cil.locUnknown
                          else Cil.get_stmtLoc (elseb.bstmts |> List.hd).skind
                        in
                        (if elseb_loc.line < 0 || elseb_loc = Cil.locUnknown
                        then ()
                        else
                          let call =
                            (if !Cmdline.mmap then
                             Cil.Call
                               ( None,
                                 Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                                 [
                                   Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                                   Cil.Const
                                     (Cil.CStr
                                        (elseb_loc.Cil.file ^ ":"
                                        ^ (elseb_loc.Cil.line |> string_of_int)
                                        ^ "\n"));
                                 ],
                                 Cil.locUnknown )
                            else
                              Cil.Call
                                ( None,
                                  Cil.Lval (Cil.Var printf, Cil.NoOffset),
                                  [
                                    Cil.Lval (Cil.Var stream, Cil.NoOffset);
                                    Cil.Const (Cil.CStr "%s:%d\n");
                                    Cil.Const (Cil.CStr elseb_loc.Cil.file);
                                    Cil.integer elseb_loc.Cil.line;
                                  ],
                                  Cil.locUnknown ))
                            |> Cil.mkStmtOneInstr
                          in
                          let mmap_inc =
                            Cil.Set
                              ( (Cil.Var mmap, Cil.NoOffset),
                                Cil.BinOp
                                  ( Cil.PlusPI,
                                    Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                    Cil.Const
                                      (Cil.CInt64
                                         ( (elseb_loc.file |> String.length)
                                           + (elseb_loc.Cil.line
                                            |> string_of_int |> String.length)
                                           + 2
                                           |> Int64.of_int,
                                           Cil.IInt,
                                           None )),
                                    Cil.intType ),
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let check_var_name =
                            "__"
                            ^ (elseb_loc.file
                              |> String.map (fun c ->
                                     if c = '/' || c = '.' || c = '-' then '_'
                                     else c))
                            ^ "_"
                            ^ (elseb_loc.line |> string_of_int)
                          in
                          let check_var =
                            Cil.makeGlobalVar check_var_name Cil.intType
                          in
                          if !Cmdline.mmap then
                            glob_check_vars :=
                              VarSet.add check_var_name !glob_check_vars;
                          let var_used =
                            Cil.Set
                              ( (Cil.Var check_var, Cil.NoOffset),
                                Cil.one,
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let empty_block =
                            [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                          in
                          let call =
                            if !Cmdline.mmap then
                              Cil.If
                                ( Cil.UnOp
                                    ( Cil.LNot,
                                      Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                      Cil.intType ),
                                  [ call; mmap_inc; var_used ]
                                  |> Cil.compactStmts |> Cil.mkBlock,
                                  empty_block,
                                  Cil.locUnknown )
                              |> Cil.mkStmt
                            else call
                          in
                          let fflush =
                            Cil.Call
                              ( None,
                                Cil.Lval (Cil.Var flush, Cil.NoOffset),
                                [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          if !Cmdline.mmap then
                            elseb.bstmts <- call :: elseb.bstmts
                          else if !Cmdline.no_seg then
                            elseb.bstmts <- call :: elseb.bstmts
                          else elseb.bstmts <- call :: fflush :: elseb.bstmts);
                        stmt.skind <- Cil.If (exp, thenb, elseb, l);
                        let call =
                          if !Cmdline.mmap then
                            strcpy_of strcpy mmap loc |> Cil.mkStmtOneInstr
                          else printf_of printf stream loc |> Cil.mkStmtOneInstr
                        in
                        let mmap_inc =
                          Cil.Set
                            ( (Cil.Var mmap, Cil.NoOffset),
                              Cil.BinOp
                                ( Cil.PlusPI,
                                  Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                  Cil.Const
                                    (Cil.CInt64
                                       ( (loc.Cil.file |> String.length)
                                         + (loc.Cil.line |> string_of_int
                                          |> String.length)
                                         + 2
                                         |> Int64.of_int,
                                         Cil.IInt,
                                         None )),
                                  Cil.intType ),
                              loc )
                          |> Cil.mkStmtOneInstr
                        in
                        let check_var_name =
                          "__"
                          ^ (loc.file
                            |> String.map (fun c ->
                                   if c = '/' || c = '.' || c = '-' then '_'
                                   else c))
                          ^ "_"
                          ^ (loc.line |> string_of_int)
                        in
                        let check_var =
                          Cil.makeGlobalVar check_var_name Cil.intType
                        in
                        if !Cmdline.mmap && loc.Cil.line >= 0 then
                          glob_check_vars :=
                            VarSet.add check_var_name !glob_check_vars;
                        let var_used =
                          Cil.Set
                            ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                          |> Cil.mkStmtOneInstr
                        in
                        let empty_block =
                          [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                        in
                        let call =
                          if !Cmdline.mmap then
                            Cil.If
                              ( Cil.UnOp
                                  ( Cil.LNot,
                                    Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                    Cil.intType ),
                                [ call; mmap_inc; var_used ]
                                |> Cil.compactStmts |> Cil.mkBlock,
                                empty_block,
                                loc )
                            |> Cil.mkStmt
                          else call
                        in
                        let fflush =
                          flush_of flush stream loc |> Cil.mkStmtOneInstr
                        in
                        let result =
                          if !Cmdline.mmap then [ stmt; call ]
                          else if !Cmdline.no_seg then [ stmt; call; fflush ]
                          else [ stmt; call ]
                        in
                        result
                    | _ -> [ stmt ]
                  in
                  action_tmp new_s
                else
                  let call =
                    (if !Cmdline.mmap then strcpy_of strcpy mmap loc
                    else printf_of printf stream loc)
                    |> Cil.mkStmtOneInstr
                  in
                  let mmap_inc =
                    Cil.Set
                      ( (Cil.Var mmap, Cil.NoOffset),
                        Cil.BinOp
                          ( Cil.PlusPI,
                            Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                            Cil.Const
                              (Cil.CInt64
                                 ( (loc.Cil.file |> String.length)
                                   + (loc.Cil.line |> string_of_int
                                    |> String.length)
                                   + 2
                                   |> Int64.of_int,
                                   Cil.IInt,
                                   None )),
                            Cil.intType ),
                        loc )
                    |> Cil.mkStmtOneInstr
                  in
                  let check_var_name =
                    "__"
                    ^ (loc.file
                      |> String.map (fun c ->
                             if c = '/' || c = '.' || c = '-' then '_' else c))
                    ^ "_"
                    ^ (loc.line |> string_of_int)
                  in
                  let check_var =
                    Cil.makeGlobalVar check_var_name Cil.intType
                  in
                  if !Cmdline.mmap && loc.Cil.line >= 0 then
                    glob_check_vars :=
                      VarSet.add check_var_name !glob_check_vars;
                  let var_used =
                    Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                    |> Cil.mkStmtOneInstr
                  in
                  let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
                  let call =
                    if !Cmdline.mmap then
                      Cil.If
                        ( Cil.UnOp
                            ( Cil.LNot,
                              Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                              Cil.intType ),
                          [ call; mmap_inc; var_used ]
                          |> Cil.compactStmts |> Cil.mkBlock,
                          empty_block,
                          loc )
                      |> Cil.mkStmt
                    else call
                  in
                  if !Cmdline.fun_level then [ new_s ]
                  else if
                    (not (String.ends_with ~suffix:".c" loc.file))
                    || loc.line < 0
                  then [ new_s ]
                  else if !Cmdline.mmap then [ call; new_s ]
                  else if not !Cmdline.no_seg then
                    let flush =
                      flush_of flush stream loc |> Cil.mkStmtOneInstr
                    in
                    [ call; flush; new_s ]
                  else [ call; new_s ]
            | _ ->
                let loc = Cil.get_stmtLoc s.Cil.skind in
                if
                  (not (String.ends_with ~suffix:".c" loc.file))
                  || loc.line < 0 || loc = Cil.locUnknown
                then [ s ]
                else if !Cmdline.block_level then
                  let action_tmp stmt =
                    match stmt.Cil.skind with
                    | If (exp, thenb, elseb, l) ->
                        let thenb_loc =
                          if thenb.bstmts = [] then Cil.locUnknown
                          else Cil.get_stmtLoc (thenb.bstmts |> List.hd).skind
                        in
                        (if thenb_loc.line < 0 || thenb_loc = Cil.locUnknown
                        then ()
                        else
                          let call =
                            (if !Cmdline.mmap then
                             Cil.Call
                               ( None,
                                 Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                                 [
                                   Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                                   Cil.Const
                                     (Cil.CStr
                                        (thenb_loc.Cil.file ^ ":"
                                        ^ (thenb_loc.Cil.line |> string_of_int)
                                        ^ "\n"));
                                 ],
                                 Cil.locUnknown )
                            else
                              Cil.Call
                                ( None,
                                  Cil.Lval (Cil.Var printf, Cil.NoOffset),
                                  [
                                    Cil.Lval (Cil.Var stream, Cil.NoOffset);
                                    Cil.Const (Cil.CStr "%s:%d\n");
                                    Cil.Const (Cil.CStr thenb_loc.Cil.file);
                                    Cil.integer thenb_loc.Cil.line;
                                  ],
                                  Cil.locUnknown ))
                            |> Cil.mkStmtOneInstr
                          in
                          let mmap_inc =
                            Cil.Set
                              ( (Cil.Var mmap, Cil.NoOffset),
                                Cil.BinOp
                                  ( Cil.PlusPI,
                                    Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                    Cil.Const
                                      (Cil.CInt64
                                         ( (thenb_loc.file |> String.length)
                                           + (thenb_loc.Cil.line
                                            |> string_of_int |> String.length)
                                           + 2
                                           |> Int64.of_int,
                                           Cil.IInt,
                                           None )),
                                    Cil.intType ),
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let check_var_name =
                            "__"
                            ^ (thenb_loc.file
                              |> String.map (fun c ->
                                     if c = '/' || c = '.' || c = '-' then '_'
                                     else c))
                            ^ "_"
                            ^ (thenb_loc.line |> string_of_int)
                          in
                          let check_var =
                            Cil.makeGlobalVar check_var_name Cil.intType
                          in
                          if !Cmdline.mmap then
                            glob_check_vars :=
                              VarSet.add check_var_name !glob_check_vars;
                          let var_used =
                            Cil.Set
                              ( (Cil.Var check_var, Cil.NoOffset),
                                Cil.one,
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let empty_block =
                            [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                          in
                          let call =
                            if !Cmdline.mmap then
                              Cil.If
                                ( Cil.UnOp
                                    ( Cil.LNot,
                                      Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                      Cil.intType ),
                                  [ call; mmap_inc; var_used ]
                                  |> Cil.compactStmts |> Cil.mkBlock,
                                  empty_block,
                                  Cil.locUnknown )
                              |> Cil.mkStmt
                            else call
                          in
                          let fflush =
                            Cil.Call
                              ( None,
                                Cil.Lval (Cil.Var flush, Cil.NoOffset),
                                [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          if !Cmdline.mmap then
                            thenb.bstmts <- call :: thenb.bstmts
                          else if !Cmdline.no_seg then
                            thenb.bstmts <- call :: thenb.bstmts
                          else thenb.bstmts <- call :: fflush :: thenb.bstmts);
                        let elseb_loc =
                          if elseb.bstmts = [] then Cil.locUnknown
                          else Cil.get_stmtLoc (elseb.bstmts |> List.hd).skind
                        in
                        (if elseb_loc.line < 0 || elseb_loc = Cil.locUnknown
                        then ()
                        else
                          let call =
                            (if !Cmdline.mmap then
                             Cil.Call
                               ( None,
                                 Cil.Lval (Cil.Var strcpy, Cil.NoOffset),
                                 [
                                   Cil.Lval (Cil.Var mmap, Cil.NoOffset);
                                   Cil.Const
                                     (Cil.CStr
                                        (elseb_loc.Cil.file ^ ":"
                                        ^ (elseb_loc.Cil.line |> string_of_int)
                                        ^ "\n"));
                                 ],
                                 Cil.locUnknown )
                            else
                              Cil.Call
                                ( None,
                                  Cil.Lval (Cil.Var printf, Cil.NoOffset),
                                  [
                                    Cil.Lval (Cil.Var stream, Cil.NoOffset);
                                    Cil.Const (Cil.CStr "%s:%d\n");
                                    Cil.Const (Cil.CStr elseb_loc.Cil.file);
                                    Cil.integer elseb_loc.Cil.line;
                                  ],
                                  Cil.locUnknown ))
                            |> Cil.mkStmtOneInstr
                          in
                          let mmap_inc =
                            Cil.Set
                              ( (Cil.Var mmap, Cil.NoOffset),
                                Cil.BinOp
                                  ( Cil.PlusPI,
                                    Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                    Cil.Const
                                      (Cil.CInt64
                                         ( (elseb_loc.file |> String.length)
                                           + (elseb_loc.Cil.line
                                            |> string_of_int |> String.length)
                                           + 2
                                           |> Int64.of_int,
                                           Cil.IInt,
                                           None )),
                                    Cil.intType ),
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let check_var_name =
                            "__"
                            ^ (elseb_loc.file
                              |> String.map (fun c ->
                                     if c = '/' || c = '.' || c = '-' then '_'
                                     else c))
                            ^ "_"
                            ^ (elseb_loc.line |> string_of_int)
                          in
                          let check_var =
                            Cil.makeGlobalVar check_var_name Cil.intType
                          in
                          if !Cmdline.mmap then
                            glob_check_vars :=
                              VarSet.add check_var_name !glob_check_vars;
                          let var_used =
                            Cil.Set
                              ( (Cil.Var check_var, Cil.NoOffset),
                                Cil.one,
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          let empty_block =
                            [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                          in
                          let call =
                            if !Cmdline.mmap then
                              Cil.If
                                ( Cil.UnOp
                                    ( Cil.LNot,
                                      Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                      Cil.intType ),
                                  [ call; mmap_inc; var_used ]
                                  |> Cil.compactStmts |> Cil.mkBlock,
                                  empty_block,
                                  Cil.locUnknown )
                              |> Cil.mkStmt
                            else call
                          in
                          let fflush =
                            Cil.Call
                              ( None,
                                Cil.Lval (Cil.Var flush, Cil.NoOffset),
                                [ Cil.Lval (Cil.Var stream, Cil.NoOffset) ],
                                Cil.locUnknown )
                            |> Cil.mkStmtOneInstr
                          in
                          if !Cmdline.mmap then
                            elseb.bstmts <- call :: elseb.bstmts
                          else if !Cmdline.no_seg then
                            elseb.bstmts <- call :: elseb.bstmts
                          else elseb.bstmts <- call :: fflush :: elseb.bstmts);
                        stmt.skind <- Cil.If (exp, thenb, elseb, l);
                        let call =
                          if !Cmdline.mmap then
                            strcpy_of strcpy mmap loc |> Cil.mkStmtOneInstr
                          else printf_of printf stream loc |> Cil.mkStmtOneInstr
                        in
                        let mmap_inc =
                          Cil.Set
                            ( (Cil.Var mmap, Cil.NoOffset),
                              Cil.BinOp
                                ( Cil.PlusPI,
                                  Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                                  Cil.Const
                                    (Cil.CInt64
                                       ( (loc.Cil.file |> String.length)
                                         + (loc.Cil.line |> string_of_int
                                          |> String.length)
                                         + 2
                                         |> Int64.of_int,
                                         Cil.IInt,
                                         None )),
                                  Cil.intType ),
                              loc )
                          |> Cil.mkStmtOneInstr
                        in
                        let check_var_name =
                          "__"
                          ^ (loc.file
                            |> String.map (fun c ->
                                   if c = '/' || c = '.' || c = '-' then '_'
                                   else c))
                          ^ "_"
                          ^ (loc.line |> string_of_int)
                        in
                        let check_var =
                          Cil.makeGlobalVar check_var_name Cil.intType
                        in
                        if !Cmdline.mmap && loc.Cil.line >= 0 then
                          glob_check_vars :=
                            VarSet.add check_var_name !glob_check_vars;
                        let var_used =
                          Cil.Set
                            ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                          |> Cil.mkStmtOneInstr
                        in
                        let empty_block =
                          [ Cil.mkEmptyStmt () ] |> Cil.mkBlock
                        in
                        let call =
                          if !Cmdline.mmap then
                            Cil.If
                              ( Cil.UnOp
                                  ( Cil.LNot,
                                    Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                                    Cil.intType ),
                                [ call; mmap_inc; var_used ]
                                |> Cil.compactStmts |> Cil.mkBlock,
                                empty_block,
                                loc )
                            |> Cil.mkStmt
                          else call
                        in
                        let fflush =
                          flush_of flush stream loc |> Cil.mkStmtOneInstr
                        in
                        let result =
                          if !Cmdline.mmap then [ stmt; call ]
                          else if !Cmdline.no_seg then [ stmt; call; fflush ]
                          else [ stmt; call ]
                        in
                        result
                    | _ -> [ stmt ]
                  in
                  action_tmp s
                else
                  let call =
                    (if !Cmdline.mmap then strcpy_of strcpy mmap loc
                    else printf_of printf stream loc)
                    |> Cil.mkStmtOneInstr
                  in
                  let mmap_inc =
                    Cil.Set
                      ( (Cil.Var mmap, Cil.NoOffset),
                        Cil.BinOp
                          ( Cil.PlusPI,
                            Cil.Lval (Cil.Var mmap, Cil.NoOffset),
                            Cil.Const
                              (Cil.CInt64
                                 ( (loc.Cil.file |> String.length)
                                   + (loc.Cil.line |> string_of_int
                                    |> String.length)
                                   + 2
                                   |> Int64.of_int,
                                   Cil.IInt,
                                   None )),
                            Cil.intType ),
                        loc )
                    |> Cil.mkStmtOneInstr
                  in
                  let check_var_name =
                    "__"
                    ^ (loc.file
                      |> String.map (fun c ->
                             if c = '/' || c = '.' || c = '-' then '_' else c))
                    ^ "_"
                    ^ (loc.line |> string_of_int)
                  in
                  let check_var =
                    Cil.makeGlobalVar check_var_name Cil.intType
                  in
                  if !Cmdline.mmap && loc.Cil.line >= 0 then
                    glob_check_vars :=
                      VarSet.add check_var_name !glob_check_vars;
                  let var_used =
                    Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                    |> Cil.mkStmtOneInstr
                  in
                  let empty_block = [ Cil.mkEmptyStmt () ] |> Cil.mkBlock in
                  let call =
                    if !Cmdline.mmap then
                      Cil.If
                        ( Cil.UnOp
                            ( Cil.LNot,
                              Cil.Lval (Cil.Var check_var, Cil.NoOffset),
                              Cil.intType ),
                          [ call; mmap_inc; var_used ]
                          |> Cil.compactStmts |> Cil.mkBlock,
                          empty_block,
                          loc )
                      |> Cil.mkStmt
                    else call
                  in
                  if !Cmdline.fun_level then [ s ]
                  else if
                    (not (String.ends_with ~suffix:".c" loc.file))
                    || loc.line < 0
                  then [ s ]
                  else if !Cmdline.mmap then [ call; s ]
                  else if not !Cmdline.no_seg then
                    let flush =
                      flush_of flush stream loc |> Cil.mkStmtOneInstr
                    in
                    [ call; flush; s ]
                  else [ call; s ]
          in
          Cil.Block (result |> Cil.mkBlock) |> Cil.mkStmt
        in
        Cil.ChangeDoChildrenPost (stmt, action)

      method! vinst instr =
        let action is =
          match is with
          | [ i ] ->
              let loc = Cil.get_instrLoc i in
              if
                (not (String.ends_with ~suffix:".c" loc.file))
                || loc.Cil.line < 0
              then [ i ]
              else
                let check_var_name =
                  "__"
                  ^ (loc.file
                    |> String.map (fun c ->
                           if c = '/' || c = '.' || c = '-' then '_' else c))
                  ^ "_"
                  ^ (loc.line |> string_of_int)
                in
                let check_var = Cil.makeGlobalVar check_var_name Cil.intType in
                if !Cmdline.mmap && loc.Cil.line >= 0 then
                  glob_check_vars := VarSet.add check_var_name !glob_check_vars;
                let call =
                  if !Cmdline.mmap then
                    append_coverage_of append_coverage check_var loc
                  else printf_of printf stream loc
                in
                let var_used =
                  Cil.Set ((Cil.Var check_var, Cil.NoOffset), Cil.one, loc)
                in
                if !Cmdline.fun_level then [ i ]
                else if
                  (not (String.ends_with ~suffix:".c" loc.file)) || loc.line < 0
                then [ i ]
                else if !Cmdline.mmap then [ call; var_used; i ]
                else if not !Cmdline.no_seg then
                  let flush = flush_of flush stream loc in
                  [ call; flush; i ]
                else [ call; i ]
          | _ -> is
        in
        Cil.ChangeDoChildrenPost ([ instr ], action)
    end

  let signal_checker work_dir origin_file_opt pt_file signal_table signal_list
      cov_list =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      print_endline pt_file;
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let cil = Option.get cil_opt in
      Cfg.computeFileCFG cil;
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Instrument Value Printer %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;

        (* List.iter
              (fun (file, line) -> print_endline (file ^ (line |> string_of_int)))
              signal_list;

            print_endline (List.length signal_list |> string_of_int); *)
        List.iter
          (fun ((file : string), line, score) ->
            if
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (origin_file |> Filename.basename |> Filename.remove_extension)
            then
              (* failwith ("check_signal origin_file: " ^ origin_file); *)
              Cil.visitCilFile
                (new signalChecker signal_table file line score cov_list)
                cil
            else ())
          signal_list

  (* List.iter
     (fun (file, line) -> print_endline (file ^ (line |> string_of_int)))
     signal_list_filter; *)

  (* print_endline (List.length signal_list_filter |> string_of_int);

     print_signal signal_list_filter; *)

  let condition_collector work_dir origin_file_opt pt_file =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      print_endline pt_file;
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    let condition_table = Hashtbl.create 100 in
    (if Option.is_none cil_opt then ()
    else
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Condition Collector for %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let printf =
          Cil.findOrCreateFunc cil "fprintf"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("stream", fileptr, []); ("format", Cil.charPtrType, []) ],
                 true,
                 [] ))
        in
        let flush =
          Cil.findOrCreateFunc cil "fflush"
            (Cil.TFun (Cil.voidType, Some [ ("stream", fileptr, []) ], false, []))
        in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        (* Cil.visitCilFile (new instrumentVisitor printf flush stream) cil; *)
        if
          String.equal
            (!Cmdline.inject_file |> Filename.basename
           |> Filename.remove_extension)
            (origin_file |> Filename.basename |> Filename.remove_extension)
        then
          Cil.visitCilFile
            (new conditionCollector
               printf flush stream !Cmdline.inject_line condition_table)
            cil;
        (* Hashtbl.iter
           (fun name exp -> print_endline ("Hashtbl vname: " ^ name))
           condition_table; *)
        Unix.system
          ("cp " ^ origin_file ^ " "
          ^ Filename.remove_extension origin_file
          ^ ".origin.c")
        |> ignore;
        (* (if List.mem (Filename.basename origin_file) [ "proc_open.c"; "cast.c" ]
           then ()
           else
             let oc = open_out origin_file in
             Cil.dumpFile !Cil.printerForMaincil oc "" cil;
             close_out oc); *)
        if
          List.mem
            (Unix.realpath origin_file)
            [
              "/experiment/src/gzip.c";
              "/experiment/src/libtiff/tif_unix.c";
              "/experiment/src/libtiff/mkg3states.c";
              "/experiment/src/src/http_auth.c";
              "/experiment/src/main/main.c";
              "/experiment/src/main.c";
              "/experiment/src/Modules/main.c";
              "/experiment/src/Parser/tokenizer_pgen.c";
              (* "/experiment/src/version.c"; *)
              "/experiment/src/src/egrep.c";
              "/experiment/src/src/kwsearch.c";
              "/experiment/src/find/find.c";
            ]
        then append_constructor work_dir origin_file "coverage");
    condition_table

  let injector work_dir origin_file_opt pt_file condition_table value_map
      assume_file (assume_list : int list) is_pos =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      print_endline pt_file;
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Condition Injector for %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let printf =
          Cil.findOrCreateFunc cil "fprintf"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("stream", fileptr, []); ("format", Cil.charPtrType, []) ],
                 true,
                 [] ))
        in
        let flush =
          Cil.findOrCreateFunc cil "fflush"
            (Cil.TFun (Cil.voidType, Some [ ("stream", fileptr, []) ], false, []))
        in
        let append_coverage =
          Cil.findOrCreateFunc cil "append_coverage"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [
                     ("check_var", Cil.intType, []);
                     ("cov_data", Cil.charConstPtrType, []);
                     ("cov_data_len", Cil.intType, []);
                   ],
                 false,
                 [] ))
        in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        let mmap = Cil.makeGlobalVar "__inst_mmap" Cil.charPtrType in
        let env_signal = Cil.makeGlobalVar "__env_signal" Cil.charPtrType in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        cil.globals <- Cil.GVarDecl (mmap, Cil.locUnknown) :: cil.globals;
        cil.globals <- Cil.GVarDecl (env_signal, Cil.locUnknown) :: cil.globals;
        let strcpy =
          Cil.findOrCreateFunc cil "strcpy"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [
                     ("dest", Cil.charPtrType, []);
                     ("src", Cil.charConstPtrType, []);
                   ],
                 false,
                 [] ))
        in
        let exit =
          Cil.findOrCreateFunc cil "exit"
            (Cil.TFun
               (Cil.voidType, Some [ ("status", Cil.intType, []) ], true, []))
        in
        let strcmp =
          Cil.findOrCreateFunc cil "strcmp"
            (Cil.TFun
               ( Cil.intType,
                 Some
                   [
                     ("str1", Cil.charConstPtrType, []);
                     ("str2", Cil.charConstPtrType, []);
                   ],
                 false,
                 [] ))
        in
        print_endline origin_file;
        let glob_check_vars = ref VarSet.empty in
        if
          !Cmdline.instrument = Cmdline.AssumeInject
          || !Cmdline.instrument = Cmdline.ErrorInject
          || !Cmdline.instrument = Cmdline.ErrorCoverage
        then
          if
            String.equal
              (assume_file |> Filename.basename |> Filename.remove_extension)
              (origin_file |> Filename.basename |> Filename.remove_extension)
          then
            (* failwith ("assume_file: " ^ assume_file); *)
            Cil.visitCilFile
              (new assumeInjector
                 printf flush stream assume_list condition_table is_pos strcpy
                 strcmp mmap env_signal append_coverage glob_check_vars)
              cil;
        VarSet.iter
          (fun v ->
            let tmp_glob_var = Cil.makeGlobalVar v Cil.intType in
            tmp_glob_var.vstorage <- Cil.Static;
            cil.globals <-
              Cil.GVar
                ( tmp_glob_var,
                  { init = Some (Cil.SingleInit Cil.zero) },
                  Cil.locUnknown )
              :: cil.globals)
          !glob_check_vars;
        (* Hashtbl.iter
           (fun name exp -> print_endline ("Hashtbl vname: " ^ name))
           condition_table; *)
        (if List.mem (Filename.basename origin_file) [ "proc_open.c"; "cast.c" ]
        then ()
        else
          let oc = open_out origin_file in
          Cil.dumpFile !Cil.printerForMaincil oc "" cil;
          close_out oc;
          if
            String.equal
              (!Cmdline.inject_file |> Filename.basename
             |> Filename.remove_extension)
              (origin_file |> Filename.basename |> Filename.remove_extension)
          then
            Unix.system
              ("sed -i \"s/void assert(int condition ) ;/#include \
                <assert.h>/\" " ^ origin_file)
            |> ignore);
        if
          List.mem
            (Unix.realpath origin_file)
            [
              "/experiment/src/gzip.c";
              "/experiment/src/libtiff/tif_unix.c";
              "/experiment/src/libtiff/mkg3states.c";
              "/experiment/src/src/http_auth.c";
              "/experiment/src/main/main.c";
              "/experiment/src/main.c";
              "/experiment/src/Modules/main.c";
              "/experiment/src/Parser/tokenizer_pgen.c";
              (* "/experiment/src/version.c"; *)
              "/experiment/src/src/egrep.c";
              "/experiment/src/src/kwsearch.c";
              "/experiment/src/find/find.c";
            ]
        then append_constructor work_dir origin_file "coverage"

  let run work_dir src_dir =
    Utils.traverse_pp_file
      (fun pp_file ->
        if
          !Cmdline.instrument = Cmdline.AssertInject
          && String.equal
               (!Cmdline.inject_file |> Filename.basename
              |> Filename.remove_extension)
               (pp_file |> Filename.basename |> Filename.remove_extension)
        then ()
        else if !Cmdline.instrument = Cmdline.AssumeInject then
          let rec read_signal_list sig_file sig_list =
            match input_line sig_file |> String.split_on_char ':' with
            | [ file; line ] ->
                read_signal_list sig_file
                  ((file, line |> int_of_string) :: sig_list)
            | exception End_of_file ->
                close_in sig_file;
                sig_list
            | _ -> read_signal_list sig_file sig_list
          in
          let signal_file = open_in (work_dir ^ "/signal_list.txt") in
          let signal_neg_file = open_in (work_dir ^ "/signal_neg_list.txt") in
          let assume_list = read_signal_list signal_file [] in
          let assume_neg_list = read_signal_list signal_neg_file [] in
          let assume_file_list = List.map (fun (file, _) -> file) assume_list in
          let assume_neg_file_list =
            List.map (fun (file, _) -> file) assume_neg_list
          in
          if
            List.exists
              (fun file ->
                String.equal
                  (file |> Filename.basename |> Filename.remove_extension)
                  (pp_file |> Filename.basename |> Filename.remove_extension))
              assume_file_list
          then ()
          else if
            List.exists
              (fun file ->
                String.equal
                  (file |> Filename.basename |> Filename.remove_extension)
                  (pp_file |> Filename.basename |> Filename.remove_extension))
              assume_neg_file_list
          then ()
          else
            let origin_file_opt = Utils.find_origin_file_opt pp_file in
            instrument work_dir origin_file_opt pp_file
        else
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          instrument work_dir origin_file_opt pp_file)
      src_dir

  let check_signal work_dir src_dir =
    let rec read_signal_list sig_file sig_list =
      match
        input_line sig_file |> String.split_on_char '\t'
        |> List.filter (fun s -> s <> "")
      with
      | [ signal; info ] -> (
          match signal |> String.split_on_char ':' with
          | [ file; line ] -> (
              match info |> String.split_on_char ' ' with
              | [ _; _; score ] ->
                  read_signal_list sig_file
                    ((file, line |> int_of_string, score |> float_of_string)
                    :: sig_list)
              | _ -> failwith "Invalid format")
          | _ -> failwith "Invalid format")
      | exception End_of_file ->
          close_in sig_file;
          sig_list
      | _ -> read_signal_list sig_file sig_list
    in

    let rec read_coverage_list cov_file cov_list =
      match
        input_line cov_file |> String.split_on_char '\t'
        |> List.filter (fun s -> s <> "")
      with
      | [ signal; info ] -> (
          match signal |> String.split_on_char ':' with
          | [ file; line ] -> (
              match info |> String.split_on_char ' ' with
              | [ neg; pos; _; _ ] ->
                  read_coverage_list cov_file
                    (( (file, line |> int_of_string),
                       (neg |> float_of_string, pos |> float_of_string) )
                    :: cov_list)
              | _ -> failwith "Invalid format")
          | _ -> failwith "Invalid format")
      | exception End_of_file ->
          close_in cov_file;
          cov_list
      | _ -> read_coverage_list cov_file cov_list
    in

    let (signal_list : (string * int * float) list) =
      let sig_file = open_in (work_dir ^ "/signal_list.txt") in
      read_signal_list sig_file []
    in

    let cov_list =
      let cov_file = open_in (work_dir ^ "/coverage.txt") in
      read_coverage_list cov_file []
    in

    print_endline
      ("signal_list length: " ^ (List.length signal_list |> string_of_int));

    let out_sig_file = open_out (work_dir ^ "/signal_list_filter.txt") in

    let rec print_signal = function
      | [] -> close_out out_sig_file
      | (file, line) :: tl ->
          Printf.fprintf out_sig_file "%s:%d\t0 0\n" file line;
          print_signal tl
    in
    let signal_table = Hashtbl.create 100000 in

    Utils.traverse_pp_file
      (fun pp_file ->
        let origin_file_opt = Utils.find_origin_file_opt pp_file in
        signal_checker work_dir origin_file_opt pp_file signal_table signal_list
          cov_list)
      src_dir;

    print_endline (Hashtbl.length signal_table |> string_of_int);

    Hashtbl.iter
      (fun (file, line, score) _ ->
        print_endline (file ^ ": " ^ (line |> string_of_int));
        Printf.fprintf out_sig_file "%s:%d\t0 0 %f\n" file line score)
      signal_table;

    close_out out_sig_file

  let assumeinject work_dir src_dir =
    let rec read_signal_list sig_file sig_list =
      match input_line sig_file |> String.split_on_char ':' with
      | [ file; line ] ->
          read_signal_list sig_file ((file, line |> int_of_string) :: sig_list)
      | exception End_of_file ->
          close_in sig_file;
          sig_list
      | _ -> read_signal_list sig_file sig_list
    in
    let signal_file = open_in (work_dir ^ "/signal_list.txt") in
    let signal_neg_file = open_in (work_dir ^ "/signal_neg_list.txt") in
    let assume_list = read_signal_list signal_file [] in
    let assume_neg_list = read_signal_list signal_neg_file [] in

    Utils.traverse_pp_file
      (fun pp_file ->
        let assume_line_list =
          List.filter
            (fun (file, line) ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_list
          |> List.map (fun (_, line) -> line)
        in
        let assume_neg_line_list =
          List.filter
            (fun (file, line) ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_neg_list
          |> List.map (fun (_, line) -> line)
        in
        let assume_file_list = List.map (fun (file, _) -> file) assume_list in
        let assume_neg_file_list =
          List.map (fun (file, _) -> file) assume_neg_list
        in
        if
          List.exists
            (fun file ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_file_list
        then
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          let condition_table =
            condition_collector work_dir origin_file_opt pp_file
          in
          (* failwith ("pp_file: " ^ pp_file); *)
          injector work_dir origin_file_opt pp_file condition_table [] pp_file
            assume_line_list true
          (* instrument work_dir origin_file_opt pp_file *)
        else if
          List.exists
            (fun file ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_neg_file_list
        then
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          let condition_table =
            condition_collector work_dir origin_file_opt pp_file
          in
          injector work_dir origin_file_opt pp_file condition_table [] pp_file
            assume_neg_line_list false
          (* instrument work_dir origin_file_opt pp_file *)
        else
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          instrument work_dir origin_file_opt pp_file)
      src_dir

  let errorinject work_dir src_dir =
    let rec read_signal_list sig_file sig_list =
      match input_line sig_file |> String.split_on_char ':' with
      | [ file; line ] ->
          read_signal_list sig_file ((file, line |> int_of_string) :: sig_list)
      | exception End_of_file ->
          close_in sig_file;
          sig_list
      | _ -> read_signal_list sig_file sig_list
    in
    let signal_file = open_in (work_dir ^ "/signal_list.txt") in
    let signal_neg_file = open_in (work_dir ^ "/signal_neg_list.txt") in
    let assume_list = read_signal_list signal_file [] in
    let assume_neg_list = read_signal_list signal_neg_file [] in

    Utils.traverse_pp_file
      (fun pp_file ->
        let assume_line_list =
          List.filter
            (fun (file, line) ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_list
          |> List.map (fun (_, line) -> line)
        in
        let assume_neg_line_list =
          List.filter
            (fun (file, line) ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_neg_list
          |> List.map (fun (_, line) -> line)
        in
        let assume_file_list = List.map (fun (file, _) -> file) assume_list in
        let assume_neg_file_list =
          List.map (fun (file, _) -> file) assume_neg_list
        in
        if
          List.exists
            (fun file ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_file_list
        then
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          let condition_table =
            condition_collector work_dir origin_file_opt pp_file
          in
          (* failwith ("pp_file: " ^ pp_file); *)
          injector work_dir origin_file_opt pp_file condition_table [] pp_file
            assume_line_list false
          (* instrument work_dir origin_file_opt pp_file *)
        else if
          List.exists
            (fun file ->
              String.equal
                (file |> Filename.basename |> Filename.remove_extension)
                (pp_file |> Filename.basename |> Filename.remove_extension))
            assume_neg_file_list
        then
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          let condition_table =
            condition_collector work_dir origin_file_opt pp_file
          in
          injector work_dir origin_file_opt pp_file condition_table [] pp_file
            assume_neg_line_list true
          (* instrument work_dir origin_file_opt pp_file *)
        else
          let origin_file_opt = Utils.find_origin_file_opt pp_file in
          instrument work_dir origin_file_opt pp_file)
      src_dir

  class branchInstrumentor printf flush stream =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        if fd.Cil.svar.vname = "bugzoo_ctor" then SkipChildren else DoChildren

      method! vblock blk = Cil.DoChildren

      method! vstmt stmt =
        let action s =
          let result =
            match s.Cil.skind with
            | Cil.If (exp, thenb, elseb, ifloc) ->
                let loc = Cil.get_stmtLoc s.Cil.skind in
                print_endline
                  ("ifloc line: " ^ ifloc.Cil.file ^ ":"
                  ^ (ifloc.Cil.line |> string_of_int));
                (* failwith "assume if"; *)
                Pretty.sprint 10 (Cil.printExp Cil.defaultCilPrinter () exp)
                |> print_endline;

                if
                  (not (String.ends_with ~suffix:".c" loc.file))
                  || loc.line < 0 || loc = Cil.locUnknown
                then [ s ]
                else
                  let call =
                    printf_of printf stream loc |> Cil.mkStmtOneInstr
                  in
                  let flush = flush_of flush stream loc |> Cil.mkStmtOneInstr in
                  let print_true =
                    Cil.Call
                      ( None,
                        Cil.Lval (Cil.Var printf, Cil.NoOffset),
                        [
                          Cil.Lval (Cil.Var stream, Cil.NoOffset);
                          Cil.mkString "True\n";
                        ],
                        loc )
                    |> Cil.mkStmtOneInstr
                  in
                  let print_false =
                    Cil.Call
                      ( None,
                        Cil.Lval (Cil.Var printf, Cil.NoOffset),
                        [
                          Cil.Lval (Cil.Var stream, Cil.NoOffset);
                          Cil.mkString "False\n";
                        ],
                        loc )
                    |> Cil.mkStmtOneInstr
                  in
                  thenb.bstmts <- print_true :: thenb.bstmts;
                  elseb.bstmts <- print_false :: elseb.bstmts;
                  let new_s =
                    Cil.Block
                      (Cil.mkBlock
                         [
                           call;
                           flush;
                           Cil.If (exp, thenb, elseb, ifloc) |> Cil.mkStmt;
                         ])
                  in
                  s.skind <- new_s;
                  [ s ]
            | _ -> [ s ]
          in
          Cil.Block (result |> Cil.mkBlock) |> Cil.mkStmt
        in
        Cil.ChangeDoChildrenPost (stmt, action)

      method! vinst instr = DoChildren
    end

  let branch_instrument work_dir origin_file_opt pt_file =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let _ = print_endline pt_file in
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Instrument Branch Printer %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let printf =
          Cil.findOrCreateFunc cil "fprintf"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("stream", fileptr, []); ("format", Cil.charPtrType, []) ],
                 true,
                 [] ))
        in
        let flush =
          Cil.findOrCreateFunc cil "fflush"
            (Cil.TFun (Cil.voidType, Some [ ("stream", fileptr, []) ], false, []))
        in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        Cil.visitCilFile (new branchInstrumentor printf flush stream) cil;

        Unix.system
          ("cp " ^ origin_file ^ " "
          ^ Filename.remove_extension origin_file
          ^ ".origin.c")
        |> ignore;
        (if List.mem (Filename.basename origin_file) [ "proc_open.c"; "cast.c" ]
        then ()
        else
          let oc = open_out origin_file in
          (* List.iter
               (fun x ->
                 Pretty.sprint ~width:100 (Cil.d_shortglobal () x) |> print_endline)
               cil.globals;
             failwith ""; *)
          Cil.dumpFile !Cil.printerForMaincil oc "" cil;
          close_out oc);
        if
          List.mem
            (Unix.realpath origin_file)
            [
              "/experiment/src/gzip.c";
              "/experiment/src/libtiff/tif_unix.c";
              "/experiment/src/libtiff/mkg3states.c";
              "/experiment/src/src/http_auth.c";
              "/experiment/src/main/main.c";
              "/experiment/src/main.c";
              "/experiment/src/Modules/main.c";
              "/experiment/src/Parser/tokenizer_pgen.c";
              (* "/experiment/src/version.c"; *)
              "/experiment/src/src/egrep.c";
              "/experiment/src/src/kwsearch.c";
              "/experiment/src/find/find.c";
            ]
        then append_constructor work_dir origin_file "coverage"

  let branch_printer work_dir src_dir =
    Utils.traverse_pp_file
      (fun pp_file ->
        let origin_file_opt = Utils.find_origin_file_opt pp_file in
        branch_instrument work_dir origin_file_opt pp_file)
      src_dir

  let branch_instrument work_dir origin_file_opt pt_file =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let _ = print_endline pt_file in
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Instrument Branch Printer %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let printf =
          Cil.findOrCreateFunc cil "fprintf"
            (Cil.TFun
               ( Cil.voidType,
                 Some
                   [ ("stream", fileptr, []); ("format", Cil.charPtrType, []) ],
                 true,
                 [] ))
        in
        let flush =
          Cil.findOrCreateFunc cil "fflush"
            (Cil.TFun (Cil.voidType, Some [ ("stream", fileptr, []) ], false, []))
        in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        Cil.visitCilFile (new branchInstrumentor printf flush stream) cil;

        Unix.system
          ("cp " ^ origin_file ^ " "
          ^ Filename.remove_extension origin_file
          ^ ".origin.c")
        |> ignore;
        (if List.mem (Filename.basename origin_file) [ "proc_open.c"; "cast.c" ]
        then ()
        else
          let oc = open_out origin_file in
          Cil.dumpFile !Cil.printerForMaincil oc "" cil;
          close_out oc);
        if
          List.mem
            (Unix.realpath origin_file)
            [
              "/experiment/src/gzip.c";
              "/experiment/src/libtiff/tif_unix.c";
              "/experiment/src/libtiff/mkg3states.c";
              "/experiment/src/src/http_auth.c";
              "/experiment/src/main/main.c";
              "/experiment/src/main.c";
              "/experiment/src/Modules/main.c";
              "/experiment/src/Parser/tokenizer_pgen.c";
              (* "/experiment/src/version.c"; *)
              "/experiment/src/src/egrep.c";
              "/experiment/src/src/kwsearch.c";
              "/experiment/src/find/find.c";
            ]
        then append_constructor work_dir origin_file "coverage"

  class functionInstrumentor function_table =
    object
      inherit Cil.nopCilVisitor

      method! vglob g =
        let loc = Cil.get_globalLoc g in
        if String.starts_with ~prefix:"/usr" loc.file then SkipChildren
        else DoChildren

      method! vfunc fd =
        let funloc = fd.svar.vdecl in
        let filename = funloc.Cil.file in
        let lineno = funloc.Cil.line in
        Hashtbl.add function_table (filename, lineno) true;
        SkipChildren
    end

  let function_instrument work_dir origin_file_opt pt_file function_table =
    Cil.resetCIL ();
    Cil.insertImplicitCasts := false;
    let cil_opt =
      try Some (Frontc.parse pt_file ()) with
      | Frontc.ParseError _ -> None
      | Stack_overflow ->
          Logging.log "%s" "Stack overflow";
          None
      | e ->
          Logging.log "%s" (Printexc.to_string e);
          None
    in
    if Option.is_none cil_opt then ()
    else
      let _ = print_endline pt_file in
      let cil = Option.get cil_opt in
      let origin_file_cand = Filename.remove_extension pt_file ^ ".c" in
      let origin_file =
        if Sys.file_exists origin_file_cand then origin_file_cand
        else if Option.is_some origin_file_opt then Option.get origin_file_opt
        else (
          prerr_endline origin_file_cand;
          Utils.find_file (Filename.basename origin_file_cand) work_dir
          |> List.hd)
      in
      Logging.log "Instrument Branch Printer %s (%s)" origin_file pt_file;
      (* TODO: clean up *)
      Cil.visitCilFile (new findTypeVisitor "_IO_FILE") cil;
      Cil.visitCilFile (new findGVarVisitor "stderr") cil;
      if Option.is_none !found_type || Option.is_none !found_gvar then ()
      else
        let fileptr = Cil.TPtr (Cil.TComp (Option.get !found_type, []), []) in
        let stream = Cil.makeGlobalVar "__inst_stream" fileptr in
        cil.globals <- Cil.GVarDecl (stream, Cil.locUnknown) :: cil.globals;
        Cil.visitCilFile (new functionInstrumentor function_table) cil

  let function_printer work_dir src_dir =
    let out_sig_file = open_out (work_dir ^ "/function_list.txt") in
    let function_table = Hashtbl.create 100000 in
    Utils.traverse_pp_file
      (fun pp_file ->
        let origin_file_opt = Utils.find_origin_file_opt pp_file in
        function_instrument work_dir origin_file_opt pp_file function_table)
      src_dir;
    Hashtbl.iter
      (fun (file, line) _ ->
        print_endline (file ^ ": " ^ (line |> string_of_int));
        Printf.fprintf out_sig_file "%s:%d\n" file line)
      function_table;

    close_out out_sig_file
end

let run work_dir =
  Cil.initCIL ();
  Cil.insertImplicitCasts := false;
  let src_dir = Filename.concat work_dir "src" in
  match !Cmdline.instrument with
  | Cmdline.Coverage -> Coverage.run work_dir src_dir
  | Cmdline.AssumeInject -> Coverage.assumeinject work_dir src_dir
  | Cmdline.ErrorCoverage | Cmdline.ErrorInject ->
      Coverage.errorinject work_dir src_dir
  | Cmdline.Filter -> Coverage.check_signal work_dir src_dir
  | Cmdline.BranchPrint -> Coverage.branch_printer work_dir src_dir
  | Cmdline.FunctionPrint -> Coverage.function_printer work_dir src_dir
  | _ -> ()
