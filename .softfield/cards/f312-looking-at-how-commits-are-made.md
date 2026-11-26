# Milestone F312: Tidier commit messages, with the owner as author and true co-authors

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-26.

## Notes
Looking at how commits are made, i'd like to tidy a bit the commit messages. why is 'F124-PAUSE-ONE-PROJECT-FROM-THE-PROJECTS signed off by the owner' upper case? -- no need for 'by the owner' jst something like signed off is enough, same for planted. -- by copliot-auto is fine no need for 'standing in for claude' -- commits should follow good commit message convention with a limit on title characters and message characters, in most cases the title of the ticket might be enough and then more details in the message -- this part is useless on commit messages, the diff is something you can get from git, not the message: Changed:
  .softfield/developer.md                    +1 -1
  factory_dashboard/templates/projects.html  +23 -4
  tests/factory_dashboard/test_projects.py   +83 -0 -- on github there's a lot of softfield runner co-authored. sometimes it's claude, sometimes it's the runner and sometimes it's my local agent? i wonder how to make the co-author more accurate and also when i do commits with claude it attributes them to claude and they have a whole github profile and everything, but softfield runner doesn't so it's just a non-clikcable grey profile co authored with me. all of it should stay co-authored with me, i just wonder how to make more accurate and interesting
