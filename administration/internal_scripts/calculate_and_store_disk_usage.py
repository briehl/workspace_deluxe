'''
Created on Apr 27, 2014

@author: crusherofheads

Calculate disk usage and object counts  by user, separated into public vs.
private and deleted vs. undeleted data.

These figures are not actually related to the physical disk space for three
reasons:
1) The workspace saves space by only keeping one copy of each unique
    document. From the perspective of user disk usage, this feature is ignored.
2) Copies in the workspace are copies by reference, not by value. Again,
    from the perspective of user disk usage, this feature is ignored.
3) Only actual data objects are included (e.g. data stored in GridFS or Shock).
    Any data stored in MongoDB (other than GridFS files) is not included.

All versions are included in the counts and disk usage statistics.

Don't run this during high loads - runs through every object in the DB
Hasn't been optimized much either
'''


from __future__ import print_function
from configobj import ConfigObj
from pymongo import MongoClient
import time
import sys
import os
from collections import defaultdict

# where to get credentials (don't check these into git, idiot)
CFG_FILE_DEFAULT = 'usage.cfg'
CFG_SECTION_SOURCE = 'SourceMongo'
CFG_SECTION_TARGET = 'TargetMongo'

CFG_HOST = 'host'
CFG_PORT = 'port'
CFG_DB = 'db'
CFG_USER = 'user'
CFG_PWD = 'pwd'

# collection names
COL_WS = 'workspaces'
COL_ACLS = 'workspaceACLs'
COL_OBJ = 'workspaceObjects'
COL_VERS = 'workspaceObjVersions'

PUBLIC = 'pub'
PRIVATE = 'priv'

WS_OBJ_CNT = 'numObj'
DELETED = 'del'
OWNER = 'owner'

OBJ_CNT = 'objs'
BYTES = 'b'


LIMIT = 10000
OR_QUERY_SIZE = 100  # 75 was slower, 150 was slower
MAX_WS = 10  # for testing, set to < 1 for all ws


def chunkiter(iterable, size):
    """Iterates over an iterable in chunks of size size. Returns an iterator
  that in turn returns iterators over the iterable that each iterate through
  size objects in the iterable.
  Note that since the inner and outer loops are pulling values from the same
  iterator, continue and break don't necessarily behave exactly as one would
  expect. In the outer loop of the iteration, continue effectively does
  nothing, but break works normally. In the inner loop, break has no real
  effect but continue works normally. For the latter issue, wrapping the inner
  iterator in a tuple will cause break to skip the remaining items in the
  iterator. Alternatively, one can set a flag and exhaust the inner iterator.
  """
    def inneriter(first, iterator, size):
        yield first
        for _ in xrange(size - 1):
            yield iterator.next()
    it = iter(iterable)
    while True:
        yield inneriter(it.next(), it, size)


def process_optional_key(configObj, section, key):
    v = configObj[section].get(key)
    v = None if v == '' else v
    configObj[section][key] = v
    return v


def get_config():
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]
    else:
        cfgfile = CFG_FILE_DEFAULT
    if not os.path.isfile(cfgfile) and not os.access(cfgfile, os.R_OK):
        print ('Cannot read file ' + cfgfile)
        sys.exit(1)
    co = ConfigObj(cfgfile)
    s = CFG_SECTION_SOURCE
    t = CFG_SECTION_TARGET

    for sec in (s, t):
        if sec not in co:
            print('Missing config section {} from file {}'.format(
                  sec, cfgfile))
            sys.exit(1)
        for key in (CFG_HOST, CFG_PORT, CFG_DB):
            v = co[sec].get(key)
            if v == '' or v is None:
                print('Missing config value {}.{} from file {}'.format(
                    sec, key, cfgfile))
                sys.exit(1)
        try:
            co[sec][CFG_PORT] = int(co[sec][CFG_PORT])
        except ValueError:
            print('Port {} is not a valid port number at {}.{}'.format(
                co[sec][CFG_PORT], sec, CFG_PORT))
    for sec in (s, t):
        u = process_optional_key(co, sec, CFG_USER)
        p = process_optional_key(co, sec, CFG_PWD)
        if u is not None and p is None:
            print ('If {} specified, {} must be specified in section '.format(
                CFG_USER, CFG_PWD) + '{} from file {}'.format(sec, cfgfile))
            sys.exit(1)
    return co[s], co[t]


def process_workspaces(db):
    ws_id = 'ws'
    user = 'user'
    all_users = '*'
    acl_id = 'id'
    ws_cursor = db[COL_WS].find({}, [ws_id, WS_OBJ_CNT, OWNER, DELETED])
    pub_read = db[COL_ACLS].find({user: all_users}, [acl_id])
    workspaces = defaultdict(dict)
    for ws in ws_cursor:
        workspaces[ws[ws_id]][PUBLIC] = False
        workspaces[ws[ws_id]][WS_OBJ_CNT] = ws[WS_OBJ_CNT]
        workspaces[ws[ws_id]][OWNER] = ws[OWNER]
        workspaces[ws[ws_id]][DELETED] = ws[DELETED]
    for pr in pub_read:
        workspaces[pr[acl_id]][PUBLIC] = True
    return workspaces


def process_object_versions(db, userdata, objects, workspaces):
    # note all objects are from the same workspace
    obj_id = 'id'
    ws_id = 'ws'
    size = 'size'
    odel = {}
    ws = objects[0][ws_id]  # all objects in same ws
    wsowner = workspaces[ws][OWNER]
    wspub = workspaces[ws][PUBLIC]
    vers = 0
    for objs in chunkiter(objects, OR_QUERY_SIZE):
        ids = []
        for o in objs:
            ids.append(o[obj_id])
            odel[o[obj_id]] = o[DELETED]
        res = db[COL_VERS].find({ws_id: ws, obj_id: {'$in': ids}},
                                [ws_id, obj_id, size])
        for v in res:
            vers += 1
            deleted = odel[v[obj_id]]
            userdata[wsowner][wspub][deleted][OBJ_CNT] += 1
            userdata[wsowner][wspub][deleted][BYTES] += v[size]
    return vers


def process_objects(db, workspaces):
    ws_id = 'ws'
    obj_id = 'id'
    # user -> pub -> del -> du or objs -> #
    d = defaultdict(lambda: defaultdict(lambda: defaultdict(
        lambda: defaultdict(int))))
    wscount = 0
    for ws in workspaces:
        if MAX_WS > 0 and wscount > MAX_WS:
            break
        wsobjcount = workspaces[ws][WS_OBJ_CNT]
        print('\nProcessing workspace {}, {} objects'.format(ws, wsobjcount))
        for lim in xrange(LIMIT, wsobjcount + LIMIT, LIMIT):
            print('\tProcessing objects {} - {}'.format(
                lim - LIMIT + 1, wsobjcount if lim > wsobjcount else lim))
            sys.stdout.flush()
            objtime = time.time()
            query = {ws_id: ws, obj_id: {'$gt': lim - LIMIT, '$lte': lim}}
            objs = db[COL_OBJ].find(query, [ws_id, obj_id, DELETED])
            print('\ttotal obj query time: ' + str(time.time() - objtime))
            ttlstart = time.time()
            vers = process_object_versions(db, d, objs, workspaces)
#             size, objsproc = process_objects(
#                 objs, unique_users, types, workspaces)

#             total_size += size
            print('\ttotal ver query time: ' + str(time.time() - ttlstart))
            print('\ttotal object versions: ' + str(vers))
#             print('\tobjects processed: ' + str(objsproc))
#             objcount += objsproc
#             print('total objects processed: ' + str(objcount))
            sys.stdout.flush()
        wscount += 1
    return d


def main():
    sourcecfg, targetcfg = get_config()
    starttime = time.time()
    srcmongo = MongoClient(sourcecfg[CFG_HOST], sourcecfg[CFG_PORT],
                           slaveOk=True)
    srcdb = srcmongo[sourcecfg[CFG_DB]]
    if sourcecfg[CFG_USER]:
        srcdb.authenticate(sourcecfg[CFG_USER], sourcecfg[CFG_PWD])
    ws = process_workspaces(srcdb)

    objdata = process_objects(srcdb, ws)
    print(objdata)
    print('name', 'pub', 'del', 'type', '#')
    for n in objdata:
        for pub in sorted(objdata[n], reverse=True):
            for deleted in sorted(objdata[n][pub], reverse=True):
                for t in sorted(objdata[n][pub][deleted]):
                    print(n, pub, deleted, t, objdata[n][pub][deleted][t])
    # print time, object data

if __name__ == '__main__':
    main()

def todostuff():

    starttime = 0
    pubws = 0
    privws = 0
    unique_users = 0
    total_size = 0
    types = 0

    print('\nElapsed time: ' + str(time.time() - starttime))

    print('\nResults:')
    print('Total public workspaces ' + str(pubws))
    print('Total private workspaces ' + str(privws))
    print('Total users who have saved or copied an object: ' +
          str(len(unique_users)))
    print('Total size of stored data (double counts copies and identical ' +
          'data saved > 1 times): ' + str(total_size))

    print('\n' + '\t'.join(['Type', 'Version', 'Public', 'Private', 'TTL']))
    pub_tot = 0
    priv_tot = 0
    for t in types:
        pub_type_tot = 0
        priv_type_tot = 0
        for v in sorted(types[t]):
            print('\t'.join([t, v, str(types[t][v][PUBLIC]),
                             str(types[t][v][PRIVATE]),
                             str(types[t][v][PUBLIC] + types[t][v][PRIVATE])]))
            pub_type_tot += types[t][v][PUBLIC]
            priv_type_tot += types[t][v][PRIVATE]
        print('\t'.join([t, 'TTL', str(pub_type_tot), str(priv_type_tot),
                         str(pub_type_tot + priv_type_tot)]))
        pub_tot += pub_type_tot
        priv_tot += priv_type_tot
    print('\t'.join(['TTL', '-', str(pub_tot), str(priv_tot)]))