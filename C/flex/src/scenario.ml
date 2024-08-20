type t = {
  work_dir : string;
  compile_script : string;
  test_script : string;
  coverage_data : string;
}

let file_instrument filename preamble =
  let read_whole_file filename =
    let ch = open_in filename in
    let s = really_input_string ch (in_channel_length ch) in
    close_in ch;
    s
  in
  let c_code = read_whole_file filename in
  let instr_c_code = preamble ^ c_code in
  let oc = open_out filename in
  Printf.fprintf oc "%s" instr_c_code;
  close_out oc

let file_instrument_all work_dir preamble =
  let rec traverse_file f root_dir =
    let files = Sys.readdir root_dir in
    Array.iter
      (fun file ->
        let file_path = Filename.concat root_dir file in
        if (Unix.lstat file_path).st_kind = Unix.S_LNK then ()
        else if List.mem file !Cmdline.blacklist then ()
        else if Sys.is_directory file_path then traverse_file f file_path
        else if Filename.extension file = ".c" then f file_path preamble
        else ())
      files
  in
  traverse_file file_instrument work_dir

let init ?(stdio_only = false) work_dir =
  let work_dir =
    if Filename.is_relative work_dir then
      Filename.concat (Unix.getcwd ()) work_dir
    else work_dir
  in
  {
    work_dir;
    compile_script = Filename.concat work_dir "compile.sh";
    test_script = Filename.concat work_dir "test.sh";
    coverage_data = Filename.concat work_dir "coverage.xml";
  }

let simple_compiler compile_script =
  Unix.create_process compile_script [| compile_script |] Unix.stdin Unix.stdout
    Unix.stderr
  |> ignore;
  match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n ->
      failwith ("Error " ^ string_of_int n ^ ": " ^ compile_script ^ " failed")
  | _ -> failwith (compile_script ^ " failed")

let make () =
  let jobs =
    if !Cmdline.jobs = 0 then "-j" else "-j" ^ string_of_int !Cmdline.jobs
  in
  Unix.create_process "make" [| "make"; jobs |] Unix.stdin Unix.stdout
    Unix.stderr
  |> ignore;
  match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n -> failwith ("Error " ^ string_of_int n ^ ": make failed")
  | _ -> failwith "make failed"

let configure () =
  Unix.create_process "./configure"
    [|
      "./configure";
      "CFLAGS=--coverage -save-temps=obj -Wno-error";
      "CXXFLAGS=--coverage -save-temps=obj";
      "LDFLAGS=-lgcov --coverage";
    |]
    Unix.stdin Unix.stdout Unix.stderr
  |> ignore;
  (match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n ->
      failwith ("Error " ^ string_of_int n ^ ": configure failed")
  | _ -> failwith "configure failed");
  if !Cmdline.corebench then (
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > po/Makefile"
    |> ignore;
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > doc/Makefile"
    |> ignore)
  else ()

let make_clean () =
  if !Cmdline.corebench then (
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > po/Makefile"
    |> ignore;
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > doc/Makefile"
    |> ignore);
  Unix.create_process "make" [| "make"; "clean" |] Unix.stdin Unix.stdout
    Unix.stderr
  |> ignore;
  match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n ->
      failwith ("Error " ^ string_of_int n ^ ": make clean failed")
  | _ -> failwith "make clean failed"

let make_distclean () =
  if !Cmdline.corebench then (
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > po/Makefile"
    |> ignore;
    Unix.system "echo \"all: ;\nclean: ;\ndistclean: ;\" > doc/Makefile"
    |> ignore);
  Unix.create_process "make" [| "make"; "distclean" |] Unix.stdin Unix.stdout
    Unix.stderr
  |> ignore;
  match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n ->
      failwith ("Error " ^ string_of_int n ^ ": make distclean failed")
  | _ -> failwith "make distclean failed"

let configure_and_make () =
  Unix.chdir "src";
  make_clean ();
  make_distclean ();
  configure ();
  Unix.system
    "sed -i \"s/all_targets = \\$(OVERALL_TARGET) \\$(PHP_MODULES) \
     \\$(PHP_ZEND_EX) \\$(PHP_BINARIES) pharcmd/all_targets = \
     \\$(OVERALL_TARGET) \\$(PHP_MODULES) \\$(PHP_ZEND_EX) \
     \\$(PHP_BINARIES)/g\" /experiment/src/Makefile"
  |> ignore;
  Unix.system
    "sed -i ‘/\$makeENV{LC_ALL} = ’\\’‘C’\\‘’;/a \$makeENV{__ENV_SIGNAL} = \
     \$ENV{__ENV_SIGNAL};' /experiment/src/tests/test_driver.pl"
  |> ignore;
  make ()

let compile scenario compiler_type =
  match compiler_type with
  | "compile" -> simple_compiler scenario.compile_script
  | "configure-and-make" -> configure_and_make ()
  | _ -> failwith "Unknown compiler"
(* if !Cmdline.engine = ErrorInject then Unix.system "/experiment/stderr.sh" |> ignore *)

let run_test test_script name bug_desc =
  Unix.create_process test_script [| test_script; name |] Unix.stdin Unix.stdout
    Unix.stderr
  |> ignore;
  let regexp_pos = Str.regexp "p.*" in
  if Str.string_match regexp_pos name 0 then
    let test_result =
      if bug_desc.BugDesc.program = "php" then (
        Unix.wait () |> ignore;
        Unix.system
          "mv /experiment/coverage_data/tmp /experiment/coverage_data/tmp_bak"
        |> ignore;
        Unix.system "mkdir /experiment/coverage_data/tmp" |> ignore;
        Unix.system
          "sed -i \"s/cmd = \\[\\\"timeout\\\", \\\"60\\\", \
           \\\"sapi\\\\/cli\\\\/php\\\", test\\]/cmd = \\[\\\"timeout\\\", \
           \\\"60\\\", \\\"sapi\\\\/cli\\\\/php-test\\\", \
           \\\"run-tests.php\\\", \\\"-p\\\", \\\"sapi\\\\/cli\\\\/php\\\", \
           test\\]/g\" /experiment/tester.py"
        |> ignore;
        Unix.create_process test_script [| test_script; name |] Unix.stdin
          Unix.stdout Unix.stderr
        |> ignore;
        let result = Unix.wait () |> snd in
        Unix.system
          "sed -i \"s/cmd = \\[\\\"timeout\\\", \\\"60\\\", \
           \\\"sapi\\\\/cli\\\\/php-test\\\", \\\"run-tests.php\\\", \
           \\\"-p\\\", \\\"sapi\\\\/cli\\\\/php\\\", test\\]/cmd = \
           \\[\\\"timeout\\\", \\\"60\\\", \\\"sapi\\\\/cli\\\\/php\\\", \
           test\\]/g\" /experiment/tester.py"
        |> ignore;
        Unix.system "rm -rf /experiment/coverage_data/tmp" |> ignore;
        Unix.system
          "mv /experiment/coverage_data/tmp_bak /experiment/coverage_data/tmp"
        |> ignore;
        result)
      else Unix.wait () |> snd
    in
    match test_result with Unix.WEXITED 0 -> 1 | _ -> 0
  else (
    Unix.wait () |> ignore;
    0)
