#!/usr/bin/python3

import sys
import os.path
import re
import subprocess
import treap


def ProcessCommit(word_diff, full_diff, word_diff_pos, full_diff_pos, old_start, old_len, new_start, new_len, root):
    word_diff_len = max(old_len, new_len)
    old_pos = 0
    new_pos = 0

    root, treap_tail = treap.Split(root, new_start + old_len - 1)  # sic!
    treap_head, treap_old = treap.Split(root, new_start - 1)
    treap_new = None
    # print("!! after cut (%d %d): %d %d %d" % (new_start + old_len - 1, new_start - 1, treap.Size(treap_head), treap.Size(treap_old), treap.Size(treap_tail)))

    for i in range(word_diff_len):
        line = word_diff[word_diff_pos + i]
        old_line = re.subn(r"\{\+.*?\+\}", "", line)[0]
        old_line = re.subn(r"\[\-(.*?)\-\]", r'\1', old_line)[0]
        new_line = re.subn(r"\[\-.*?\-\]", "", line)[0]
        new_line = re.subn(r"\{\+(.*?)\+\}", r'\1', new_line)[0]
        # print("!! %d: \"%s\"\n!!    \"%s\"\n!!    \"%s\"" % (i, line.replace("\r", "\\r").replace("\n", "\\n"), old_line.replace("\r", "\\r").replace("\n", "\\n"), new_line.replace("\r", "\\r").replace("\n", "\\n")))
        # print(
        #     "!! X  \"%s\" %d\n!! X  \"%s\" %d" %
        #     (
        #         full_diff[full_diff_pos + old_pos][1].replace("\r", "\\r").replace("\n", "\\n"),
        #         full_diff[full_diff_pos + old_pos][1] == old_line,
        #         full_diff[full_diff_pos + old_len + new_pos][1].replace("\r", "\\r").replace("\n", "\\n"),
        #         full_diff[full_diff_pos + old_len + new_pos][1] == new_line
        #     )
        # )
        is_in_old = is_in_new = False
        if old_pos < old_len and full_diff[full_diff_pos + old_pos][1:] == old_line:
            is_in_old = True
        if new_pos < new_len and full_diff[full_diff_pos + old_len + new_pos][1:] == new_line:
            is_in_new = True
        assert is_in_old or is_in_new
        changes = 0
        if is_in_old and is_in_new:
            changes = len(re.findall("\[\-.*?\-\]?\{\+.*?\+\}?", line))
        # print(
        #     "! %s -> %s, %s" %
        #     (
        #         str(old_start + old_pos) if is_in_old else "/dev/null",
        #         str(new_start + new_pos) if is_in_new else "/dev/null",
        #         changes
        #     )
        # )
        if is_in_old:
            treap_old_row, treap_old = treap.Split(treap_old, 1)
            if is_in_new:
                treap_old_row.value += changes
                treap_new = treap.Merge(treap_new, treap_old_row)
        if is_in_new and not is_in_old:
            treap_new = treap.Merge(treap_new, treap.Treap())
        if is_in_old:
            old_pos += 1
        if is_in_new:
            new_pos += 1

    return treap.Merge(treap_head, treap.Merge(treap_new, treap_tail))


def InitParsing(path, commit1, commit2):
    dir = os.path.dirname(path)
    git_cmd = ("git", "-C", dir)
    git_word_diff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w", "--word-diff", "%s..%s" % (commit1, commit2), "--", path)
    git_full_diff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w",                "%s..%s" % (commit1, commit2), "--", path)

    subprocess.Popen(git_cmd + ("checkout", commit1, "--", path), stdout=subprocess.PIPE).wait()
    initial_len = subprocess.Popen(("wc", "-l", path), stdout=subprocess.PIPE).communicate()[0].decode()[:-1]
    initial_len = int(re.match(".*(?= )", initial_len).group())
    subprocess.Popen(git_cmd + ("checkout", "HEAD", "--", path), stdout=subprocess.PIPE).wait()
    # print("! initial_len = %d" % initial_len)

    word_diff_run = subprocess.Popen(git_word_diff_cmd, stdout=subprocess.PIPE)
    word_diff = []
    for line in word_diff_run.stdout:
        word_diff.append(line.decode())
    full_diff_run = subprocess.Popen(git_full_diff_cmd, stdout=subprocess.PIPE)
    full_diff = []
    for line in full_diff_run.stdout:
        full_diff.append(line.decode())
    # print("!", len(word_diff), len(full_diff), file=sys.stderr)
    return word_diff, full_diff, treap.Build(initial_len)


def ProcessLog(path, commit1, commit2):
    word_diff, full_diff, root = InitParsing(path, commit1, commit2)
    i = j = 0
    while i < len(word_diff):
        commit_id1 = re.search("(?<=commit )[a-z0-9]+", word_diff[i]).group()
        commit_id2 = re.search("(?<=commit )[a-z0-9]+", full_diff[j]).group()
        if commit_id1 != commit_id2:
            exit("Unmatched commits")
        # print(commit_id1)
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
            # print("!", (old_pos, old_len, new_pos, new_len))
            i += 1
            j += 1
            root = ProcessCommit(word_diff, full_diff, i, j, old_pos, old_len, new_pos, new_len, root)
            while i < len(word_diff) and word_diff[i][0:2] != "@@" and word_diff[i][0:6] != "commit":
                i += 1
            while j < len(full_diff) and full_diff[j][0:2] != "@@" and full_diff[j][0:6] != "commit":
                j += 1
    # print("!!", root.size)
    file = [x.strip('\n') for x in open(path).readlines()]
    treap.Out(root, file)


def main():
    if len(sys.argv) != 3:
        exit("Wrong args")
    commit1, commit2 = re.search("(.*):(.*)", sys.argv[1]).groups()
    file = os.path.abspath(sys.argv[2])
    ProcessLog(file, commit1, commit2)

if __name__ == "__main__":
    main()
