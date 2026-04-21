# Usage

Once you have [installed](installation.md) LayOpt in your virtual environment you will have the command line programme
`layopt` available.

## Accessing Help

`layopt` and its sub-commands have the flag `--help` (or `-h` for short) which shows the available options.

```shell
(.venv) ❱ layopt --help
usage: layopt [-h] [-v] [-c CONFIG_FILE] [-b BASE_DIR] [-o OUTPUT_DIR] [-l LOG_LEVEL] [-j CORES]
  {optimise,create-config} ...

Run layopt.

options:
  -h, --help            show this help message and exit
  -v, --version         Report the current version of Layopt that is installed
  -c, --config-file CONFIG_FILE
                        Path to a YAML configuration file.
  -o, --output-dir OUTPUT_DIR
                        Output directory to write results to.
  -l, --log-level LOG_LEVEL
                        Set verbosity of logging, options (least verbose to most) are 'error', 'warning', 'info', 'error', 'debug'.
  -j, --cores CORES     Number of cores to use for parallel processing.

program:
  Available processing options are :

  {optimise,create-config}
    optimise            Run LayOpt
    create-config       Create a configuration file using the defaults.
```

There are generic options available that control the configuration file used, if any, the output directory, log-level
and the number of cores to use when running in parallel.

There are two "program" or sub-commands available `optimise` and `create-config`

### `layopt create-config`

This program will write a copy of the `default_config.yaml` to disk, users can specify the location to write to and the
filename. This will be a [YAML][yaml] file with comments indicating what parameters are and can be edited by the user to
control how `layopt` is run. `layopt cretae-config` also has help available using the `-h`/`--help flag`.

```shell
(.venv) ❱ layopt create-config --help
usage: layopt create-config [-h] [-f FILENAME] [-o OUTPUT_DIR] [-m MODULE] [-c CONFIG]

Create a configuration file using the defaults.

options:
  -h, --help            show this help message and exit
  -f, --filename FILENAME
                        Name of YAML file to save configuration to (default 'config.yaml').
  -o, --output-dir OUTPUT_DIR
                        Path to where the YAML file should be saved (default './' the current directory).
  -m, --module MODULE   The AFM module to use, currently `afmslicer` (default).
  -c, --config CONFIG   Configuration to use, currently only 'default' is supported.
```

### `layopt optimise`

The `optimise` program runs the analysis. If no configuration file is specified then the packages `default_config.yaml`
will be used. Typically though users will want to use `layopt create-config` to create their own configuration file,
edit parameters and use those. To use your own configuration file you would then run...

```shell
layopt --config-file my_custom_config.yaml
```

If the `output_dir` has not been modified results will be in the `output/` directory where you will find a `.csv` file
of results and a `.yaml` which reflects the parameters used in running the optimisation. `layopt optimise` also has help
available using the `-h`/`--help` flag.

```shell
(.venv) ❱ layopt optimise --help
usage: layopt optimise [-h] [--width WIDTH] [--height HEIGHT] [--stress-tensile STRESS_TENSILE]
  [--stress-compressive STRESS_COMPRESSIVE] [--joint-cost JOINT_COST]
  [--load-direction LOAD_DIRECTION [LOAD_DIRECTION ...]] [--load-large LOAD_LARGE]
  [--load-small LOAD_SMALL] [--max-length MAX_LENGTH]
  [--filter-levels FILTER_LEVELS [FILTER_LEVELS ...]] [--primal-method PRIMAL_METHOD]
  [--problem-name PROBLEM_NAME] [--save-to-csv SAVE_TO_CSV] [--csv-filename CSV_FILENAME]
  [--notes NOTES]

Run Layopt

options:
  -h, --help            show this help message and exit
  --width WIDTH         Width of structure.
  --height HEIGHT       Height of structure.
  --stress-tensile STRESS_TENSILE
                        Tensile stress limit.
  --stress-compressive STRESS_COMPRESSIVE
                        Compressive stress limit.
  --joint-cost JOINT_COST
                        Joint cost.
  --load-direction LOAD_DIRECTION [LOAD_DIRECTION ...]
                        Load direction.
  --load-large LOAD_LARGE
                        Large load to apply at each load point.
  --load-small LOAD_SMALL
                        Small load to apply at each load point.
  --max-length MAX_LENGTH
                        Maximum member length.
  --filter-levels FILTER_LEVELS [FILTER_LEVELS ...]
                        Member area filtering levels.
  --primal-method PRIMAL_METHOD
                        Primal violation method.
  --problem-name PROBLEM_NAME
                        Problem name
  --save-to-csv SAVE_TO_CSV
                        Whether to save output to '.csv' file.
  --csv-filename CSV_FILENAME
                        File to save results to. Defaults to 'results_<YYYY-MM-DD-hhmmss>.csv'.
  --notes NOTES         Additional notes.
```

These options allow the user to override any parameter in a configuration file as the precedence for configuration
options is `default_config.yaml` < `--config-file <user_custom_config.yaml>` < `layopt optimise <--flags>`.

For example if you wanted to run with a custom configuration file, but increase the value for `load_large` to `200` but
didn't want to edit your `.yaml` you can

```shell
(.venv) ❱ layopt --config-file my_custom_config.yaml optimise --load-large 200
```

## Results

Results are saved to the `output_dir` defined in the configuration file, which by default is `output`, or the user
specified `--output-dir <directory>`. To avoid over-writing results and configuration files they are date/time stamped
with `YY-MM-DD-hhmmss` included in the filenames. Most of the time these will match for the `.csv` and `.yaml`, on rare
occasions there may be a slight difference in the seconds values.

## Interactive use

Layopt can be used interactively in the Python REPL (Read-eval-print loop) shell. An example session using
[iPython][ipython] is shown below. `layopt.trussopt()` returns a tuple of `volume`, `a`, a dataframe of results and the
`filter_level`.

```shell
ipython

In [1]: from layopt.layopt import trussopt

In [2]: import numpy as np

In [3]: parameters = {
    "width": 1,
    "height": 1,
    "stress_tensile": 1.0,
    "stress_compressive": 1.0,
    "joint_cost": 0.0,
    "loaded_points": np.asarray([[3, 3]]),
    "load_direction": np.asarray([0.0, -1.0]),
    "load_large": 50.0,
    "load_small": 5.0,
    "max_length": 18.0,
    "support_points": np.asarray([[]]),
    "primal_method": "load_factor",
    "problem_name": "short cantilever",
    "notes": "short cantilever test",
}

In [4]: results = layopt.trussopt(**parameters)
   ...:
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:make_pattern_loads:414 - Total patterns for 1 load point(s) : 2
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:make_pattern_loads:417 - Base case (all large) : pt0=L
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:trussopt:854 - Setup took 0.0011236679999999666
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:trussopt:855 -     Nodes               : 4
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:trussopt:856 -     Members             : 6
2026-04-20 09:58:30.666 | INFO     | layopt.layopt:trussopt:857 -     Total load patterns : 2
2026-04-20 09:58:30.669 | INFO     | layopt.layopt:trussopt:900 - Iteration: 1, vol: 149.9999999955983, mems: 6 active load cases:1/2
2026-04-20 09:58:30.672 | INFO     | layopt.layopt:trussopt:900 - Iteration: 2, vol: 149.9999999955983, mems: 6 active load cases:1/2
2026-04-20 09:58:30.676 | INFO     | layopt.layopt:trussopt:958 - Volume: 149.9999999955983
2026-04-20 09:58:30.676 | INFO     | layopt.layopt:trussopt:960 - Solve took 0.0137718109999998
2026-04-20 09:58:30.677 | INFO     | layopt.layopt:trussopt:961 - Active patterns: 1/2

In
```

[ipython]: https://ipython.org/
[yaml]: https://yaml.org
