# !/bin/bash

# This is not used now but in the future should be run during installation/setup
# of picata. When doing so, it should check to see whether a set_env.sh file
# exists. If it does not, then it should create it by prompting the user for
# their canvas url and token, and then populate the appropriate env vars in the
# newly created set_env.sh file. From that point on the user won't need this
# script any longer and they will only need to call the set_env.sh script (which
# is also in .gitignore in order to ensure tokens are not uploaded to github).

# check if set_env.sh exists...

# if it does not:
echo "Creating script: set_env.sh"

# if it does, then don't do anything (or print the current url and token to see
# if the user wants to change them)


