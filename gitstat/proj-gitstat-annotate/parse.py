#!/usr/bin/python3

import sys
import os.path
import re
import subprocess
import treap


def NormalizeString(str):
    # Dumb one!
    return " " + " ".join(re.split("[ \t\n]+", str)) + " "

def ProcessCommit(word_diff, full_diff, word_diff_pos, full_diff_pos, old_start, old_len, new_start, new_len, root):
    word_diff_len = max(old_len, new_len)
    old_pos = 0
    new_pos = 0

    # print("!! initial size = %d" % treap.Size(root))
    root, treap_tail = treap.Split(root, new_start + old_len - 1)  # sic!
    treap_head, treap_old = treap.Split(root, new_start - 1)
    treap_new = None
    # print("!! after cut (%d %d): %d %d %d" % (new_start + old_len - 1, new_start - 1, treap.Size(treap_head), treap.Size(treap_old), treap.Size(treap_tail)))

    i = 0
    while old_pos < old_len or new_pos < new_len:
        # print("!!! old: %d/%d new:%d/%d" % (old_pos, old_len, new_pos, new_len))
        word_diff_old_line = word_diff_new_line = ""
        changes = 0
        was_prev_del = False
        while word_diff[word_diff_pos + i] != "~\n":
            next_line = word_diff[word_diff_pos + i]
            i += 1
            if next_line[0] != '+':
                word_diff_old_line += next_line[1:-1]
            elif was_prev_del:
                changes += 1
            if next_line[0] != '-':
                word_diff_new_line += next_line[1:-1]
            was_prev_del = next_line[0] == '-'
        i += 1
        word_diff_old_line = NormalizeString(word_diff_old_line)
        word_diff_new_line = NormalizeString(word_diff_new_line)

        full_diff_old_line = full_diff_new_line = ""
        is_in_old = is_in_new = False
        full_diff_old_len = full_diff_new_len = 0
        if old_pos < old_len:
            full_diff_old_line = NormalizeString(full_diff[full_diff_pos + old_pos][1:-1])
            full_diff_old_len = 1
            while len(full_diff_old_line) < len(word_diff_old_line) and full_diff_old_line == word_diff_old_line[:len(full_diff_old_line)]:
                full_diff_old_line += full_diff[full_diff_pos + old_pos + full_diff_old_len][1:-1]
                full_diff_old_line = NormalizeString(full_diff_old_line)
                full_diff_old_len += 1
            if full_diff_old_line == word_diff_old_line:
                is_in_old = True
                old_pos += full_diff_old_len

        if new_pos < new_len:
            full_diff_new_line = NormalizeString(full_diff[full_diff_pos + old_len + new_pos][1:-1])
            full_diff_new_len = 1
            while len(full_diff_new_line) < len(word_diff_new_line) and full_diff_new_line == word_diff_new_line[:len(full_diff_new_line)]:
                full_diff_new_line += full_diff[full_diff_pos + old_len + new_pos + full_diff_new_len][1:-1]
                full_diff_new_line = NormalizeString(full_diff_new_line)
                full_diff_new_len += 1
            if full_diff_new_line == word_diff_new_line:
                is_in_new = True
                new_pos += full_diff_new_len

        # print("!! %d:\n!!    \"%s\"\n!!    \"%s\"" % (i, word_diff_old_line.replace("\r", "\\r").replace("\n", "\\n"), word_diff_new_line.replace("\r", "\\r").replace("\n", "\\n")))
        # print(
        #     "!! X  \"%s\" %d %d (took %d)\n!! X  \"%s\" %d %d (took %d)" %
        #     (
        #         full_diff_old_line.replace("\r", "\\r").replace("\n", "\\n"),
        #         full_diff_old_line == word_diff_old_line, is_in_old, full_diff_old_len,
        #         full_diff_new_line.replace("\r", "\\r").replace("\n", "\\n"),
        #         full_diff_new_line == word_diff_new_line, is_in_new, full_diff_new_len
        #     )
        # )
        assert is_in_old or is_in_new
        # print(
        #     "! %s -> %s, %s" %
        #     (
        #         str(old_start + old_pos) if is_in_old else "/dev/null",
        #         str(new_start + new_pos) if is_in_new else "/dev/null",
        #         changes
        #     )
        # )
        if is_in_old:
            treap_old_row, treap_old = treap.Split(treap_old, full_diff_old_len)
            if is_in_new:
                sum_value = treap.Sum(treap_old_row) + changes
                treap_new = treap.Merge(treap_new, treap.Build(full_diff_new_len, sum_value / full_diff_new_len))
        if is_in_new and not is_in_old:
            treap_new = treap.Merge(treap_new, treap.Build(full_diff_new_len))

    # print("!! final size = %d" % treap.Size(treap_new))
    root = treap.Merge(treap_head, treap.Merge(treap_new, treap_tail))
    # print("!! after merge size = %d" % treap.Size(root))
    return root


def InitParsing(path, commit1, commit2):
    dir = os.path.dirname(path)
    git_cmd = ("git", "-C", dir)
    git_word_diff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w", "--word-diff=porcelain",
                                   "--reverse", "%s..%s" % (commit1, commit2), "--", path)
    git_full_diff_cmd = git_cmd + ("log", "-p", "--no-color", "-U0", "-w",
                                   "--reverse", "%s..%s" % (commit1, commit2), "--", path)

    subprocess.Popen(git_cmd + ("checkout", commit1 + "^", "--", path), stdout=subprocess.PIPE).wait()
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
