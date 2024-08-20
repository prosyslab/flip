let work_dir : string option ref = ref None
let out_dir = ref "localizer-out"
let faulty_func = ref false

type instrument =
  | DfSan
  | GSA
  | Coverage
  | ErrorCoverage
  | ValuePrint
  | AssertInject
  | AssumeInject
  | ErrorInject
  | Filter
  | BranchPrint
  | FunctionPrint
  | Nothing

let instrument = ref Nothing
let inject_file = ref ""
let inject_line = ref 0

let select_instrument s =
  match s with
  | "dfsan" -> instrument := DfSan
  | "gsa" -> instrument := GSA
  | "coverage" | "value_print" | "inject" -> instrument := Coverage
  | _ -> failwith "Unknown instrument"

let skip_compile = ref false

type engine =
  | Tarantula
  | Prophet
  | Jaccard
  | Ochiai
  | Dummy
  | UniVal
  | Coverage
  | ErrorCoverage
  | ValuePrint
  | AssertInject
  | AssumeInject
  | ErrorInject
  | ErrorRun
  | Filter
  | BranchPrint
  | FunctionPrint
  | All

let engine = ref Dummy

let select_engine s =
  match s with
  | "tarantula" ->
      engine := Tarantula;
      instrument := Coverage
  | "prophet" ->
      engine := Prophet;
      instrument := Coverage
  | "jaccard" ->
      engine := Jaccard;
      instrument := Coverage
  | "ochiai" ->
      engine := Ochiai;
      instrument := Coverage
  | "dummy" ->
      engine := Dummy;
      instrument := Coverage
  | "unival" ->
      engine := UniVal;
      instrument := GSA
  | "coverage" ->
      engine := Coverage;
      instrument := Coverage
  | "error_coverage" ->
      engine := ErrorCoverage;
      instrument := ErrorCoverage
  | "value_print" ->
      engine := ValuePrint;
      instrument := ValuePrint
  | "assert" ->
      engine := AssertInject;
      instrument := AssertInject
  | "assume" ->
      engine := AssumeInject;
      instrument := AssumeInject
  | "error" ->
      engine := ErrorInject;
      instrument := ErrorInject
  | "error_run" ->
      engine := ErrorRun;
      instrument := Nothing
  | "filter" ->
      engine := Filter;
      instrument := Filter
  | "branch_print" ->
      engine := BranchPrint;
      instrument := BranchPrint
  | "function_print" ->
      engine := FunctionPrint;
      instrument := FunctionPrint
  | "all" ->
      engine := All;
      instrument := Coverage
  | _ -> failwith "Unknown engine"

let jobs = ref 0 (* i.e., #cpus *)
let blacklist = ref []
let gnu_source = ref false
let no_seg = ref false
let mmap = ref false
let fun_level = ref false
let block_level = ref false
let fun_signal = ref false
let advantage = ref false
let corebench = ref false
let gcov = ref false

let options =
  [
    ("-outdir", Arg.Set_string out_dir, "Output directory");
    ( "-instrument",
      Arg.String select_instrument,
      "Specify instrument method (default: Nothing)" );
    ("-faulty_func", Arg.Set faulty_func, "Set faulty functions");
    ("-skip_compile", Arg.Set skip_compile, "Skip compilation");
    ( "-engine",
      Arg.String select_engine,
      "Specify localization engine (default: Dummy)" );
    ("-j", Arg.Set_int jobs, "Number of parallel jobs for make (default: -j)");
    ( "-blacklist",
      Arg.String (fun x -> blacklist := x :: !blacklist),
      "Blacklist for instrumentation" );
    ( "-gnu_source",
      Arg.Set gnu_source,
      "Add #define _GNU_SOURCE when instrumentation for some programs (e.g., \
       gimp)" );
    ( "-no_seg",
      Arg.Set no_seg,
      "Do not instrument fflush after every line if there is no segfault" );
    ("-gcov", Arg.Set gcov, "Use gcov when extracting coverage");
    ("-inject_file", Arg.Set_string inject_file, "Target file for injection");
    ("-inject_line", Arg.Set_int inject_line, "Target line for injection");
    ("-mmap", Arg.Set mmap, "Using mmap to print coverage");
    ("-fun_level", Arg.Set fun_level, "Using function level coverage");
    ("-block_level", Arg.Set block_level, "Using block level coverage");
    ("-advantage", Arg.Set advantage, "Using advantage using slice");
    ("-corebench", Arg.Set corebench, "Using corebench docker");
    ( "-fun_signal",
      Arg.Set fun_signal,
      "Using signal power using function coverage" );
  ]

let parse_arg x =
  work_dir := Some x;
  ()
