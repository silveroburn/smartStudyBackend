import pymysql as con
import flask
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit

app = flask.Flask(__name__)
load_dotenv()

app.config['SECRET_KEY'] = os.environ.get('keyval')

conn = con.connect(
    host = '34.131.195.96',
    user = 'root',
    password = 'test1',
    database = 'first',
    port = 3306
)
cursor = conn.cursor()

#______________________________________________________________________________________________________________________________________________________________________________

websocket = SocketIO(app, cors_allowed_origins="*")
user_sockets = {}

@websocket.on('connect')
def printConnection():
    print("Connection established with request id: ", flask.request.sid)

@websocket.on('getRegNo')
def handleConnection(data):
    regNo = data.get('regNo')
    user_sockets[regNo] = flask.request.sid
    
@websocket.on('disconnect')
def handleDisconnect():
    SID = flask.request.sid
    userToDelete = None
    for regNo, socketId in user_sockets.items():
        if (socketId == SID):
            userToDelete = regNo
            break
        
    if userToDelete:
        user_sockets.pop(userToDelete)

@websocket.on('chat')
def handleChats(data):
    date = data.get('date')
    time = data.get('time')
    body = data.get('body')
    fromUser = data.get('from')
    toUser = data.get('to')
    if toUser in user_sockets:
        toUserId = user_sockets[toUser]
        websocket.emit('getReaction', {'date' : date, 'time' : time, 'from' : fromUser, 'body' : body}, to=toUserId)
        emit('getSentStatus', {'status' : 'data sent successfully'})
    else:
        emit('getSentStatus', {'status' : 'user offline'})
    
#______________________________________________________________________________________________________________________________________________________________________________
            

@app.route('/signup', methods=['POST'])
def getSignUpData():
    print('signup')
    userData = flask.request.get_json()    
    name = userData.get('name')
    emailId = userData.get('emailId')
    password = userData.get('password')
    regNo = userData.get('regNo')
    print("this is regNo", regNo)
    print("this is regNo", name)
    print("this is regNo", emailId)
    print("this is regNo", password)
    
    cursor.execute('select * from user where regNo = %s limit 1', (regNo, ))
    data = cursor.fetchall()
    
    if (len(data) >= 1):
        return flask.jsonify({"message" : "User already exists"}), 409
    
    cursor.execute('insert into user values (%s, %s, %s, %s)', (regNo, name, emailId, password))
    conn.commit()
    
    return flask.jsonify({"message": "User created successfully"}), 201

@app.route('/signin', methods = ['POST'])
def signIn():
    userData = flask.request.get_json()
    print('signin')
    name = userData.get('name')
    password = userData.get('password')
    
    cursor.execute('select * from user where (regNo = %s or emailId = %s) and password = %s', (name, name, password))
    data = cursor.fetchone()
    if (data):
        cursor.execute('select regNo from user where regNo = %s or emailId = %s', (name, name))
        responseRegNo = cursor.fetchone()
        print("this is responseRegNo: ", responseRegNo[0])
        return flask.jsonify({"regNo" : responseRegNo[0]}), 202
    else:
        return flask.jsonify({"message" : "User does not exist"}), 404
    
@app.route('/additionalInfoStatus', methods=['POST'])
def getStatus():
    data = flask.request.get_json()
    print('checking status')
    regNo = data.get('regNo')
    
    cursor.execute('select * from userInfo where regNo = %s', (regNo,))
    rows = cursor.fetchone()
    
    if (rows):
        return flask.jsonify({"message" : "User data already filled"}), 409
    return flask.jsonify({"message" : "no data found, heading to additional info page"}), 200
    
@app.route('/additionalInfo', methods=['POST'])
def addAdditionalInfo():
    userAddInfo = flask.request.get_json()
    print('additional info')
    regNo = userAddInfo.get('regNo')
    year = userAddInfo.get('year')
    department = userAddInfo.get('department')
    skillset = userAddInfo.get('skillset')
    
    cursor.execute('insert into userInfo (regNo, year, department, skillset) values (%s, %s, %s, %s)', (regNo, year, department, skillset))
    conn.commit()
    
    return flask.jsonify({"message" : "user additional data added successfully"}), 201


@app.route('/getAboutMe', methods=['POST'])
def getAboutMe():
    aboutMeInfo = flask.request.get_json()
    regNo = aboutMeInfo.get('regNo')
    print('getting the about me info and the regNo is: ', regNo)
    
    cursor.execute('select * from user join userInfo on user.regNo = userInfo.regNo where user.regNo = %s', (regNo,))
    data = cursor.fetchone()
    if (data):
        print(data)
        return flask.jsonify(data), 200
    else:
        return flask.jsonify({"message" : "Details not found"}), 404
    
@app.route('/createProject', methods=['POST'])
def createProjectData():
    data = flask.request.get_json()
    print("Creating Project")
    leader = data.get('regNo')
    pName = data.get('pName')
    pDes = data.get('pDes')
    pMembers = data.get('pMembers')
    pMaxMembers = data.get('pMaxMembers')
    pTimeToComplete = data.get('pTimeToComplete')
    pTechStack = data.get('pTechStack')
    
    print("Checkpoint 1")
    cursor.execute('select * from project where leader = %s and projectName = %s', (leader, pName))
    print("Checkpoint 2")
    rows = cursor.fetchone()
    if (rows):
        return flask.jsonify({"message" : "project already exists"}), 409
    print("Checkpoint 3")
    
    for i in range(len(pMembers)):
        cursor.execute('select * from user where regNo = %s', pMembers[i])
        validRow = cursor.fetchone()
        if not validRow:
            return flask.jsonify({"message" : "One or more member not found in database"}), 404
    print("Checkpoint 4")

    cursor.execute('insert into project (projectName, leader) values (%s, %s)', (pName, leader))
    print("Checkpoint 5")
    
    cursor.execute('select id from project where leader = %s and projectName = %s', (leader, pName))
    rows = cursor.fetchone()
    print("Checkpoint 6")
    projectId = rows[0]
    
    print("Checkpoint 7")
    cursor.execute('insert into projectInfo (id, description, minTime, maxMembers, techStack) values (%s, %s, %s, %s, %s)', (projectId, pDes, pTimeToComplete, pMaxMembers, pTechStack))
    
    print("This is one of the members: ")
    for i in range(len(pMembers)):
        print("This is one of the members: ", pMembers[i])
        cursor.execute('insert into projectMembers (id, memberRegNo) values (%s, %s)', (projectId, pMembers[i]))
    conn.commit()
    
    return flask.jsonify({"message" : "project data added successfully"}), 201
    
@app.route('/getBrowse', methods=['POST'])
def getBrowseInfo():
    data = flask.request.get_json()
    print("getBrowse")
    regNo = data.get('regNo')
    
    cursor.execute('select project.id, project.projectName, project.leader, projectInfo.techStack, projectInfo.maxMembers from project left join projectInfo on project.id = projectInfo.id where project.leader != %s and project.id not in (select projectMembers.id from projectMembers where projectMembers.memberRegNo = %s)', (regNo, regNo))
    rows = cursor.fetchall()
    
    if not rows:
        return flask.jsonify({"message" : "no projects online right now"}), 404
    
    print("Data found: ", rows)
    return flask.jsonify({"data" : rows}), 200

@app.route('/exploreInfo', methods=['POST'])
def getExploreInfo():
    data = flask.request.get_json()
    print("ExploreInfo")
    
    projectId = data.get('projectId')
    
    cursor.execute('select projectName from project where id = %s', (projectId,))
    projectName = cursor.fetchone()
    print(projectName)
    
    cursor.execute('select * from projectInfo where id = %s', (projectId, ))
    rows = cursor.fetchone()
    print(rows)
    
    cursor.execute('select memberRegNo from projectMembers where id = %s', (projectId, ))
    members = cursor.fetchall()
    print(members)
    if not rows:
        return flask.jsonify({"message" : "No data found regarding the project id"}), 404
    
    if (rows):
        return flask.jsonify({"data" : rows, "members" : members, "projectName" : projectName}), 200
    

if __name__ == '__main__':
    websocket.run(app, host='0.0.0.0', port=5000)

