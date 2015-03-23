GIT_EXTERNAL_DIFF=`pwd`/diff-only-numbers git -C `dirname $1` log -p --ext-diff $1
