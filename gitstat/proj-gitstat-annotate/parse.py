#!/usr/bin/python3

import sys
import os.path
import re
import subprocess


def ProcessCommit(word_fiff, full_diff, i, j, old_start, old_len, new_start, new_len):
    pass


def GetLogs(path, commit1, commit2):
    dir = os.path.dirname(path)
    git_cmd = ("git", "-C", dir)
    git_worddiff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w", "--word-diff", "%s..%s" % (commit1, commit2), "--", path)
    git_fulldiff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w",                "%s..%s" % (commit1, commit2), "--", path)
    print("! git_worddiff_cmd = ", git_worddiff_cmd, file = sys.stderr)
    word_diff_run = subprocess.Popen(git_worddiff_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
    word_diff = []
    for line in word_diff_run.stdout:
        word_diff.append(line.decode())
    full_diff_run = subprocess.Popen(git_fulldiff_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
    full_diff = []
    for line in full_diff_run.stdout:
        full_diff.append(line.decode())
    print("!", len(word_diff), len(full_diff), file=sys.stderr)
    return word_diff, full_diff


def ProcessLog(path, commit1, commit2):
    word_diff, full_diff = GetLogs(path, commit1, commit2)
    i = j = 0
    while i < len(word_diff):
        commit_id1 = re.search("(?<=commit )[a-z0-9]+", word_diff[i]).group()
        commit_id2 = re.search("(?<=commit )[a-z0-9]+", full_diff[j]).group()
        if commit_id1 != commit_id2:
            exit("Unmatched commits")
        print(commit_id1)
        while i < len(word_diff) and word_diff[i][0:2] != "@@":
            i += 1
            j += 1
        while i < len(word_diff) and word_diff[i][0:2] == "@@":
            find = re.search("(?<=@@ )-(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?(?= @@)", word_diff[i]).groups()
            print("!", find, file=sys.stderr)

            i += 1
            j += 1
            while i < len(word_diff) and word_diff[i][0:2] != "@@" and word_diff[i][0:6] != "commit":
                i += 1
            while j < len(full_diff) and full_diff[j][0:2] != "@@" and full_diff[j][0:6] != "commit":
                j += 1


def main():
    if len(sys.argv) != 3:
        exit("Wrong args")
    print("! args =", sys.argv, file=sys.stderr)
    commit1, commit2 = re.search("(.*):(.*)", sys.argv[1]).groups()
    file = os.path.abspath(sys.argv[2])
    ProcessLog(file, commit1, commit2)

if __name__ == "__main__":
    main()
