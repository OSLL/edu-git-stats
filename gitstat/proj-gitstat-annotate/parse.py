#!/usr/bin/python3

import sys
import os.path
import re
import subprocess


def ProcessCommit(word_diff, full_diff, word_diff_pos, full_diff_pos, old_start, old_len, new_start, new_len):
    def return_match(match):
        # print("!!! matched:", match)
        return match.group(1)

    word_diff_len = max(old_len, new_len)
    full_diff_len = old_len + new_len
    old_pos = 0
    new_pos = 0
    for i in range(word_diff_len):
        line = word_diff[word_diff_pos + i]
        old_line = re.subn("\{\+.*?\+\}", "", line)[0]
        old_line = re.subn("\[\-(.*?)\-\]", return_match, old_line)[0]
        new_line = re.subn("\[\-.*?\-\]", "", line)[0]
        new_line = re.subn("\{\+(.*?)\+\}", return_match, new_line)[0]
        print("!! %d: \"%s\"\n!!    \"%s\"\n!!    \"%s\"" % (i, line[:-1], old_line[:-1], new_line[:-1]))
        print(
            "!! X  \"%s\" %d\n!! X  \"%s\" %d" %
            (
                full_diff[full_diff_pos + old_pos][1:-1],
                full_diff[full_diff_pos + old_pos][1:] == old_line,
                full_diff[full_diff_pos + old_len + new_pos][1:-1],
                full_diff[full_diff_pos + old_len + new_pos][1:] == new_line
            )
        )
        is_in_old = is_in_new = False
        if old_pos < old_len and full_diff[full_diff_pos + old_pos][1:] == old_line:
            is_in_old = True
        if new_pos < new_len and full_diff[full_diff_pos + old_len + new_pos][1:] == new_line:
            is_in_new = True
        assert is_in_old or is_in_new
        changes = 0
        if is_in_old and is_in_new:
            changes = len(re.findall("\[\-.*?\-\]?\{\+.*?\+\}?", line))
        print(
            "! %s -> %s, %s" %
            (
                str(old_start + old_pos) if is_in_old else "/dev/null",
                str(new_start + new_pos) if is_in_new else "/dev/null",
                changes
            )
        )
        if is_in_old:
            old_pos += 1
        if is_in_new:
            new_pos += 1



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
        i += 1
        j += 1
        while i < len(word_diff) and word_diff[i][0:2] != "@@" and word_diff[i][0:6] != "commit":
            i += 1
            j += 1
        while i < len(word_diff) and word_diff[i][0:2] == "@@":
            find = re.search("(?<=@@ )-(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?(?= @@)", word_diff[i]).groups()
            old_pos = int(find[0])
            old_len = int(find[1]) if not find[1] is None else 1
            new_pos = int(find[2])
            new_len = int(find[3]) if not find[3] is None else 1
            print("!", (old_pos, old_len, new_pos, new_len))
            i += 1
            j += 1
            ProcessCommit(word_diff, full_diff, i, j, old_pos, old_len, new_pos, new_len)
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
