from monday_wrapper import MondayWrapper

def monday_tests():
    mon = MondayWrapper(board_name="Testing Board For Api")
    mon.new_board()
    get_item_results = mon.get_specific_item_by_name(item_name="Set up project")
    print(f"LOG INFO: RESULTS: {get_item_results}")

    mon.change_value_of_column(item_name="Set up project", col_title="Link", new_value="https://github.com/",link_text="Github link")
    mon.change_value_of_column(item_name="Set up project", col_title="Status", new_value="Updated")
    mon.change_value_of_column(item_name="Set up project", col_title="Task Weight", new_value="80")
    
    users_list = mon.get_list_of_users()
    for user_object in users_list:
        user_info = {"User_id": user_object.id,
                     "Name": user_object.name,
                     "Email": user_object.email
                     }
        print(f"LOG INFO: USER DETAILS {user_info}")
    
    mon.change_value_of_column(item_name="Set up project", col_title="Notes", new_value="Do more testing")
