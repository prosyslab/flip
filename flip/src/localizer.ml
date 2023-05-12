module F = Format
module LineCoverage = Coverage.LineCoverage
module LineCoverageInst = Coverage.LineCoverage2

module BugLocation = struct
  type t = Cil.location * float * float * float * int

  let pp fmt (l, score_neg, score_pos, score, score_time) =
    F.fprintf fmt "%s:%d\t%f %f %f %d" l.Cil.file l.Cil.line score_neg score_pos
      score score_time

  let pp_cov fmt (l, score_neg, score_pos, score, _score_time) =
    F.fprintf fmt "%s:%d,%d,%d,%f"
      (l.Cil.file |> Filename.basename)
      l.Cil.line (int_of_float score_pos) (int_of_float score_neg) score

  let pp_file fmt file = F.fprintf fmt "%s" file
end

let print_file bic_locations parent_locations resultname =
  let locations =
    List.fold_left
      (fun acc (l, s1, _, _, _) ->
        if List.mem (l.Cil.file |> Filename.basename) acc || s1 = 0. then acc
        else (l.Cil.file |> Filename.basename) :: acc)
      [] bic_locations
  in
  let locations =
    List.fold_left
      (fun acc (l, s1, _, _, _) ->
        if List.mem (l.Cil.file |> Filename.basename) acc || s1 = 0. then acc
        else (l.Cil.file |> Filename.basename) :: acc)
      locations parent_locations
  in
  let oc3 = Filename.concat !Cmdline.out_dir resultname |> open_out in
  let fmt3 = F.formatter_of_out_channel oc3 in
  List.iter (fun l -> F.fprintf fmt3 "%a\n" BugLocation.pp_file l) locations;
  close_out oc3

let print_coverage locations resultname =
  let oc2 = Filename.concat !Cmdline.out_dir resultname |> open_out in
  let fmt2 = F.formatter_of_out_channel oc2 in
  List.iter (fun l -> F.fprintf fmt2 "%a\n" BugLocation.pp_cov l) locations;
  close_out oc2;
  locations

let print locations resultname =
  let oc = Filename.concat !Cmdline.out_dir resultname |> open_out in
  let fmt = F.formatter_of_out_channel oc in
  List.iter (fun l -> F.fprintf fmt "%a\n" BugLocation.pp l) locations;
  close_out oc

let copy_src () =
  Unix.create_process "cp"
    [| "cp"; "-rf"; "src"; !Cmdline.out_dir |]
    Unix.stdin Unix.stdout Unix.stderr
  |> ignore;

  match Unix.wait () |> snd with
  | Unix.WEXITED 0 -> ()
  | Unix.WEXITED n ->
      () (*failwith ("Error " ^ string_of_int n ^ ": copy failed")*)
  | _ -> ()
(*failwith "copy failed"*)

let spec_localizer work_dir bug_desc localizer_list =
  let coverage =
    (* if !Cmdline.gcov then LineCoverage.run work_dir bug_desc
       else *)
    LineCoverageInst.run work_dir bug_desc
  in
  Logging.log "Coverage: %a" LineCoverageInst.pp coverage;
  copy_src ();
  let table = Hashtbl.create 99999 in
  List.fold_left
    (fun locs (e : LineCoverageInst.elem) ->
      (* print_endline (e.test ^ ", " ^ (e.test_result |> string_of_int)); *)
      let regexp_pos = Str.regexp "p.*" in
      Coverage.StrMap.fold
        (fun file lines locs ->
          let new_locs =
            if Str.string_match regexp_pos e.LineCoverageInst.test 0 then
              Coverage.IntMap.mapi
                (fun line num ->
                  ({ Cil.file; line; byte = 0 }, 0.0, 1.0, 0.0, e.test_result))
                lines
              |> Coverage.IntMap.bindings
              |> List.map (fun (_, v) -> v)
            else
              Coverage.IntMap.mapi
                (fun line num ->
                  ({ Cil.file; line; byte = 0 }, num, 0.0, 0.0, e.test_result))
                lines
              |> Coverage.IntMap.bindings
              |> List.map (fun (_, v) -> v)
          in
          List.rev_append new_locs locs)
        e.LineCoverageInst.coverage locs)
    [] coverage
  |> List.iter (fun (l, s1, s2, s3, s4) ->
         (* if s2 = 1.0 then print_endline (s4 |> string_of_int); *)
         match Hashtbl.find_opt table l with
         | Some (new_s1, new_s2, new_s3, new_s4) ->
             Hashtbl.replace table l
               (s1 +. new_s1, s2 +. new_s2, s3 +. new_s3, s4 + new_s4)
         | _ -> Hashtbl.add table l (s1, s2, s3, s4));
  if bug_desc.BugDesc.program = "php" then (
    Unix.create_process "sudo"
      [| "sudo"; "rm"; "-rf"; "/experiment/src/test/bad" |]
      Unix.stdin Unix.stdout Unix.stderr
    |> ignore;
    match Unix.wait () |> snd with
    | Unix.WEXITED 0 -> ()
    | Unix.WEXITED n -> failwith ("Error " ^ string_of_int n ^ ": rm bad failed")
    | _ -> failwith "rm bad failed");

  let spec_coverage =
    List.map
      (fun (l, (s1, s2, s3, s4)) ->
        (* print_endline (s4 |> string_of_int); *)
        (l, s1, s2, s3, s4))
      (List.of_seq (Hashtbl.to_seq table))
  in
  match localizer_list with
  | (v, _) :: _ -> v work_dir bug_desc spec_coverage
  | _ -> spec_coverage

let tarantula_localizer _work_dir bug_desc locations =
  let test_cases = bug_desc.BugDesc.test_cases in
  let pos_num =
    List.fold_left
      (fun acc t ->
        let regexp_pos = Str.regexp "p.*" in
        if Str.string_match regexp_pos t 0 then acc + 1 else acc)
      0 test_cases
  in
  let neg_num =
    List.fold_left
      (fun acc t ->
        let regexp_neg = Str.regexp "n.*" in
        if Str.string_match regexp_neg t 0 then acc + 1 else acc)
      0 test_cases
  in
  let taran_loc =
    List.map
      (fun (l, s1, s2, _, s4) ->
        let nep = s2 in
        let nnp = float_of_int pos_num -. s2 in
        let nef = s1 in
        let nnf = float_of_int neg_num -. s1 in
        let numer = nef /. (nef +. nnf) in
        let denom1 = nef /. (nef +. nnf) in
        let denom2 = nep /. (nep +. nnp) in
        let score = numer /. (denom1 +. denom2) in
        (l, s1, s2, score, s4))
      locations
  in
  List.stable_sort
    (fun (_, _, _, s13, _) (_, _, _, s23, _) ->
      if s23 > s13 then 1 else if s23 = s13 then 0 else -1)
    taran_loc

let ochiai_localizer _work_dir bug_desc locations =
  let test_cases = bug_desc.BugDesc.test_cases in
  let pos_num =
    List.fold_left
      (fun acc t ->
        let regexp_pos = Str.regexp "p.*" in
        if Str.string_match regexp_pos t 0 then acc + 1 else acc)
      0 test_cases
  in
  let neg_num =
    List.fold_left
      (fun acc t ->
        let regexp_neg = Str.regexp "n.*" in
        if Str.string_match regexp_neg t 0 then acc + 1 else acc)
      0 test_cases
  in
  let ochiai_loc =
    List.map
      (fun (l, s1, s2, _, s4) ->
        (* print_endline (s4 |> string_of_int); *)
        let nep = s2 in
        let _nnp = float_of_int pos_num -. s2 in
        let nef = s1 in
        let nnf = float_of_int neg_num -. s1 in
        let sub_denom1 = nef +. nnf in
        let sub_denom2 = nef +. nep in
        let denom = sqrt (sub_denom1 *. sub_denom2) in
        let score = nef /. denom in
        (l, s1, s2, score, s4))
      locations
  in
  List.stable_sort
    (fun (_, _, _, s13, _) (_, _, _, s23, _) ->
      if s23 > s13 then 1 else if s23 = s13 then 0 else -1)
    ochiai_loc

let jaccard_localizer _work_dir bug_desc locations =
  let test_cases = bug_desc.BugDesc.test_cases in
  let pos_num =
    List.fold_left
      (fun acc t ->
        let regexp_pos = Str.regexp "p.*" in
        if Str.string_match regexp_pos t 0 then acc + 1 else acc)
      0 test_cases
  in
  let neg_num =
    List.fold_left
      (fun acc t ->
        let regexp_neg = Str.regexp "n.*" in
        if Str.string_match regexp_neg t 0 then acc + 1 else acc)
      0 test_cases
  in
  let jaccard_loc =
    List.map
      (fun (l, s1, s2, _, s4) ->
        let nep = s2 in
        let _nnp = float_of_int pos_num -. s2 in
        let nef = s1 in
        let nnf = float_of_int neg_num -. s1 in
        let denom = nef +. nnf +. nep in
        let score = nef /. denom in
        (l, s1, s2, score, s4))
      locations
  in
  List.stable_sort
    (fun (_, _, _, s13, _) (_, _, _, s23, _) ->
      if s23 > s13 then 1 else if s23 = s13 then 0 else -1)
    jaccard_loc

let coverage work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Instrument.run scenario.work_dir;
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  if !Cmdline.engine = Cmdline.ErrorCoverage then
    Unix.system
      "sed -i '/\$makeENV{LC_ALL} = '\\''C'\\'';/a \$makeENV{__ENV_SIGNAL} = \
       \$ENV{__ENV_SIGNAL};' /experiment/src/tests/test_driver.pl"
    |> ignore

let check_signal work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Instrument.run scenario.work_dir;
  Unix.chdir scenario.Scenario.work_dir
(* Scenario.compile scenario bug_desc.BugDesc.compiler_type *)

let value_print work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Instrument.run scenario.work_dir;
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Logging.log "Start printing value";
  (* let _print_path = Filename.concat scenario.work_dir "output.txt" in *)
  List.iter
    (fun test ->
      let regexp_pos = Str.regexp "p.*" in
      if not (Str.string_match regexp_pos test 0) then (
        Unix.chdir scenario.Scenario.work_dir;
        Scenario.run_test scenario.test_script test bug_desc |> ignore;
        Unix.system
          ("mv /experiment/output.txt /experiment/output_" ^ test ^ ".txt")
        |> ignore))
    bug_desc.BugDesc.test_cases

let assume_inject work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  (* Instrument.run scenario.work_dir;
     Unix.chdir scenario.Scenario.work_dir;
     Scenario.compile scenario bug_desc.BugDesc.compiler_type; *)
  Unix.system
    "mv /experiment/src/sapi/cli/php /experiment/src/sapi/cli/php-test"
  |> ignore;
  (* Unix.system
       "sed -i \"s/cmd = \\[\\\"timeout\\\", \\\"60\\\", \
        \\\"sapi\\\\/cli\\\\/php\\\", test\\]/cmd = \\[\\\"timeout\\\", \
        \\\"60\\\", \\\"sapi\\\\/cli\\\\/php-test\\\", \\\"run-tests.php\\\", \
        \\\"-p\\\", \\\"sapi\\\\/cli\\\\/php\\\", test\\]/g\" \
        /experiment/tester.py"
     |> ignore; *)
  Unix.chdir scenario.Scenario.work_dir;
  spec_localizer work_dir bug_desc [ (ochiai_localizer, "ochiai") ]
  |> Fun.flip print "result.txt"

let error_inject work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  (* Unix.system "./stderr.sh" |> ignore; *)
  Unix.system
    "sed -i '/\$makeENV{LC_ALL} = '\\''C'\\'';/a \$makeENV{__ENV_SIGNAL} = \
     \$ENV{__ENV_SIGNAL};' /experiment/src/tests/test_driver.pl"
  |> ignore;
  List.iter
    (fun test ->
      let regexp_neg = Str.regexp "n.*" in
      if Str.string_match regexp_neg test 0 then (
        Unix.chdir scenario.Scenario.work_dir;
        Unix.system ("./test.sh " ^ test ^ " 2>" ^ test ^ ".log") |> ignore))
    bug_desc.BugDesc.test_cases;
  (* Unix.system
       "mv /experiment/src/sapi/cli/php /experiment/src/sapi/cli/php-test"
     |> ignore; *)
  Unix.chdir scenario.Scenario.work_dir;
  spec_localizer work_dir bug_desc [ (ochiai_localizer, "ochiai") ]
  |> Fun.flip print "result.txt"

let error_run work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  (* List.iter
     (fun test ->
       let regexp_neg = Str.regexp "n.*" in
       if Str.string_match regexp_neg test 0 then (
         Unix.chdir scenario.Scenario.work_dir;
         Unix.system ("./test.sh " ^ test ^ " 2>" ^ test ^ ".log") |> ignore))
     bug_desc.BugDesc.test_cases; *)
  (* Unix.system
       "mv /experiment/src/sapi/cli/php /experiment/src/sapi/cli/php-test"
     |> ignore; *)
  Unix.chdir scenario.Scenario.work_dir;
  spec_localizer work_dir bug_desc [ (ochiai_localizer, "ochiai") ]
  |> Fun.flip print "result.txt"

let branch_printer work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Instrument.run scenario.work_dir;
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type

let function_printer work_dir bug_desc =
  let scenario = Scenario.init ~stdio_only:true work_dir in
  Unix.chdir scenario.Scenario.work_dir;
  Scenario.compile scenario bug_desc.BugDesc.compiler_type;
  Instrument.run scenario.work_dir

let run work_dir =
  Logging.log "Start localization";
  let bug_desc = BugDesc.read work_dir in
  if bug_desc.BugDesc.program = "make" || bug_desc.BugDesc.program = "grep" then
    Cmdline.corebench := true;
  Logging.log "Bug desc: %a" BugDesc.pp bug_desc;
  let localizer = spec_localizer in
  match !Cmdline.engine with
  | Cmdline.Tarantula ->
      localizer work_dir bug_desc [ (tarantula_localizer, "tarantula") ]
      |> Fun.flip print "result_tarantula.txt"
  | Cmdline.Ochiai ->
      localizer work_dir bug_desc [ (ochiai_localizer, "ochiai") ]
      |> Fun.flip print "result_ochiai.txt"
  | Cmdline.ErrorCoverage | Cmdline.Coverage -> coverage work_dir bug_desc
  | Cmdline.ValuePrint -> value_print work_dir bug_desc
  | Cmdline.AssumeInject -> assume_inject work_dir bug_desc
  | Cmdline.ErrorInject -> error_inject work_dir bug_desc
  | Cmdline.ErrorRun -> error_run work_dir bug_desc
  | Cmdline.Filter -> check_signal work_dir bug_desc
  | Cmdline.BranchPrint -> branch_printer work_dir bug_desc
  | Cmdline.FunctionPrint -> function_printer work_dir bug_desc
  | _ -> ()
