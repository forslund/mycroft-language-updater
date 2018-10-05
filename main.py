import sys
import os
from os.path import join, basename, exists
from glob import glob
from datetime import date
from requests import get

import polib
from github_actions import get_work_repos, create_work_dir, create_or_edit_pr

DEFAULT_BRANCH = '18.08'
SKILLS_URL = ('https://raw.githubusercontent.com/MycroftAI/mycroft-skills/'
              '{}/.gitmodules')

def get_skill_repos(branch=None):
    """ Fetches the skill list from the mycroft-skills repo and returns
        a dict mapping paths to urls

        Arguments:
            branch: branch of the repo to use

        Returns: dict with path-url pairs
    """
    branch = branch or DEFAULT_BRANCH
    response = get(SKILLS_URL.format(branch))
    skills = response.text.split('\n')

    d = {}
    key = None
    for l in skills:
        if 'path = ' in l:
            key = l.split(' = ')[1].strip()
        elif key and 'url = ' in l:
            d[key] = l.split(' = ')[1].strip()
            key = None
        else:
            key = None
    return d


def skill_from_po(po_file):
    """ removes -<Lang-code>.po and returns skill name

    Ex. cocktails-sv.po -> cocktails,
        skill-alarm-de.po -> skill-alarm
    """
    return '-'.join(basename(po_file).split('-')[:-1])


def download_lang(lang):
    # TODO
    # build url for language code

    # use wget module to download

    # use zip to unpack

    return path # Path to directory with po_files


def is_translated(path):
    """ Checks if all files in the translation has at least one translation.

    Arguments:
        path (str): path to po-file

    Returns: True if all files in translation has at least one translation,
             otherwise False.
    """
    po = polib.pofile(path)
    files = []
    for e in po:
        files += [f[0] for f in e.occurrences]
    all_files = sorted(set(files))
    translated_entities = [e for e in po if e.translated()]
    files = []
    for e in translated_entities:
        files += [f[0] for f in e.occurrences]
    translated_files = sorted(set(files))

    return translated_files == all_files


def parse_po_file(path):
    """ Create dictionary with translated files as key containing
    the file content as a list.

    Arguments:
        path: path to the po-file of the translation

    Returns:
        Dictionary mapping files to translated content
    """
    out_files = {}  # Dict with all the files of the skill
    # Load the .po file
    po = polib.pofile(path)

    for entity in po:
        for out_file, _ in entity.occurrences:
            f = out_file.split('/')[-1] # Get only the filename
            content = out_files.get(f, [])
            content.append(entity.msgstr)
            out_files[f] = content

    return out_files


def insert_translation(path, translation):
    for filename in translation:
        with open(join(path, filename), 'w+') as f:
            f.writelines([l + '\n' for l in translation[filename]])


def main():
    skill_repos = get_skill_repos()
    for lang in languages:
        po_dir = get_language(lang)

        # for all po files
        # use glob to get all po-files in the directory that is translated
        for f in [po for  po in glob(join(po_dir, '*')) if is_translated(po)]:
            print('Processing {}'.format(f))

            translation = parse_po_file(f)
            # Get git repo and github connections
            skill_url = skill_repos[skill_from_po(f)]
            fork, upstream = get_work_repos(skill_url)
            work = create_work_dir(upstream, fork)

            # Modify repo
            # Checkout new branch
            branch = 'translate-' + str(date.today())
            work.checkout('-b', branch)

            if 'locale' in os.listdir(work.tmp_path):
                path = join('locale', lang)
                if not exists(join(work.tmp_path,path)):
                    os.mkdir(join(work.tmp_path, path))
                else:
                    work.rm(join(path, '*'))  # Remove all files
                # insert new translations
                insert_translations(join(work.tmp_path, path), translations)
                work.add(join(path, '*'))  # add the new files
            else:
                # handle dialog directory
                path = join('dialog', lang)
                if not exists(join(work.tmp_path,path)):
                    os.mkdir(join(work.tmp_path, path))
                else:
                    work.rm(join(path, '*'))  # Remove all files
                insert_translation(join(work.tmp_path, path),
                    {k: translation[k] for k in translation if
                        k.endswith('.dialog')})
                insert_translation(join(work.tmp_path, path),
                    {k: translation[k] for k in translation if
                        k.endswith('.list')})
                work.add(join(path, '*'))  # add the new files
                # handle vocab directory
                path = join('vocab', lang)
                if not exists(join(work.tmp_path,path)):
                    os.mkdir(join(work.tmp_path, path))
                else:
                    work.rm(join(path, '*'))  # Remove all files
                insert_translation(join(work.tmp_path, path),
                    {k: translation[k] for k in translation if
                        k.endswith('.intent')})
                insert_translation(join(work.tmp_path, path),
                    {k: translation[k] for k in translation if
                        k.endswith('.voc')})
                insert_translation(join(work.tmp_path, path),
                    {k: translation[k] for k in translation if
                        k.endswith('.entity')})
                work.add(join(path, '*'))  # add the new files
                # Handle regex dir
                path = join('regex', lang)
                if exists(join(work.tmp_path, 'regex')):
                    if not exists(join(work.tmp_path,path)):
                        os.mkdir(join(work.tmp_path, path))
                    else:
                        work.rm(join(path, '*'))  # Remove all files
                    insert_translation(join(work.tmp_path, path),
                        {k: translation[k] for k in translation if
                            k.endswith('.rx')})
            # Commit
            work.commit('-m', 'Update translations')
            # Push branch to fork
            work.push('-f', 'work', branch)
            # Open PR
            create_or_edit_pr(branch, upstream, lang)
            work.tmp_remove()
