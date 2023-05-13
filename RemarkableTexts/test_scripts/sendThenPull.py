#!/usr/bin/env python3

# this file borrows heavily from https://github.com/cherti/remarkable-cli-tooling/resync.py.
# because of that, the project in this folder inherits a GPL3-License.

import sys
import os
import time
import json
import shutil
import argparse
import uuid
import subprocess
import tempfile
import pathlib
import urllib.request
import re
import datetime
from google.cloud import vision

document = './new_texts_pdf/8234567890.pdf'

default_prepdir = tempfile.mkdtemp(prefix="resync-")
ssh_socketfile = '/tmp/remarkable-push.socket'

def gen_did():
    return str(uuid.uuid4())

def gen_metadata(name, parent_id=''):
    return {
        "visibleName": name,
        "parent": parent_id,
        "lastModified": str(int(time.time()*1000)),
        "metadatamodified": False,
        "modified": False,
        "pinned": False,
        "synced": False,
        "type": "DocumentType",
        "version": 0,
        "deleted": False,
        "lastOpened": str(int(time.time()*1000)),
        "lastOpenedPage": 0
    }

def get_metadata_by_uuid(u):
    raw_metadata = subprocess.getoutput(f'ssh -S {ssh_socketfile} root@10.11.99.1 "cat .local/share/remarkable/xochitl/{u}.metadata"')
    metadata = json.loads(raw_metadata)
    if metadata['deleted'] or metadata['parent'] == 'trash':
        return None
    else:
        return metadata

def get_metadata_by_visibleName(name):
    cmd = f'ssh -S {ssh_socketfile} root@10.11.99.1 "grep -lF \'\\"visibleName\\": \\"{name}\\"\' .local/share/remarkable/xochitl/*.metadata"'
    res = subprocess.getoutput(cmd)

    reslist = []
    if res != '':
        for result in res.split('\n'):
            try:
                _, _, _, _, filename = result.split('/')
            except ValueError:
                continue

            u, _ = filename.split('.')

            metadata = get_metadata_by_uuid(u)
            if metadata:
                reslist.append((u, metadata))

    return reslist

class Node:

    def __init__(self, name, parent=None, filetype=None, document=None):

        self.name = name
        self.filetype = filetype
        self.doctype = 'CollectionType' if filetype == 'folder' else 'DocumentType'
        self.parent = parent
        self.children = []
        if filetype in ['pdf', 'epub']:
            if document is not None:
                self.doc = document
            else:
                raise TypeError("No document provided for file node " + name)

        self.id = None
        self.exists = False
        self.gets_modified = False

        # now retrieve the document ID for this document if it already exists
        metadata = get_metadata_by_visibleName(self.name)

        # first, we filter the metadata we got for those that are actually in the same location
        # in the document tree that this node is, i.e. same parent and same document type
        filtered_metadata = []
        for (did, md) in metadata:

            # ˇ (is root node) or (has matching parent) ˇ
            location_match = (self.parent is None and md['parent'] == '') or (self.parent is not None and self.parent.id == md['parent'])
            type_match = self.doctype == md['type']
            if location_match and type_match:
                # only keep metadata at the same location in the filesystem tree
                filtered_metadata.append((did, md))


        if len(filtered_metadata) == 1:

            # ok, we have a document already in place at this node_point that fits the position in the document tree
            # first, get unpack its metadata and assign the document id
            did, md = metadata[0]
            self.id = did
            self.initial_md = md
            self.exists = True

        elif len(filtered_metadata) > 1 and args.conflict_behavior in ['skip', 'replace', 'replace-pdf-only'] and args.mode == 'push':
            # ok, something is still ambiguous, but for what we want to do we cannot have that.
            # Hence, we error out here as the risk of breaking something is too great at this point.
            destination_name = self.parent.name if self.parent is not None else 'toplevel'
            msg = f"File or folder {self.name} occurs multiple times in destination {destination_name}. Situation ambiguous, cannot decide how to proceed."
            print(msg, file=sys.stderr)
            sys.exit(1)


    def __repr__(self):
        return self.get_full_path()


    def add_child(self, node):
        self.children.append(node)


    def get_full_path(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.get_full_path() + '/' + self.name


    def render_common(self, prepdir):
        """
        renders all files that are shared between the different DocumentTypes
        """

        if self.id is None:
            self.id = gen_did()

        with open(f'{prepdir}/{self.id}.metadata', 'w') as f:
            if self.parent:
                metadata = gen_metadata(self.name, parent_id=self.parent.id)
            else:
                metadata = gen_metadata(self.name)
            json.dump(metadata, f, indent=4)

        with open(f'{prepdir}/{self.id}.content', 'w') as f:
            json.dump({}, f, indent=4)


    def render(self, prepdir):
        """
        This renders the given note, including DocumentType specifics;
        needs to be reimplemented by the subclasses
        """
        raise Exception("Rendering not implemented")


    def build_downwards(self):
        """
        This creates a document tree for all nodes that are direct and indirect
        descendants of this node.
        """
        if self.filetype != 'folder':
            # documents don't have children, this one's easy
            return

        cmd = f'ssh -S {ssh_socketfile} root@10.11.99.1 "grep -lF \'\\"parent\\": \\"{self.id}\\"\' .local/share/remarkable/xochitl/*.metadata"'
        children_uuids = set([pathlib.Path(d).stem for d in subprocess.getoutput(cmd).split('\n')])
        if '' in children_uuids:
            # if we get an empty string here, there are no children to this folder
            return

        for chu in children_uuids:
            md = get_metadata_by_uuid(chu)
            if md['type'] == "CollectionType":
                ch = Folder(md['visibleName'], parent=self)
            else:

                name = md['visibleName']

                if not name.endswith('.pdf'):
                    name += '.pdf'

                ch = Document(name, parent=self)

            ch.id = chu
            self.add_child(ch)
            ch.build_downwards()


    def download(self, targetdir=pathlib.Path.cwd()):
        os.chdir(targetdir)
        print('downloading to ' + str(targetdir))

        # documents we need to actually download
        filename = self.name if self.name.lower().endswith('.pdf') else f'{self.name}.pdf'
        try:
            resp = urllib.request.urlopen(f'http://10.11.99.1/download/{self.id}/placeholder')
            with open(filename, 'wb') as f:
                f.write(resp.read())
        except urllib.error.URLError as e:
            print(f"{e.reason}: Is the web interface enabled? (Settings > Storage > USB web interface)")
            sys.exit(2)


class Document(Node):

    def __init__(self, document, parent=None):

        docpath = pathlib.Path(document)
        filetype = docpath.suffix[1:] if docpath.suffix.startswith('.') else docpath.suffix

        super().__init__(docpath.name, parent=parent, filetype=filetype, document=docpath)


    def render(self, prepdir):
        """
        renders an actual DocumentType tree node
        """
        if not self.exists:

            self.render_common(prepdir)

            os.makedirs(f'{prepdir}/{self.id}')
            os.makedirs(f'{prepdir}/{self.id}.thumbnails')
            shutil.copy(self.doc, f'{prepdir}/{self.id}.{self.filetype}')


class Folder(Node):

    def __init__(self, name, parent=None):
        super().__init__(name, parent=parent, filetype='folder')


    def render(self, prepdir):
        """
        renders a folder tree node
        """
        if not self.exists:
            self.render_common(prepdir)

        for ch in self.children:
            ch.render(prepdir)


def identify_node(name, parent=None):
    """
    infer a node's type by name and location, and return a node object
    in case this is unambiguously possible
    """
    metadata = get_metadata_by_visibleName(name)
    candidates = []

    for u, md in metadata:
        # location_match = (is root node) or (has matching parent)
        location_match = (parent is None and md['parent'] == '') or (parent is not None and parent.id == md['parent'])
        if location_match:
            candidates.append((u, md))

    if len(candidates) == 1:
        u, md = candidates[0]
        return Document(name, parent=parent) if md['type'] == 'DocumentType' else Folder(name, parent=parent)
    else:
        return None


def get_toplevel_files():
    cmd = f'ssh -S {ssh_socketfile} root@10.11.99.1 "grep -lF \'\\"parent\\": \\"\\"\' .local/share/remarkable/xochitl/*.metadata"'
    toplevel_candidates = set([pathlib.Path(d).stem for d in subprocess.getoutput(cmd).split('\n')])

    toplevel_files = []
    for u in toplevel_candidates:
        md = get_metadata_by_uuid(u)
        if md is not None:
            toplevel_files.append(md['visibleName'])

    return toplevel_files


def push_to_remarkable(document, destination=None):

    def construct_node_tree_from_disk(basepath, parent=None):
        path = pathlib.Path(basepath)

        node = Document(path, parent=parent)

        if node.exists:
            node.exists = False
            node.gets_modified = True

        return node

    node = construct_node_tree_from_disk(document)
    node.render(default_prepdir)

    subprocess.call(f'scp -r {default_prepdir}/* root@10.11.99.1:.local/share/remarkable/xochitl', shell=True)
    subprocess.call(f'ssh -S {ssh_socketfile} root@10.11.99.1 systemctl restart xochitl', shell=True)

    return node


def pull_from_remarkable(document, destination=None):
    destination_directory = pathlib.Path.cwd()

    *parents, target = document.split('/')
    local_anchor = None
    if parents:
        local_anchor = Folder(parents[0], parent=None)
        for par in parents[1:]:

            new_node = Folder(par, parent=local_anchor)
            local_anchor.add_child(new_node)
            local_anchor = new_node

    new_node = identify_node(target, parent=local_anchor)

    if new_node is not None:
        new_node.build_downwards()
        new_node.download(targetdir=destination_directory)



def getFileDate(u):
    try:
        date = subprocess.getoutput(f'ssh -S {ssh_socketfile} root@10.11.99.1 "stat -c \'%z\' .local/share/remarkable/xochitl/{node.id}"')
        return datetime.datetime.strptime(date.split('.')[0], '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print('FAILED TO GET FILE CTIME: ' + str(e))
        return None

def fileUpdated(t1, t2):
    no_difference = datetime.timedelta(0)
    try:
        return (t1-t2 != no_difference)
    except:
        return False


def checkInDocument():
    try:
        lastLog = subprocess.getoutput(f'ssh -S {ssh_socketfile} root@10.11.99.1 "journalctl -u xochitl | grep \'rm.documentlockmanager\' | tail -1"')

        if("Opening" in lastLog):
            return True

        return False
    except:
        return False
        

ssh_connection = None
try:
    ssh_connection = subprocess.Popen(f'ssh -o ConnectTimeout=1 -M -N -q -S {ssh_socketfile} root@10.11.99.1', shell=True)

    # quickly check if we actually have a functional ssh connection (might not be the case right after an update)
    checkmsg = subprocess.getoutput(f'ssh -S {ssh_socketfile} root@10.11.99.1 "/bin/true"')

    if checkmsg != "":
        print("ssh connection does not work, verify that you can manually ssh into your reMarkable. ssh itself commented the situation with:")
        print(checkmsg)
        ssh_connection.terminate()
        sys.exit(255)

    #push but keep node
    node = push_to_remarkable(document)
    print(node)
    
    print('GET DATES')
    last_modified = getFileDate(node.id)
    time.sleep(5)

    for i in range(20*4): #for 2 min
        time.sleep(3)
        new_modified = getFileDate(node.id)
        if fileUpdated(last_modified, new_modified):
            print('FILE UPDATED')
        last_modified = new_modified
        if checkInDocument():
            print('in doc')
        else:
            print('not in doc')

    #redownload
    node.download()




finally:
    if ssh_connection is not None:
        ssh_connection.terminate()
    if os.path.exists(default_prepdir):  # we created this
        shutil.rmtree(default_prepdir)
