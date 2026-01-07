"""Non-worktree sdlc_zte workflow entrypoint.

Currently delegates to worktree-isolated implementation.
"""

from cxc.workflows.wt.sdlc_zte_iso import main as iso_main


def main() -> None:
    print("NOTE: reg workflows currently delegate to wt/*_iso; non-worktree versions are not restored yet.")
    iso_main()


if __name__ == "__main__":
    main()
