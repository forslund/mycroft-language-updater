# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from github.Repository import Repository
from github import Github
from git import Git, GitCommandError

from subprocess import call
from os.path import join, splitext
import os
import shutil

CREDS = os.environ.get('GITHUB_ACCESS_KEY')
if CREDS:
    g = Github(CREDS)
else:
    g = None

class TempGit(Git):
    def __init__(self, url, name):
        self.tmp_path = join('/tmp/', name)
        call(['git', 'clone', url, self.tmp_path])
        super().__init__(self.tmp_path)

    def tmp_remove(self):
        shutil.rmtree(self.tmp_path)


def get_work_repos(upstream_url):
    # Github fork repo
    upstream_id, _= splitext(upstream_url.split('github.com/')[1])
    print(upstream_id)
    upstream = g.get_repo(upstream_id)
    print(upstream)
    fork = g.get_user().create_fork(upstream)
    print(fork)
    return (fork, upstream)


def create_work_dir(upstream, fork):
   # Clone from upstream
    tmp_repo = TempGit(upstream.clone_url, upstream.name)
    # Add fork
    tmp_repo.remote('add', 'work', fork.ssh_url)
    return tmp_repo


def create_or_edit_pr(branch, upstream, langs=[]):
    user = g.get_user()

    base = upstream.default_branch
    head = '{}:{}'.format(user.login, branch)
    pulls = list(upstream.get_pulls(base=base, head=head))
    title = 'Updated translations'.format(lang)
    body = 'Automatically generated PR from translate.mycroft.ai\n\n'
    body += 'The updated languages are:\n'
    for lang in langs:
        body += '- {}\n'.format(lang)

    pulls = list(upstream.get_pulls(base=base, head=head))
    if pulls:
        pull = pulls[0]
        pull.edit(title, body)
    else:
        return upstream.create_pull(title, body, base=base, head=head)
