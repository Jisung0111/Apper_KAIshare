from flask import Flask, request
import utils
import json
import time, datetime

Funcs = {
    "Login": utils.login,
    "Register": utils.register,
    "RegisterVerify": utils.register_verify,
    "GetCategories": utils.get_categories,
    "GetBoardList": utils.get_board_list,
    "GetEventInfo": utils.get_event_info,
    "GetComments": utils.get_comments,
    "CheckPoster": utils.check_poster,
    "PostEvent": utils.post_event,
    "UpdateEvent": utils.update_event,
    "JoinEvent": utils.join_event,
    "LeaveEvent": utils.leave_event,
    "CloseEvent": utils.close_event,
    "ReopenEvent": utils.reopen_event,
    "DisableEvent": utils.disable_event,
    "AddComment": utils.add_comment,
    "DeleteComment": utils.delete_comment,
    "UpdateUserInfo": utils.update_userinfo
}

Admin_Funcs = {
    "GetTableEntries": utils.get_table_entries,
    "GetTables": utils.get_tables,
    "GetTableColumn": utils.get_table_column,
    "AddUserInfo": utils.add_userinfo,
    "DeleteUserInfo": utils.delete_userinfo,
    "InitTable": utils.init_table
}

app = Flask(__name__);

@app.route('/resource', methods = ['GET', 'POST'])
def method():
    while True:
        with open("status", "r") as f: status = f.readline();
        if status != "rest": time.sleep(0.02);
        else:
            with open("status", "w") as f: f.write("work");
            break;
    
    try:
        if request.method == 'POST':
            args = request.get_json();
            if type(args) is not dict: args = json.loads(args);
            
            with open(utils.Log_Saving_file, 'a') as f:
                args_write = json.dumps(
                    {i: args[i] for i in args if i != "admin-pwd"},
                    indent = 4
                );
                f.write("{} ({})\ninput: {}\n".format(
                    request.remote_addr, datetime.datetime.utcnow(), args_write));
            
            # Management of Administration Functions 
            if "admin-func" in args:
                utils.chk_args(args, "AdminInput");
                utils.chk_admin_pwd(args["admin-pwd"]);
                if args["admin-func"] not in Admin_Funcs:
                    raise Exception("Wrong Function Name ({})".format(["admin-func"]));
                utils.chk_args(args["argument"], args["admin-func"]);
                return Admin_Funcs[args["admin-func"]](args["argument"]);
            
            # Management of Normal Functions
            utils.chk_args(args, "Input");
            if args["function-name"] not in Funcs:
                raise Exception("Wrong Function Name ({})".format(args["function-name"]));
        
            if args["function-name"] in ["Login", "Register", "RegisterVerify"]:
                utils.chk_args(args["user-info"], args["function-name"]);
                return Funcs[args["function-name"]](args["user-info"]);
            
            if "argument" not in args: raise Exception("Input: Invalid Arguments");
            utils.chk_args(args["user-info"], "UserInfoCheck");
            utils.chk_register(args["user-info"], args["function-name"]);
            utils.chk_args(args["argument"], args["function-name"]);
            return Funcs[args["function-name"]](args["argument"]);

        else: return "Hello, world!";

    except Exception as e:
        return utils.error_msg(repr(e));
        
    finally:
        with open("status", "w") as f: f.write("rest");

if __name__ == "__main__":
    utils.init();
    app.run(host = "0.0.0.0", port = 5000, debug = True);
