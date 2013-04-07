#!/usr/bin/env python
import time, datetime
import logging

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.web
import tornado.database
from tornado.options import define, options

import Settings
from Request import userData

define("port", default=8080, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="test", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="ygs", help="database password")
define("sync_time", default=60, help="sync from mem to db", type=int)

userDict = {}
timeDict = {}

mysqldb = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)

def ProcessRequest(params={}, callback=None):
    user = params['user']
    action = params['action']
    content = params['content']
    reqTime = float(params['time'])

    Key = user + '_' + action
    now = time.time()

    # get the user_action content's counts, if found, increment 
    # counts of content, otherwise add new userData into dict 
    # alert if over configure counts for frequent request
    try:
        userQueue = userDict[Key]
        users = [e for e in userQueue if e.content == content]
        if len(users) > 0:
            userObj = users[0]
            userObj.modify = True
            userObj.counts += 1

            # if over threshold, callback 
            if userObj.counts > Settings.max_identity_count:
                callback(user, action)
        else:
            userObj = userData(user, action, content, reqTime)
            userObj.New = True
            userQueue.append(userObj)
    except KeyError:
        userObj = userData(user, action, content, reqTime)
        userObj.New = True
        userDict[Key] = [userObj]

    # append timenode to user_action time queue, 
    # alert if over configure counts for identity request
    try:
        queue = timeDict[Key]
        queue.append(now)
        queue = removeTimeoutNode(queue) 
    except KeyError, e:
        timeDict[Key] = [now]

    queue = timeDict[Key]
    if len(queue) > Settings.max_request_count:
        callback(user, action)

# remove time node in user_action timeQueue
def removeTimeoutNode(queue):
    lastTimeSpec = datetime.timedelta(seconds=Settings.max_request_timeout)
    lastTime = time.time() - lastTimeSpec.total_seconds()
    length = len(queue)
    while length >= 0:
        first = queue[0]
        if first < lastTime:
            queue.pop(0)
        else:
            break

def FrequentLog(user, action):
    logging.warning('%s,您频繁%s' % (user, action))

def sync_dbFromMem():
    count = 0
    for (k,v) in userDict.items():

        # insert new users into db
        news = [user for user in v if user.New == True]
        for newUser in news:

            count += mysqldb.execute("INSERT INTO userRequest(user, action,\
                content, counts, updated) VALUES (%s, %s, %s, %s, %s);",\
                newUser.name, newUser.action, newUser.content, \
                newUser.counts, datetime.datetime.fromtimestamp(newUser.updated))
            newUser.New = False

        # update the modify data 
        updates = [user for user in v if user.modify == True]
        for update in updates:
            count += mysqldb.execute("update userRequest set counts=%s, updated=%s\
                where user=%s and action=%s and content=%s;", \
                update.counts, datetime.datetime.fromtimestamp(update.updated),\
                update.name, update.action, update.content)
            update.modify = False
    logging.info('change db data %d' % (count)) 

def load_Fromdb():
    users = mysqldb.query("SELECT * FROM userRequest;")
    for user in users:
        user.New = False
        user.modify = False
        Key = user.user + '_' + user.action
        loadUser = userData(user['user'], user['action'], \
                user['content'], time.mktime(user['updated'].timetuple()))
        loadUser.counts = user['counts']
        
        try:
            userList = userDict[Key]
            userList.append(loadUser)
        except KeyError:
            userDict[Key] = [loadUser]

        # update timeQueue
        lastTimeSpec = datetime.timedelta(seconds=Settings.max_request_timeout)
        lastTime = time.time() - lastTimeSpec.total_seconds()
        userTime = time.mktime(user['updated'].timetuple())
        if userTime < lastTime:
            try:
                timeQueue = timeDict[Key]
                timeQueue.append(userTime)
            except KeyError:
                timeDict[Key] = [userTime]
    if len(users) > 0:
        logging.info('load from db success: %d', len(users)) 

class MainPageHandler(tornado.web.RequestHandler):
    def prepare(self):
        pass

    def post(self):
        body = self.request.body
    	params = body.split('&')
        paramDict = {}
        for param in params:
            kv = param.split('=')
            paramDict[kv[0]] = kv[1] if len(kv) > 1 else ""

        IOLoop.instance().add_callback(lambda:ProcessRequest(paramDict, FrequentLog))


def  main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
            (r"/", MainPageHandler),
        ])

    http_server = HTTPServer(application)
    http_server.listen(options.port)
    load_Fromdb()
    PeriodicCallback(sync_dbFromMem, options.sync_time*1000).start()
    IOLoop.instance().start()


if __name__ == "__main__":
    main()
