# This script fixes up the output of bzr fast-export command
# so it can be properly imported into another VCS
#
# For instance, for importing _one_ branch into git;
#
#   cd ..
#   mkdir -p stoq-git
#   cd stoq-git
#   git init
#   bzr fast-export ../stoq | \
#     sed -f ../stoq/tools/bzr-fast-export-fixup.sed | \
#     git fast-import
#   git reset --hard master
#

# This is a bug in bzr fast-export related to renames
/^R / {
  s,R data/sql/patch-02-27.sql data/sql/patch-02-26.sql,,g
}

# Fix up the broken author and use async.com.br email
# addresses as much as possible.
/^\(author\|committer\) / {
  s/<Alberto>/Alberto Alvarez <alberto.alvarez81@gmail.com>/g
  s/Alberto <>/Alberto Alvarez <alberto.alvarez81@gmail.com>/g
  s/Alberto Alvarez <>/Alberto Alvarez <alberto.alvarez81@gmail.com>/g
  s/Alberto Alavarez/Alberto Alvarez/g
  s/<batosti>/Andre Batosti <batosti@async.com.br>/g
  s/batosti <>/Andre Batosti <batosti@async.com.br>/g
  s/<brg>/Bruno Garcia <brg@async.com.br>/g
  s/brg <>/Bruno Garcia <brg@async.com.br>/g
  s/<daniel>/Daniel Saran R. Da Cunha <daniel@async.com.br>/g
  s/daniel <>/Daniel Saran R. Da Cunha <daniel@async.com.br>/g
  s/<evandro>/Evandro Vale Miquelito <evandro@async.com.br>/g
  s/evandro <>/Evandro Vale Miquelito <evandro@async.com.br>/g
  s/<fabio>/Fabio Morbec <fabio@async.com.br>/g
  s/fabio <>/Fabio Morbec <fabio@async.com.br>/g
  s/Gabriel Gerga <gergagabriel@gmail.com>/Gabriel Gerga <gerga@async.com.br>/g
  s/<gergagabriel@gmail.com>/Gabriel Gerga <gerga@async.com.br>/g
  s/gergagabriel@gmail.com <>/Gabriel Gerga <gerga@async.com.br>/g
  s/<george>/George Kussumoto <george@async.com.br>/g
  s/george <>/George Kussumoto <george@async.com.br>/g
  s/georgeyk <georgeyk.dev@gmail.com>/George Kussumoto <george@async.com.br>/g
  s/georgeyk <georgeyk@blackbird>/George Kussumoto <george@async.com.br>/g
  s/george <george@memento>/George Kussumoto <george@async.com.br>/g
  s/<gjc>/Gustavo Carneiro <gjc@inescporto.pt>/g
  s/<hackedbellini>/Thiago Bellini <hackedbellini@async.com.br>/g
  s/<hackedbellini@async.com.br>/Thiago Bellini <hackedbellini@async.com.br>/g
  s/hackedbellini <>/Thiago Bellini <hackedbellini@async.com.br>/g
  s/hackedbellini@async.com.br <>/Thiago Bellini <hackedbellini@async.com.br>/g
  s/<henrique>/Henrique Romano <henrique@async.com.br>/g
  s/henrique <>/Henrique Romano <henrique@async.com.br>/g
  s/<jvdm>/Joao Victor Duarte Martins <jvdm@async.com.br>/g
  s/jvdm <>/Joao Victor Duarte Martins <jvdm@async.com.br>/g
  s/<jdahlin@async.com.br>/Johan Dahlin <jdahlin@async.com.br>/g
  s/jdahlin@async.com.br <>/Johan Dahlin <jdahlin@async.com.br>/g
  s/<johan@async.com.br>/Johan Dahlin <jdahlin@async.com.br>/g
  s/johan@async.com.br <>/Johan Dahlin <jdahlin@async.com.br>/g
  s/<johan@gnome.org>/Johan Dahlin <jdahlin@async.com.br>/g
  s/johan@gnome.org <>/Johan Dahlin <jdahlin@async.com.br>/g
  s/<jdahlin>/Johan Dahlin <jdahlin@async.com.br>/g
  s/jdahlin <>/Johan Dahlin <jdahlin@async.com.br>/g
  s/Johan Dahlin Johan Dahlin/Johan Dahlin/g
  s/<Launchpad>/Launchpad Translations <nobody@async.com.br>/g
  s/Launchpad Translations on behalf of stoq-dev <>/Launchpad Translations <nobody@async.com.br>/g
  s/<lincoln>/Lincoln Molica <lincoln@async.com.br>/g
  s/lincoln <>/Lincoln Molica <lincoln@async.com.br>/g
  s/<romaia>/Ronaldo Maia <romaia@async.com.br>/g
  s/romaia <>/Ronaldo Maia <romaia@async.com.br>/g
  s/Ronaldo Maia <mainha+lp@gmail.com>/Ronaldo Maia <romaia@async.com.br>/g
  s/<silvio>/Silvio Rangel <silvio@async.com.br>/g
  s/silvio <>/Silvio Rangel <silvio@async.com.br>/g
  s/silvio <silvio@sylar>/Silvio Rangel <silvio@async.com.br>/g
  s/Silvio Rangel <silvio@lost>/Silvio Rangel <silvio@async.com.br>/g
  s/Silvio Rangel <silvio@ubuntu>/Silvio Rangel <silvio@async.com.br>/g
  s/silvio-async <silvio@async.com.br>/Silvio Rangel <silvio@async.com.br>/g
  s/Thiago Bellini <thiago.bellini@hackedbellini.org>/Thiago Bellini <hackedbellini@async.com.br>/g
  s/Thiago Bellini <hackedbellini@gmail.com>/Thiago Bellini <hackedbellini@async.com.br>/g
}
