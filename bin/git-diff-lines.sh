GIT_EXTERNAL_DIFF=`pwd`/diff-only-numbers git -C `dirname $1` diff HEAD~100..HEAD $1
