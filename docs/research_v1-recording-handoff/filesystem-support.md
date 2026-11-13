# Durable file-recorder platform contract

Engineering implementation: sequential exclusive writer on a local POSIX filesystem that supports same-directory atomic rename/replace, hard-link create-if-absent, file fsync and directory fsync. On macOS every file acknowledgment additionally requires F_FULLFSYNC. Unsupported synchronization fails closed; there is no flush-only fallback.

Available test host: Python 3.12 Intel macOS, temporary directories on /System/Volumes/Data, reported by mount as local journaled APFS. File flush/fsync/F_FULLFSYNC, directory fsync, exclusive creation, same-filesystem link/replace, injected publication/sync failures and real subprocess exits are exercised. These are software/OS durability interfaces, not a physical power-cut or controller/cache guarantee.

- Atomic metadata/final output: stage in destination directory; sync bytes; replace or hard-link create-if-absent; sync directory. Visibility after failed directory sync is not successful acknowledgment. Keep originals and crash leftovers for disposition.
- Attempts: exclusive journal files, stable IDs, durable start before dispatch and terminal before advancing. A write/sync failure poisons the writer. No concurrency, shared-writer or advisory-lock coordination is promised; exclusive run directories and file creation provide ownership.
- Recovery: strict newline-terminated JSONL, duplicate/start/terminal links, request/setup identity, retained explicit states. Torn or invalid files and started-without-terminal ambiguity block automatic retry. Completed but incomplete/missing report outcomes remain incomplete. Resume writes a new directory and preserves originals.
- Windows: NOT supported/certified by this implementation's POSIX directory synchronization path. The authentic calibration host was Windows/Python 3.10. Tabmayee must either choose a separately approved POSIX recording environment with reviewed source/cost compatibility or obtain a separately reviewed Windows persistence implementation. Do not infer portability from os.replace alone.
- Linux/other POSIX, network filesystems, containers with special mounts and actual deployment storage: not exercised here. Required primitives must succeed and platform-specific tests must pass before certifying a future run. Physical exactly-once external execution is not claimed.

Local engineering validation can support code review while the actual collection platform remains an explicit blocker. No platform choice or calibration reuse is approved by these tests.
