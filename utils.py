from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pymysql
import random
import time
import json

Status_Dict = {"Closed": 0, "Open": 1};
Log_Saving_file = "Log.txt";
DB_Refresh_Time = 10;

Table_Contents = {
    "Register": [
        ["Email", "VARCHAR(50)", "NOT NULL"],
        ["Password", "VARCHAR(50)", "NOT NULL"],
        ["Username", "VARCHAR(25)", "DEFAULT 'Anonymous'"],
        ["Code", "VARCHAR(10)", "NOT NULL"],
        ["TimeLimit", "DOUBLE", "NOT NULL"]
    ],
    "UserInfo": [
        ["Email", "VARCHAR(50)", "NOT NULL"],
        ["Password", "VARCHAR(50)", "NOT NULL"],
        ["Username", "VARCHAR(25)", "DEFAULT 'Anonymous'"]
    ],
    "EventBoard": [
        ["EventID", "BIGINT", "UNSIGNED PRIMARY KEY AUTO_INCREMENT"],
        ["Email", "VARCHAR(50)", "NOT NULL"],
        ["Category", "VARCHAR(50)", "NOT NULL"],
        ["Title", "VARCHAR(100)", "NOT NULL"],
        ["Contents", "VARCHAR(1000)", "NOT NULL"],
        ["Place", "VARCHAR(50)", "NOT NULL"],
        ["EventTime", "DOUBLE", "NOT NULL"],
        ["PostingTime", "DOUBLE", "NOT NULL"],
        ["Status", "TINYINT", "DEFAULT 1"], # Default: Open
        ["NumMember", "SMALLINT", "UNSIGNED NOT NULL"],
        ["CurMember", "SMALLINT", "UNSIGNED DEFAULT 1"] # Only Event Poster
    ],
    "Member": [
        ["EventID", "BIGINT", "UNSIGNED NOT NULL"],
        ["Email", "VARCHAR(50)", "NOT NULL"],
        ["Username", "VARCHAR(25)", "DEFAULT 'Anonymous'"]
    ],
    "Comment": [
        ["CommentID", "BIGINT", "UNSIGNED PRIMARY KEY AUTO_INCREMENT"],
        ["EventID", "BIGINT", "UNSIGNED NOT NULL"],
        ["Email", "VARCHAR(50)", "NOT NULL"],
        ["Username", "VARCHAR(25)", "NOT NULL"],
        ["Comment", "VARCHAR(500)", "NOT NULL"],
        ["Time", "DOUBLE", "NOT NULL"]
    ]
};

Argument_Dict = {
    # Internal Functions
    "AdminInput": [
        ["admin-pwd", str, None, None, None],
        ["argument", None, None, None, None]
    ],
    "Input":[
        ["function-name", str, None, None, None],
        ["user-info", None, None, None, None]
    ],
    "UserInfoCheck": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 1, 50]
    ],
    
    # Normal Functions Not Requiring UserInfo pre-check
    "Login": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 1, 50]
    ],
    "Register": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password1", str, "Password1", 1, 50],
        ["password2", str, "Password2", 8, 50]
    ],
    "RegisterVerify": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 8, 50],
        ["code", str, "Code", 3, 9]
    ],
    
    # Normal Functions
    "GetCategories": [  
    ],
    "GetBoardList": [
        ["search-word", str, "Search Word", 0, 100],
        ["category", str, "Category", 1, 50],
        ["place", str, "Place", 1, 50],
        ["period-start", float, "Period Start", None, None],
        ["period-end", float, "Period End", None, None],
        ["event-start", int, "Querying Event Start", 0, None],
        ["num-event", int, "Number of Events to Query", 1, None]
    ],
    "GetEventInfo": [
        ["event-id", int, "Event ID", 0, None]
    ],
    "GetComments": [
        ["event-id", int, "Event ID", 0, None],
        ["comment-start", int, "Querying Comments Start", 0, None],
        ["num-comment", int, "Number of Comments to Query", 1, None]
    ],
    "CheckPoster": [
        ["event-id", int, "Event ID", 0, None],
        ["email", str, "Email", len("a@kaist.ac.kr"), 50]
    ],
    "PostEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["category", str, "Category", 1, 50],
        ["title", str, "Title", 1, 100],
        ["content", str, "Content", 0, 1000],
        ["place", str, "Place", 1, 50],
        ["event-time", float, "Event Time", None, None],
        ["num-member", int, "Number of Members to Collect", 2, 60000]
    ],
    "UpdateEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None],
        ["to-change", str, "Component to Change", 1, 20],
        ["turn-into", None, None, None, None] # the type depends on "to-change"
    ],
    "JoinEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None]
    ],
    "LeaveEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None]
    ],
    "CloseEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None]
    ],
    "ReopenEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None]
    ],
    "DisableEvent": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None]
    ],
    "AddComment": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None],
        ["comment", str, "Comment", 1, 500]
    ],
    "DeleteComment": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["event-id", int, "Event ID", 0, None],
        ["comment-id", int, "Comment ID", 0, None]
    ],
    "UpdateUserInfo": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 8, 50],
        ["type-password", str, "Typed Password", 1, 50]
    ],
    
    # Administration Functions
    "GetTableEntries": [
        ["table", str, "Table", 1, 100]
    ],
    "GetTables": [
    ],
    "GetTableColumn": [
        ["table", str, "Table", 1, 100]
    ],
    "AddUserInfo": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 8, 50]
    ],
    "DeleteUserInfo": [
        ["email", str, "Email", len("a@kaist.ac.kr"), 50],
        ["password", str, "Password", 8, 50]
    ],
    "InitTable": [
        ["table", str, "Table", 1, 100]
    ]
}

UdtEvt_Contents = {
    "category": [str, "Category", 1, 50],
    "title": [str, "Title", 1, 100],
    "content": [str, "Content", 0, 1000],
    "place": [str, "Place", 1, 50],
    "event-time": [float, "EventTime"],
    "num-member": [int, "NumMember", 2, 30000]
};
TWeek_to_Sec = 14 * 24 * 3600;

def connect_db():
    global db, Last_DB_Connection;
    db = pymysql.connect(host = 'localhost',
                         port = 3306,
                         user = 'Apper',
                         passwd = 'TeamApper1!',
                         db = 'apper',
                         charset = 'utf8'
                        );
    Last_DB_Connection = time.time();

def init():
    connect_db();
    random.seed(int(1e8 * time.time() % 1e8));
    
    tables = [i[0] for i in result("SHOW TABLES")];
    for table_name in Table_Contents:
        if table_name not in tables:
            create_table(table_name, Table_Contents[table_name]);

def commit(sql, val = None):
    if time.time() - Last_DB_Connection > DB_Refresh_Time: connect_db();
    cursor = db.cursor();
    if val is None: cursor.execute(sql);
    else: cursor.execute(sql, val);
    cursor.close();
    db.commit();

def result(sql, val = None):
    if time.time() - Last_DB_Connection > DB_Refresh_Time: connect_db();
    cursor = db.cursor();
    if val is None: cursor.execute(sql);
    else: cursor.execute(sql, val);
    res = cursor.fetchall();
    cursor.close();
    return res;

def create_table(table_name, table_contents):
    sql = "CREATE TABLE " + table_name + "(" + ",".join([" ".join(i) for i in table_contents]) + ")";
    commit(sql);

def chk_len(arg, min = 1, max = 50):
    return min <= len(arg) and len(arg) <= max;

def save_result(args):
    with open(Log_Saving_file, 'a') as f:
        f.write("output: {}\n\n".format(json.dumps(args, indent = 4)));

def error_msg(msg):
    output = {"exit_code": 0, "error_msg": msg[11: -2] if msg[:9] == "Exception" else msg};
    save_result(output);
    return jsonify(output);

def success(data = None):
    output = {"exit_code": 1} if data is None else {"exit_code": 1, "data": data};
    save_result(output);
    return jsonify(output);

def chk_register(args, func_name):
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s AND BINARY Password = %s", (args["email"], args["password"]))) == 0:
        raise Exception("{}-UserInfo: NOT Existing User Information ({})".format(func_name, args["email"]));

def chk_args(args, func_name):
    for arg in Argument_Dict[func_name]:
        if arg[0] not in args: raise Exception("{}: Invalid Arguments".format(func_name));
        if arg[1] is None: continue;
        if type(args[arg[0]]) is not arg[1] and not (type(args[arg[0]]) is int and arg[1] is float):
            raise Exception("{}: Type of {} should be {} (Input: {})".format(
                            func_name, arg[2], arg[1].__name__.upper(), type(args[arg[0]]).__name__.upper()));
        # type is one of str, float, int
        if arg[1] is str:
            if (arg[3] is not None and len(args[arg[0]]) < arg[3]) or (arg[4] is not None and len(args[arg[0]]) > arg[4]):
                raise Exception("{}: Invalid {} (Length should be in range [{}, {}])".format(func_name, arg[2], arg[3], arg[4]));
            if arg[0] == "email" and args[arg[0]][-len("@kaist.ac.kr"):] != "@kaist.ac.kr":
                raise Exception("{}: NOT KAIST Email ({})".format(func_name, args[arg[0]]));
        elif arg[1] is float: pass;
        elif arg[1] is int:
            if (arg[3] is not None and args[arg[0]] < arg[3]) or (arg[4] is not None and args[arg[0]] > arg[4]):
                raise Exception("{}: Invalid {} (Number should be in [{}, {}])".format(func_name, arg[2], arg[3], arg[4]));

def login(args):
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s", args["email"])) != 0:
        if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s AND BINARY Password = %s", (args["email"], args["password"]))) != 0:
            return success();
        else: raise Exception("Login: Password NOT Matched");
    else: raise Exception("Login: Ask to Register");

def register(args):
    if args["password1"] != args["password2"]: raise Exception("Register: NOT Identical Passwords");
    username = args["username"] if "username" in args else "Anonymous";
    if not chk_len(username, 1, 25): raise Exception("Register: Invalid Username (Length should be in [1, 25])");

    commit("DELETE FROM Register WHERE TimeLimit < %s", time.time());
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s", args["email"])) != 0:
        raise Exception("Register: Already Registered Email ({})".format(args["email"]));
    if "username" in args and len(result("SELECT Email FROM UserInfo WHERE BINARY Username = %s", args["username"])) != 0:
        raise Exception("Register: Already Existing Username ({})".format(args["username"]));
    
    commit("DELETE FROM Register WHERE BINARY Email = %s", args['email']);
    code = "{:06d}".format(random.randrange(1000000));
    try:
        msg = MIMEMultipart();
        msg["Subject"] = "KAIshare  Verification  Code";
        msg["To"] = args["email"];
        msg["From"] = "teamapperse@gmail.com";
        msg.attach(MIMEText(
            "Dear KAIshare Customer,\n" \
            "Your instant authentification code is below for KAIshare services.\n" \
            "  Verification Code: {}\n" \
            "Please, fill out your authentification code on the application.\n  \n" \
            "Best Regards,\n  \n" \
            "KAIshare Administrator Team Apper".format(code)
        ));
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465);
        smtp.login("teamapperse@gmail.com", "jpxwhlylmzcqwbyt");
        smtp.send_message(msg);
        smtp.quit();
    except Exception as e:
        raise Exception("Register: Failed to send an Email ({})\n Error Message: {}".format(args["email"], e));
    
    commit("INSERT INTO Register(Email, Password, Username, Code, TimeLimit) VALUES (%s, %s, %s, %s, %s)",
           (args["email"], args["password2"], username, code, time.time() + 180));
    return success();

def register_verify(args):
    username = args["username"] if "username" in args else "Anonymous";
    if not chk_len(username, 1, 25): raise Exception("RegisterVerify: Invalid Username ({})".format(username));

    commit("DELETE FROM Register WHERE TimeLimit < %s", time.time());
    if len(result("SELECT Email FROM Register WHERE BINARY Email = %s AND BINARY Password = %s AND BINARY Username = %s",
                  (args["email"], args["password"], username))) != 0:
        if len(result("SELECT Email FROM Register WHERE BINARY Email = %s AND BINARY Password = %s AND BINARY Username = %s AND Code = %s",
               (args["email"], args["password"], username, args["code"]))) != 0:
            commit("DELETE FROM Register WHERE BINARY Email = %s AND BINARY Password = %s", (args["email"], args["password"]));
            commit("INSERT INTO UserInfo(Email, Password, Username) VALUES (%s, %s, %s)", (args["email"], args["password"], username));
            return success();
        else:
            commit("UPDATE Register SET TimeLimit = %s WHERE BINARY Email = %s AND BINARY Password = %s",
                   (result("SELECT TimeLimit FROM Register WHERE BINARY Email = %s AND BINARY Password = %s",
                           (args["email"], args["password"]))[0][0] - 2.0, args["email"], args["password"]));
            raise Exception("RegisterVerify: Wrong Code ({})".format(args["code"]));
    else: raise Exception("RegisterVerify: Timeout");

def get_categories(args):
    return success([i[0] for i in result("SELECT DISTINCT Category FROM EventBoard")]);

def get_board_list(args):
    sql = "SELECT EventID, Email, Category, Title, Contents, Place, EventTime, NumMember, CurMember FROM EventBoard WHERE Status = 1 AND ";
    if len(args["search-word"]) != 0: sql += "(REPLACE(Title, ' ', '') LIKE '%{}%' OR REPLACE(Contents, ' ', '') LIKE '%{}%') AND ".format(
                                              args["search-word"].replace(" ", ""), args["search-word"].replace(" ", ""));
    if args["category"] != "##ALL##": sql += "BINARY Category = '{}' AND ".format(args["category"]);
    if args["place"] != "##ALL##": sql += "BINARY Place = '{}' AND ".format(args["place"]);
    if args["period-start"] != 0: sql += "EventTime >= {} AND ".format(args["period-start"]);
    if args["period-end"] != 0: sql += "EventTime <= {} AND ".format(args["period-end"]);
    sql = sql[:-4] + "ORDER BY EventTime DESC LIMIT {}, {}".format(args["event-start"], args["num-event"]);
    return success([list(i) for i in result(sql)]);
    
def get_event_info(args):
    event_info = result("SELECT Email, Category, Title, Contents, Place, EventTime, PostingTime, Status, NumMember, CurMember "
                        "FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(event_info) == 0: raise Exception("GetEventInfo: NOT Existing Event ID ({})".format(args["event-id"]));
    
    keys = ["email", "category", "title", "content", "place", "event_time", "posting_time", "status", "num_member", "cur_member"];
    data = {key: val for key, val in zip(keys, event_info[0])};
    username = result("SELECT Username FROM UserInfo WHERE BINARY Email = %s", data["email"]);
    if len(username) == 0: raise Exception("GetEventInfo: NOT Existing Poster Email ({})  BackEnd Problem".format(data["email"]));
    data["username"] = username[0][0];
    data["members"] = [list(i) for i in result("SELECT Email, Username FROM Member WHERE EventID = %s", args["event-id"])];
    return success(data);

def get_comments(args):
    if len(result("SELECT EventID FROM EventBoard WHERE EventID = %s", args["event-id"])) == 0:
        raise Exception("GetComments: Wrong Event ID ({})".format(args["event-id"]));
    
    return success([list(i) for i in result("SELECT CommentID, Email, Username, Comment, Time FROM Comment "
        "WHERE EventID = %s ORDER BY Time DESC LIMIT %s, %s", (args["event-id"], args["comment-start"], args["num-comment"]))]);

def check_poster(args):
    email = result("SELECT Email FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(email) == 0: raise Exception("CheckPoster: Wrong Event ID ({})".format(args["event-id"]));
    
    return success("T" if email[0][0] == args["email"] else "F");

def post_event(args):
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s", args["email"])) == 0:
        raise Exception("PostEvent: Who Are You? ({})".format(args["email"]));
    if args["event-time"] < time.time() or time.time() + TWeek_to_Sec < args["event-time"]:
        raise Exception("PostEvent: Event Time should be within 2 Weeks");
    
    post_time = time.time();
    commit("INSERT INTO EventBoard(Email, Category, Title, Contents, Place, EventTime, PostingTime, NumMember) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
           (args["email"], args["category"], args["title"], args["content"], args["place"], args["event-time"], post_time, args["num-member"]));
    commit("INSERT INTO Member(EventID, Email, Username) VALUES (%s, %s, %s)",
           (result("SELECT EventID FROM EventBoard WHERE PostingTime = %s", post_time)[0][0], args["email"], 
            result("SELECT Username FROM UserInfo WHERE BINARY Email = %s", args["email"])[0][0]));
    return success();

def update_event(args):
    emlstscmb = result("SELECT Email, Status, CurMember FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(emlstscmb) == 0: raise Exception("UpdateEvent: Wrong Event ID ({})".format(args["event-id"]));
    if emlstscmb[0][0] != args["email"]: raise Exception("UpdateEvent: Permission Denied (You are NOT the Event Poster)");
    if emlstscmb[0][1] == Status_Dict["Closed"]: raise Exception("UpdateEvent: Event Already Closed");
    
    if args["to-change"] not in UdtEvt_Contents: raise Exception("UpdateEvent: Wrong Argument ({})".format(args["to-change"]));
    if type(args["turn-into"]) is not UdtEvt_Contents[args["to-change"]][0]: raise Exception("UpdateEvent: Turn-Into Type {} Should be {}".format(
        type(args["turn-into"]).__name__, UdtEvt_Contents[args["to-change"]][0].__name__));
    if type(args["turn-into"]) is str and not chk_len(args["turn-into"], UdtEvt_Contents[args["to-change"]][2], UdtEvt_Contents[args["to-change"]][3]):
        raise Exception("UpdateEvent: Invalid {} (Length should be in [{}, {}])".format(UdtEvt_Contents[args["to-change"]][1: 4]));
    if args["to-change"] == "event-time" and (args["turn-into"] < time.time() or time.time + TWeek_to_Sec < args["turn-into"]):
        raise Exception("UpdateEvent: Event Time should be within 2 Weeks");
    if args["to-change"] == "num-member":
        if args["turn-into"] < 2 or args["turn-into"] > 30000: raise Exception("UpdateEvent: Number of Member Should be in [2, 30000]");
        if args["turn-into"] < emlstscmb[0][2]:
            raise Exception("UpdateEvent: Number of Members so far({}) is MORE than {}".format(emlstscmb[0][2], args["turn-into"]));
    
    commit("UPDATE EventBoard SET " + UdtEvt_Contents[args["to-change"]][1] + " = %s WHERE EventID = %s", (args["turn-into"], args["event-id"]));
    return success();

def join_event(args):
    stanum = result("SELECT Status, NumMember, CurMember FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(stanum) == 0: raise Exception("JoinEvent: Wrong Event ID ({})".format(args["event-id"]));
    if stanum[0][0] == 0: raise Exception("JoinEvent: Event is Closed");
    if stanum[0][1] <= stanum[0][2]: raise Exception("JoinEvent: Members are Full");
    
    if len(result("SELECT Email FROM Member WHERE EventID = %s AND BINARY Email = %s", (args["event-id"], args["email"]))) != 0:
        raise Exception("JoinEvent: Already Joining the Event");
    
    commit("INSERT INTO Member (EventID, Email, Username) VALUES (%s, %s, %s)",
           (args["event-id"], args["email"], result("SELECT Username FROM UserInfo WHERE BINARY Email = %s", args["email"])[0][0]));
    commit("UPDATE EventBoard SET CurMember = %s WHERE EventID = %s", (stanum[0][2] + 1, args["event-id"]));
    return success();

def leave_event(args):
    stanum = result("SELECT Email, Status, CurMember FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(stanum) == 0: raise Exception("LeaveEvent: Wrong Event ID ({})".format(args["event-id"]));
    if stanum[0][0] == args["email"]: raise Exception("LeaveEvent: Permission Denied (You are the Event Poster)");
    if stanum[0][1] == Status_Dict["Closed"]: raise Exception("LeaveEvent: Event is Closed");
    
    if len(result("SELECT Email FROM Member WHERE EventID = %s AND BINARY Email = %s", (args["event-id"], args["email"]))) == 0:
        raise Exception("LeaveEvent: Already NOT Joining the Event");
    
    commit("DELETE FROM Member WHERE EventID = %s AND BINARY Email = %s", (args["event-id"], args["email"]));
    commit("UPDATE EventBoard SET CurMember = %s WHERE EventID = %s", (stanum[0][2] - 1, args["event-id"]));
    return success();

def close_event(args):
    email_status = result("SELECT Email, Status FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(email_status) == 0: raise Exception("CloseEvent: Wrong Event ID ({})".format(args["event-id"]));
    if email_status[0][0] != args["email"]: raise Exception("CloseEvent: Permission Denied (NOT Event Poster)");
    if email_status[0][1] == 0: raise Exception("CloseEvent: Already Closed");
    
    commit("UPDATE EventBoard SET Status = 0 WHERE EventID = %s", args["event-id"]);
    return success();

def reopen_event(args):
    email_status = result("SELECT Email, Status FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(email_status) == 0: raise Exception("ReopenEvent: Wrong Event ID ({})".format(args["event-id"]));
    if email_status[0][0] != args["email"]: raise Exception("ReopenEvent: Permission Denied (NOT Event Poster)");
    if email_status[0][1] == 1: raise Exception("ReopenEvent: Already Opened");
    
    commit("UPDATE EventBoard SET Status = 1 WHERE EventID = %s", args["event-id"]);
    return success();

def disable_event(args):
    poster_email = result("SELECT Email FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(poster_email) == 0: raise Exception("DisableEvent: Wrong Event ID ({})".format(args["event-id"]));
    if poster_email[0][0] != args["email"]: raise Exception("DisableEvent: Permission Denied (NOT Event Poster)");
    
    commit("DELETE FROM Member WHERE EventID = %s", args["event-id"]);
    commit("DELETE FROM Comment WHERE EventID = %s", args["event-id"]);
    commit("DELETE FROM EventBoard WHERE EventID = %s", args["event-id"]);
    return success();

def add_comment(args):
    status = result("SELECT Status FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(status) == 0: raise Exception("AddComment: Wrong Event ID ({})".format(args["event-id"]));
    if status[0][0] == 0: raise Exception("AddComment: Event is Closed");
    
    commit("INSERT INTO Comment (EventID, Email, Username, Comment, Time) VALUES (%s, %s, %s, %s, %s)",
           (args["event-id"], args["email"], result("SELECT Username FROM UserInfo WHERE BINARY Email = %s", args["email"])[0][0],
            args["comment"], time.time()));
    return success();

def delete_comment(args):
    status = result("SELECT Status FROM EventBoard WHERE EventID = %s", args["event-id"]);
    if len(status) == 0: raise Exception("DeleteComment: Wrong Event ID ({})".format(args["event-id"]));
    if status[0][0] == 0: raise Exception("DeleteComment: Event is Closed");
    
    email = result("SELECT Email FROM Comment WHERE CommentID = %s", args["comment-id"]);
    if len(email) == 0: raise Exception("DeleteComment: NOT Existing Comment");
    if email[0][0] != args["email"]: raise Exception("DeleteComment: Permission Denied (NOT Commenter)");
    
    commit("DELETE FROM Comment WHERE CommentID = %s", args["comment-id"]);
    return success();

def update_userinfo(args):
    pwd_usn = result("SELECT Password, Username FROM UserInfo WHERE BINARY Email = %s", args["email"]);
    if len(pwd_usn) == 0: raise Exception("UpdateUserInfo: Who Are You? ({})".format(args["email"]));
    
    password, username = pwd_usn[0];
    if args["type-password"] != password: raise Exception("UpdateUserInfo: Wrong Password");
    
    if "username" not in args:
        if password == args["password"]: raise Exception("UpdateUserInfo: Nothing to Update");
        commit("UPDATE UserInfo SET Password = %s WHERE BINARY Email = %s", (args["password"], args["email"]));
    else:
        if password == args["password"] and username == args["username"]: raise Exception("UpdateUserInfo: Nothing to Update");
        elif password == args["password"]:
            if not chk_len(args["username"], 1, 25):
                raise Exception("UpdateUserInfo: Invalid Username (Length should be in [1, 25])");
            if len(result("SELECT Email FROM UserInfo WHERE BINARY Username = %s", args["username"])) != 0:
                raise Exception("UpdateUserInfo: Already Existing User Name ({})".format(args["username"]));
            commit("UPDATE UserInfo SET Username = %s WHERE BINARY Email = %s", (args["username"], args["email"]));
        elif username == args["username"]:
            commit("UPDATE UserInfo SET Password = %s WHERE BINARY Email = %s", (args["password"], args["email"]));
        else: raise Exception("UpdateUserInfo: Cannot Update Password and Username at Once");
    return success();


###################### Administration Functions ######################

def chk_admin_pwd(pwd):
    with open("ADMIN_PASSWORD", "r") as f: org_pwd = f.read();
    if org_pwd != pwd: raise Exception("Invalid Administration Password");

def get_table_entries(args):
    if args["table"] not in [i[0] for i in result("SHOW TABLES")]: raise("GetTable: NOT Existing Table ({})".format(args["table"]));
    return success([list(i) for i in result("SELECT * FROM " + args["table"])]);

def get_tables(args = None):
    return success([i[0] for i in result("SHOW TABLES")]);

def get_table_column(args):
    if args["table"] not in [i[0] for i in result("SHOW TABLES")]: raise("GetTableColumn: NOT Existing Table ({})".format(args["table"]));
    return success([list(i) for i in result("SHOW FULL COLUMNS FROM " + args["table"])]);

def add_userinfo(args):
    username = args["username"] if "username" in args else "Anonymous";
    if not chk_len(username, 1, 25): raise Exception("AddUserInfo: Invalid Username ({})".format(username));
    
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s", args["email"])) != 0:
        raise Exception("AddUserInfo: Already Exsiting Email ({})".format(args["email"]));
    if "username" in args and len(result("SELECT Email FROM UserInfo WHERE BINARY Username = %s", args["username"])) != 0:
        raise Exception("AddUserInfo: Already Exsiting Username ({})".format(args["username"]));

    username = args["username"] if "username" in args else "Anonymous";
    commit("INSERT INTO UserInfo (Email, Password, Username) VALUES (%s, %s, %s)", (args["email"], args["password"], username));
    return success();

def delete_userinfo(args):
    if len(result("SELECT Email FROM UserInfo WHERE BINARY Email = %s AND BINARY Password = %s", (args["email"], args["password"]))) == 0:
        raise Exception("DeleteUserInfo: NOT Exsiting User Information");
    commit("DELETE FROM UserInfo WHERE BINARY Email = %s AND BINARY Password = %s", (args["email"], args["password"]));
    return success();

def init_table(args):
    if args["table"] not in [i[0] for i in result("SHOW TABLES")]: raise Exception("InitTable: NOT Existing Table ({})".format(args["table"]));
    
    commit("TRUNCATE " + args["table"]);
    return success();
