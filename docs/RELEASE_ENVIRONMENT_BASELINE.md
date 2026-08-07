# Local release-environment baseline

Captured on 2026-08-04 in `<RELEASE_ROOT>` before the repair.

## Required command output

### `py -0p`

```text
The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

### `where.exe python`

```text
<TEMP_WORKSPACE>\Anaconda\python.exe
<TEMP_WORKSPACE>\AppData\Local\Microsoft\WindowsApps\python.exe
```

### `python --version`

```text
Python 3.13.5
```

### `conda info --envs`

```text
# conda environments:
#
labtest                <TEMP_WORKSPACE>\.conda\envs\labtest
wei-mcat               <TEMP_WORKSPACE>\.conda\envs\wei-mcat
base                 * <TEMP_WORKSPACE>\Anaconda
DL                     <TEMP_WORKSPACE>\Anaconda\envs\DL
OC                     <TEMP_WORKSPACE>\Anaconda\envs\OC
airwayq                <TEMP_WORKSPACE>\Anaconda\envs\airwayq
ocpserver311_new       <TEMP_WORKSPACE>\Anaconda\envs\ocpserver311_new
```

## Direct interpreter probes

```text
<TEMP_WORKSPACE>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe  3.12.13
<TEMP_WORKSPACE>\.conda\envs\labtest\python.exe                                      3.10.20
<TEMP_WORKSPACE>\.conda\envs\wei-mcat\python.exe                                      3.13.14
<TEMP_WORKSPACE>\Anaconda\envs\DL\python.exe                                                                 3.9.18
<TEMP_WORKSPACE>\Anaconda\envs\OC\python.exe                                                                 3.14.1
<TEMP_WORKSPACE>\Anaconda\envs\airwayq\python.exe                                                            3.11.15
<TEMP_WORKSPACE>\Anaconda\envs\ocpserver311_new\python.exe                                                   3.11.15
```

The selected bootstrap interpreter is the available Python 3.12.13. No package is installed into Conda base or any other global/non-project environment.
