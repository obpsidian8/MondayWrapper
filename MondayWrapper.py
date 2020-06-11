import json
import time
from moncli import MondayClient, BoardKind, UserKind, ColumnType, create_column_value
from moncli.entities.objects import StatusSettings

USER_NAME = 'made_up_user@email.com'
API_V1 = 'apikeyapikeyapikeyv1apikeyv1apikeyv1apikeyv1'
API_V2 = 'apikeyv2apikeyv2apikeyv2apikeyv2apikeyv2'
# THIS MAY BE MODIFIED TO USE ENVIRONMENT VARIABLE FOR USERNAME AND API KEYS

CLIENT = MondayClient(user_name=USER_NAME, api_key_v1=API_V1, api_key_v2=API_V2)

class MondayWrapper:
    """
    Wrapper class for moncli module for operations on our monday.com tasks.
    Requires a board name which will be the base/main board we are working with.
    """

    def __init__(self, board_name):
        self.board_name = board_name
        self.existing_boards_list = []
        self.all_items_list = []
        self.all_users_list = []

        self.board_objects_cache = {}
        self.item_objects_cache = {}
        self.column_objects_cache = {}

    def new_board(self, board_name=None):
        """
        Makes a new board with name passed into the method.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        If the board with the name exists , the id of the existing board is returned. If not, the board is created and the id is returned
        :param board_name: str
        :return: id of the board (existing or created): int
        """
        if not board_name:
            board_name = self.board_name

        board_exists = self.check_board_exists(board_name)

        if board_exists is False:
            board_object = CLIENT.create_board(board_name, board_kind=BoardKind.public)
            print(f"LOG INFO: New board created with id {board_object.id}")
            # ADD TO CACHE: BOARD OBJECT
            self.board_objects_cache[board_name] = board_object
            return board_object.id
        else:
            existing_board_id = self.get_board_id(board_name)
            print(f"LOG INFO: See above message. Not making board for '{board_name}'. Will return id of existing board with same name. Id: {existing_board_id}")
            return existing_board_id

    def get_board_id(self, board_name=None):
        """
        Get's the board id of the board name passed.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param board_name: str
        :return: id of the board specified: int
        """
        if not board_name:
            board_name = self.board_name

        retrieved_board = CLIENT.get_board_by_name(board_name)
        board_id = retrieved_board.id
        return board_id

    def add_column_to_board(self, column_title, board_name=None):
        """
        Add column to the board name passed. (Only implemented for columns of type long_text)
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param column_title: Title of column: str
        :param board_name: str
        :return: column id of the column added
        """
        if not board_name:
            board_name = self.board_name
        print(f"LOG INFO: Adding column {column_title} to board {board_name}")
        retrieved_board = CLIENT.get_board_by_name(board_name)
        retrieved_board.add_column(title=column_title, column_type=ColumnType.long_text)

        col_id = self.get_column_id_by_name(col_name=column_title, board_name=board_name)

        return col_id

    def add_new_item_to_board(self, item_name, board_name=None):
        """
        Adds a new item or task to a board.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: Name of the task/ item you want to add to the board.
        :param board_name: str
        :return: itemm id of the item just added to the board: int
        """
        if not board_name:
            board_name = self.board_name

        new_item_object = None
        item_exists = self.check_item_exists(item_name=item_name, board_name=board_name)
        if item_exists:
            print(f"LOG INFO: Item with name '{item_name}' already exists within board '{board_name}'. Getting item id for existing item")
        else:
            print(f"LOG INFO: Adding new item {item_name} to board {board_name}")
            retrieved_board = CLIENT.get_board_by_name(board_name)
            try:
                new_item_object = retrieved_board.add_item(item_name=item_name)
                print(f"LOG INFO: New item '{new_item_object.name}' added with item ID {new_item_object.id}")
            except Exception as e:
                print(f"LOG ERROR: Could not add new item. Max complexity issue. Error details {e}. Will pause and try again")
                complexityError = True
                counter = 1
                while complexityError and counter < 30:
                    print(f"\nTrying Mpnday.com API. Try #{counter} from (add_new_item_to_board - getting new_item_object)")
                    time.sleep(2)
                    try:
                        new_item_object = retrieved_board.add_item(item_name=item_name)
                        print(f"LOG INFO: New item '{new_item_object.name}' added with item ID {new_item_object.id}")
                        complexityError = False
                    except Exception as e:
                        print(f"LOG ERROR: Could not add new item. Max complexity issue. Error details {e}. Will pause and try again")
                        counter = counter + 1

            if new_item_object:
                # ADD TO CACHE: ITEM OBJECT
                print(f"LOG INFO: Adding item object for item \"{item_name}\" to cache for item objects.")
                self.item_objects_cache[new_item_object.name] = new_item_object
            else:
                print(f"LOG ERROR: Could not add new item {item_name} after multiple tries")
                return None

        item_id = self.get_item_id_by_name(item_name=item_name, board_name=board_name)
        return item_id

    def check_item_exists(self, item_name, board_name=None):
        """
        Checks if item exists.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: str
        :param board_name: str
        :return: Boolean
        """
        if not board_name:
            board_name = self.board_name

        item_objects_list = self._get_item_objects_list(item_name=item_name, board_name=board_name)
        for item_obj in item_objects_list:
            if item_obj.name == item_name:
                print(f"LOG INFO: Found existing item with name {item_name}")
                return True

        print(f"LOG ERROR: No existing item found with name {item_name}")
        return False

    def get_specific_item_by_name(self, item_name, board_name=None):
        """
        Gets a specific item object whose name is passed. If board is passed , it will check the board passed.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: str
        :param board_name: str
        :return: Item object: object
        """
        if not board_name:
            board_name = self.board_name

        item_objects_list = self._get_item_objects_list(item_name=item_name, board_name=board_name)

        for item_object in item_objects_list:
            # ADD TO CACHE: ITEM OBJECT
            print(f"LOG INFO: Adding item object for item '{item_name}' to cache for item objects.")
            self.item_objects_cache[item_object.name] = item_object
            if item_name == item_object.name:
                print(f"LOG INFO: Found item object with name '{item_name}' in in board '{board_name}'")
                return item_object

        print(f"LOG INFO: No item/task found with name '{item_name}' in '{board_name}' using cache or API query")
        return None

    def get_items_in_single_board(self, board_name=None):
        """
        Gets a list of all items in the board passed to the method.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param board_name: str
        :return: List of item objects: List
        """
        if not board_name:
            board_name = self.board_name

        board_items_list = []
        print(f"LOG INFO: Getting items for board {board_name}")
        retrieved_board = CLIENT.get_board_by_name(board_name)
        board_items = retrieved_board.get_items()
        for board_item in board_items:
            item_info = {"item_id": board_item.id,
                         "item_name": board_item.name
                         }
            # print(f"LOG INFO: ITEM DETAILS: {item_info}")
            board_items_list.append(board_item)
        # print(f"LOG INFO: List of items in board {board_name}:\n\t{board_items_list}")
        print(f"LOG INFO: {len(board_items_list)} found.")
        return board_items_list

    def check_board_exists(self, board_name=None):
        """
        Checks if board with board name passed exists.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param board_name: str
        :return: Boolean
        """
        if not board_name:
            board_name = self.board_name

        # CHECK IN CACHE FOR BOARD OBJECT
        print(f"LOG INFO: Checking in board object cache for board name '{board_name}'.")
        board = self.board_objects_cache.get(board_name)

        if board is None:
            try:
                board = CLIENT.get_board(name=board_name)
                print(f"LOG INFO: Board name {board.name} exists!")
                self.board_objects_cache[board_name] = board
                return True
            except Exception as e:
                print(f"LOG WARN: No board found with name: {board_name}. ERROR DETAILS: {e}")
                return False
        else:
            print(f"LOG INFO: Found board object for board in cache. Board name {board.name} exists!")
            return True

    def get_list_of_existing_boards(self):
        """
        Gets a list of board (objects) in all workspaces.
        :return: List of board objects: List
        """
        boards = CLIENT.get_boards()

        for board in boards:
            board_info = {
                "board_id": board.id,
                "board_name": board.name
            }
            # print(f"LOG INFO: {board_info} ")
            self.existing_boards_list.append(board)
        # print(f"LOG INFO: Existing boards list:\n\t{self.existing_boards_list}")
        return self.existing_boards_list

    def get_columns_in_single_board(self, board_name=None):
        """
        Gets a list of all columns in the board with the name passed.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param board_name:str
        :return: List of board column objects: List
        """
        if not board_name:
            board_name = self.board_name

        print(f"LOG INFO: Getting columns for board {board_name}")

        # CHECK IN CACHE FOR COLUMNS OBJECT LIST
        print(f"LOG INFO: Checking in column objects list for board name {board_name} in cache.")
        if board_name in self.column_objects_cache:
            print(f"LOG SUCCESS: Found column object list for board name '{board_name}' in column object list cache")
            return self.column_objects_cache.get(board_name)
        else:
            print(f"LOG WARN: No column object list was found for the board \"{board_name}\".")

        # IF COLUMNS LIST FOR BOARD NOT IN CACHE, RETRIEVE AND ADD TO CACHE
        retrieved_board = CLIENT.get_board_by_name(board_name)
        columns_list = retrieved_board.get_columns()
        # ADD TO CACHE: COLUMN OBJECT
        self.column_objects_cache[board_name] = columns_list

        for column in columns_list:
            # COLUMN ID IS NOT A NUMBER. IT IS A STRING.
            column_info = {"column_id": column.id,
                           "column_title": column.title,
                           "column type": column.type
                           }
            # print(f"LOG INFO: COLUMN DETAILS {column_info}")
        # print(f"LOG INFO: List of columns in board {board_name}:\n\t{board_colunms_list}")
        return columns_list

    def get_column_settings_string_for_board(self, board_name=None, col_title="Status"):
        """
        Returns the label settings for the board specified.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param board_name: str
        :return: label settings: str
        """

        if not board_name:
            board_name = self.board_name

        print(f"LOG INFO: Getting columns for board {board_name}")
        retrieved_board = CLIENT.get_board_by_name(board_name)
        columns = retrieved_board.get_columns()

        for column in columns:
            if column.title == col_title:
                label_setting_str = column.settings_str
                return label_setting_str

        return None

    def get_all_items_in_all_boards(self):
        """
        Gets a list of all items in all boards.
        :return: List of item objects: List
        """

        items = CLIENT.get_items(limit=50, newest_first=True)
        for item in items:
            item_info = {"item_id": item.id,
                         "item_name": item.name
                         }
            # print(f"LOG INFO: ITEM DETAILS {item_info}")
            self.all_items_list.append(item)
        # print(f"LOG INFO: List of all items from all boards:\n\t{self.all_items_list}")
        return self.all_items_list

    def get_list_of_users(self):
        """
        Gets a list of users for the workspace
        :return: List of user objects : List
        """
        users = CLIENT.get_users(kind=UserKind.all)
        for user in users:
            if user.is_guest:
                user_type = "Guest"
            else:
                user_type = "Team Member"
            user_info = {"User_id": user.id,
                         "Name": user.name,
                         "Email": user.email,
                         "User_type": user_type
                         }
            # print(f"LOG INFO: USER INFO DETAILS: {user_info}")
            self.all_users_list.append(user)
        return self.all_users_list

    def get_columns_for_item_from_board(self, item_name, board_name=None):
        """
        Gets a list of columns for an item. A board name can be passed to narrow down the search.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: str
        :param board_name: str
        :return: list of column objects if available or return empty list []: List
        """
        # SIMPLY GET THE COLUMNS FOR THE BOARD THE ITEM IS IN
        if not board_name:
            board_name = self.board_name

        # THIS IS TO CHECK THAT WE ARE LOOKING FOR COLUMNS OF THE RIGHT BOARD
        item_object = self.get_specific_item_by_name(item_name, board_name)
        if item_object:
            # MEANS ITEM WITH NAME WAS FOUND IN THE BOARD WITH GIVEN NAME
            columns_list = self.get_columns_in_single_board(board_name)
            print(f"LOG INFO: Found columns for item {item_name}, located in board {board_name}")
            return columns_list
        else:
            return []

    def get_value_of_column_for_item(self, item_name, col_title, board_name=None):
        """
        Get the value of a particular cell with the item name passed , column title passed and board name passed.
        If no board name is passed to this method, the name passed in the __init__ method is used.

        :param item_name: str
        :param col_title: str
        :param board_name: str
        :return: value of particular cell cast as a string: str
        """
        value_index = 2  # THE VALUE OF AN ITEM FROM A PARTICULAR COLUMN IS THE THIRD ITEM IN THE COLUMN OBJECT
        if not board_name:
            board_name = self.board_name

        # GET THE ITEM OBJECT FOR THE ITEM PARAMETERS SUPPLIED
        item_obj = self.get_specific_item_by_name(item_name=item_name, board_name=board_name)

        # GET COLUMN ID
        col_id = self.get_column_id_by_name(col_name=col_title, board_name=board_name)

        # GET THE COLUMN VALUE OBJECT FROM THE ITEM OBJECT
        print(f"LOG INFO: Getting column value object from item object (item name: \"{item_name}\")")
        try:
            col_val_object = item_obj.get_column_value(title=col_title)
        except Exception as e:
            print(f"LOG ERROR: Error getting column value object for item \"{item_name}\"  at column \"{col_title}\" using column name. ERROR DETAILS: {e}. Will use Id")
            col_val_object = item_obj.get_column_value(id=col_id)
            if col_val_object:
                print(f"LOG INFO: Column value object found for item \"{item_name}\" and column \"{col_title}\" using column id.")

        # THIRD KEY OF THE DICT FORM OF COL_VAL_OBJECT IS THE VALUE
        col_val_dict = col_val_object.__dict__
        print(f"LOG INFO: COLUMN INFORMATION : {col_val_dict}")
        keys = list(col_val_dict.keys())

        col_val_key = keys[value_index]
        value = col_val_dict[col_val_key]

        return value

    def get_item_id_by_name(self, item_name, board_name=None):
        """
        Gets the item id of the item whose name is passed. Item is searched within the board name passed
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: str
        :param board_name: str
        :return: item id : int
        """
        if not board_name:
            board_name = self.board_name

        item_objects_list = self._get_item_objects_list(item_name=item_name, board_name=board_name)

        for item_obj in item_objects_list:
            if item_obj.name == item_name:
                item_id = item_obj.id
                print(f"LOG INFO: RESULT: Id found for item {item_name}, in board {board_name}, Item Id: {item_id}")
                return item_id
        return None

    def _get_item_objects_list(self, item_name, board_name):
        """
        Returns a list of item moncli objects for the item name and board name supplied.
        This method is to be used only internally by the class.
        The item name and board name are required and are supplied by the methods that use this class.
        :param item_name: Item name: str
        :param board_name: Board name: str
        :return: List of item objects: List
        """
        item_objects_list = []

        # CHECK IN CACHE FOR BOARD OBJECT
        print(f"LOG INFO: Checking in board object cache for board object with name '{board_name}'.")
        board = self.board_objects_cache.get(board_name)
        if board is None:
            # IF NOT IN CACHE, QUERY MONDAY API FOR BOARD OBJECT
            try:
                board = CLIENT.get_board(name=board_name)
                self.board_objects_cache[board_name] = board
            except Exception as e:
                print(f"LOG ERROR: Board with name '{board_name}' not returned from API query. ERROR DETAILS: {e}. Will pause and try again")
                complexityError = True
                counter = 1
                while complexityError and counter < 30:
                    print(f"\nTrying Mpnday.com API. Try #{counter} from _get_item_objects_list - getting board object")
                    time.sleep(2)
                    try:
                        board = CLIENT.get_board(name=board_name)
                        self.board_objects_cache[board_name] = board
                        complexityError = False
                    except Exception as e:
                        print(f"LOG ERROR: Board object with name '{board_name}' not returned from API query. Item objects list cannot be queried . ERROR DETAILS: {e}")
                        counter = counter + 1

                if complexityError:
                    return item_objects_list

        else:
            print(f"LOG SUCCESS: Found board object in cache for board name {board_name}. Will use to check if item exists.")

        # GET ITEMS IN CURRENT BOARD FIRST WITH ATTRIBUTES MATCHING ITEM NAME SUPPLIED
        try:
            status_value = create_column_value(id='name', column_type=ColumnType.name, value=str(item_name))
            item_objects_list = board.get_items_by_column_values(column_value=status_value)
            print(f"LOG SUCCESS: Found item object list from API using item name {item_name}")
        except Exception as e:
            print(f"LOG ERROR: Error getting item objects list matching item name {item_name} from Monday API. ERROR DETAILS: {e}")
            print(f"LOG INFO: No item objects returned from the search for item objects for item name \"{item_name}\" due to API error. WIll pause and re-query Monday API")
            complexityError = True
            counter = 1
            while complexityError and counter < 30:
                print(f"\nTrying Mpnday.com API. Try #{counter} from (_get_item_objects_list - getting status value )")
                time.sleep(2)
                try:
                    status_value = create_column_value(id='name', column_type=ColumnType.name, value=str(item_name))
                    item_objects_list = board.get_items_by_column_values(column_value=status_value)
                    complexityError = False
                except Exception as e:
                    print(f"LOG ERROR: Error getting board objects list  matching item name {item_name} from Monday API on try # {counter}. ERROR DETAILS: {e}")
                    counter = counter + 1
            if complexityError:
                item_objects_list = []

        if item_objects_list:
            print(f"LOG SUCCESS: Item objects list returned for the search for item name \"{item_name}\"")
        return item_objects_list

    def get_column_id_by_name(self, col_name, board_name=None):
        """
        Gets the id of a column whose name is passed into the method. The board name is passed.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param col_name: str
        :param board_name: sr
        :return: Id of the column specfied
        """
        if not board_name:
            board_name = self.board_name

        # GET COLUMNS IN CURRENT BOARD AND FILTER OUT BOARD WITH COLUMN NAME/ TITLE SUPPLIED
        col_obj_list = self.get_columns_in_single_board(board_name=board_name)
        for col_obj in col_obj_list:
            if col_obj.title == col_name:
                col_id = col_obj.id
                print(f'LOG INFO: RESULT: Id found. Column name {col_obj.title}, Column Id: {col_id}')
                return col_id

        return None

    def get_column_type_by_name(self, col_title, board_name=None):
        """
        Gets the column type using the column name/ title supplied
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param col_name: column name/title: str
        :param board_name: board name
        :return:
        """
        if not board_name:
            board_name = self.board_name

        # GET COLUMNS IN CURRENT BOARD AND FILTER OUT BOARD WITH COLUMN NAME/ TITLE SUPPLIED
        col_obj_list = self.get_columns_in_single_board(board_name=board_name)
        for col_obj in col_obj_list:
            if col_obj.title == col_title:
                col_type = col_obj.type
                print(f"LOG INFO: RESULT: Found type for column '{col_title}' located in board '{board_name}'. Column Type: {col_type}")
                return col_type

        return None

    def get_status_of_item(self, item_name, col_title="Status", board_name=None):
        """
        Gets the status of an item from a particular board.
        Primarily will search in the default Status column if no status column is defined.
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: str
        :param col_title: str
        :param board_name: str
        :return: status of item: str
        """
        value_index = 2  # THE VALUE OF AN ITEM FROM A PARTICULAR COLUMN IS THE THIRD ITEM IN THE COLUMN OBJECT
        if not board_name:
            board_name = self.board_name

        # GET THE ITEM OBJECT FOR THE ITEM PARAMETERS SUPPLIED
        item_obj = self.get_specific_item_by_name(item_name=item_name, board_name=board_name)

        # GET THE COLUMN VALUE OBJECT FROM THE ITEM OBJECT
        col_val_object = item_obj.get_column_value(title=col_title)

        # THIRD KEY OF THE DICT FORM OF COL_VAL_OBJECT IS THE VALUE
        col_val_dict = col_val_object.__dict__
        print(f"LOG INFO: Column Information : {col_val_dict}")
        keys = list(col_val_dict.keys())

        col_val_key = keys[value_index]
        value = col_val_dict[col_val_key]

        col_type = self.get_column_type_by_name(col_title=col_title, board_name=board_name)
        if col_type == 'color':
            value_dict = value.__dict__
            status_index = col_val_dict.get('index')

            status = value_dict['labels'][str(status_index)]
            return status

        return value

    def change_value_of_column(self, item_name, col_title, new_value, board_name=None, link_text=None):
        """
        Changes the value of a column. Column type needs to be checked first
        If no board name is passed to this method, the name passed in the __init__ method is used.
        :param item_name: Name of item/ task: str
        :param col_title: Name/ title of column: str
        :param new_value: New value: Date values should be entered in the format. YYYY-MM-DD: str
        :param board_name: Name of board: str
        :return: The new value: str
        """

        if new_value is None:
            # IF NEW VALUE IS OF NONE TYPE, RETURN NONE. THIS MAY HAPPEN WHEN VALUES FROM THE DATABASE ARE NONE (FOR AUTOMATION)
            return None

        column_value = None
        if not board_name:
            board_name = self.board_name

        # GET THE ITEM OBJECT FOR THE ITEM PARAMETERS SUPPLIED
        item_obj = self.get_specific_item_by_name(item_name=item_name, board_name=board_name)
        if item_obj is None:
            print(f"LOG WARN: Item object is for item name \"{item_name}\" \"None\".")
            print(f"\nLOG WARN:****Max query complexity for API might have been reached trying to get item object for {item_name}. Cooling off  before retrying.")
            complexityError = True
            counter = 1
            while complexityError and counter < 30:
                print(f"\nTrying Mpnday.com API. Try #{counter} from (change_value_of_column -  get item object)")
                time.sleep(2)
                item_obj = self.get_specific_item_by_name(item_name=item_name, board_name=board_name)
                if item_obj:
                    print(f"LOG SUCCESS: Item object for item name \"{item_name}\" was found on try #{counter}.")
                    complexityError = False
                else:
                    print(f"LOG ERROR: Cannot get item object to use to change column value.")
                    counter = counter + 1

            if item_obj is None:
                print(f"LOG WARN: Item object for item name \"{item_name}\" is \"None\" after {counter} tries. Column value will not be changed!")

        # GET THE ID OF THE SPECIFIED COLUMN
        col_id = self.get_column_id_by_name(col_name=col_title)

        # GET COLUMN TYPE AND COMPOSE COLUMN VALUE
        # ==================================================================================================
        col_type = self.get_column_type_by_name(col_title=col_title, board_name=board_name)
        if col_type == 'long-text':
            column_type = ColumnType.long_text
            column_value = create_column_value(id=col_id, column_type=column_type, text=str(new_value))

        elif col_type == 'numeric':
            column_type = ColumnType.numbers
            column_value = create_column_value(id=col_id, column_type=column_type, value=float(new_value))

        elif col_type == 'text':
            column_type = ColumnType.text
            column_value = create_column_value(id=col_id, column_type=column_type, value=str(new_value))

        elif col_type == 'name':
            column_type = ColumnType.name
            column_value = create_column_value(id=col_id, column_type=column_type, value=str(new_value))

        elif col_type == 'color':
            column_type = ColumnType.status
            labels_string = self.get_column_settings_string_for_board(board_name=board_name, col_title=col_title)

            labels = json.loads(labels_string)

            settings = StatusSettings(**labels)
            column_value = create_column_value(id=col_id, column_type=column_type, label=str(new_value), settings=settings)
            column_value.change_status_by_label(new_value)

        elif col_type == 'date':
            column_type = ColumnType.date
            column_value = create_column_value(id=col_id, column_type=column_type, date=str(new_value))

        elif col_type == 'link':
            column_type = ColumnType.link
            if link_text:
                column_value = create_column_value(id=col_id, column_type=column_type, url=str(new_value), text=str(link_text))
            else:
                column_value = create_column_value(id=col_id, column_type=column_type, url=str(new_value))
        # ===================================================================================================

        # FINALLY, USE COMPOSED COLUMN VALUE TO UPDATE COLUMN
        if column_value:
            try:
                item_obj.change_column_value(column_value=column_value)
                return new_value
            except Exception as e:
                print(f"LOG ERROR: Changing column value for item {item_name}, column {col_title} failed: DETAILS: {e}")
                print(f"LOG INFO: Will pause and retry for item {item_name}")
                complexityError = True
                counter = 1
                while complexityError and counter < 30:
                    print(f"\nTrying Mpnday.com API. Try #{counter} from (change_value_of_column -  changing value of column)")
                    time.sleep(2)
                    try:
                        item_obj.change_column_value(column_value=column_value)
                        complexityError = False
                        print(f"LOG SUCCESS: Value of column changed to {column_value}")
                        return new_value
                    except Exception as e:
                        print(f"LOG ERROR: Changing column value for item {item_name}, column {col_title} failed on {counter} try: DETAILS: {e}")
                        counter = counter + 1

        return None

    def move_item_to_group(self, item_name, group_name, board_name=None):
        """
        Moves an item with name specified to the group with the group name specified
        :param item_name: item name: str
        :param group_name: group name: str
        :param board_name: str
        :return:
        """
        if not board_name:
            board_name = self.board_name

        # GET THE ITEM OBJECT FOR THE ITEM PARAMETERS SUPPLIED
        item_obj = self.get_specific_item_by_name(item_name=item_name, board_name=board_name)

        # CHECK IN CACHE FOR BOARD OBJECT
        print(f"LOG INFO: Checking in board object cache for board name '{board_name}'.")
        board = self.board_objects_cache.get(board_name)

        if board is None:
            try:
                board = CLIENT.get_board(name=board_name)
                print(f"LOG INFO: Board object for board with name {board.name} exists!")
                self.board_objects_cache[board_name] = board
            except Exception as e:
                print(f"LOG WARN: No board found with name: {board_name}. ERROR DETAILS: {e}")
                print(f"LOG WARN: Cannot move item to group {group_name}")
                return
        else:
            print(f"LOG INFO: Found board object for board in cache. Board name {board.name} exists!")

        group_object = None
        try:
            group_object = board.get_group(title=group_name)
        except Exception as e:
            print(f"LOG ERROR: Could not find group with name {group_name}: ERROR DETAILS: {e}")
            complexityError = True
            counter = 1
            while complexityError and counter < 30:
                print(f"\nTrying Mpnday.com API. Try #{counter} (from move_item_to_group - get group object)")
                time.sleep(2)
                print(f"LOG INFO: Trying to query API again.")
                try:
                    group_object = board.get_group(title=group_name)
                    complexityError = False
                except Exception as e:
                    print(f"LOG ERROR: ERROR DETAILS: {e}.")
                    counter = counter + 1

            if complexityError:
                print(f"LOG ERROR: Could not find group with name {group_name}: ")
                return None

        group_id = group_object.id
        moved_item = None
        try:
            moved_item = item_obj.move_to_group(group_id=group_id)
        except Exception as e:
            print(f"LOG ERROR: Moving item to group failed! Item Name: {item_name}. ERROR DETAILS: {e}. WIll pause and query API again")
            complexityError = True
            counter = 1
            while complexityError and counter < 30:
                print(f"\nTrying Mpnday.com API. Try #{counter} (from move_item_to_group -  move item to group)")
                time.sleep(2)
                try:
                    moved_item = item_obj.move_to_group(group_id=group_id)
                    complexityError = False
                except Exception as e:
                    print(f"LOG ERROR: Moving item to group failed on {counter} try. Item Name: {item_name}. ERROR DETAILS: {e}. ")
                    counter = counter + 1

            if complexityError:
                print(f"LOG ERROR: Could not move item {item_name} to group {group_name} after multiple tries")
                return None

        print(f"LOG SUCCESS: Item {item_name} successfully moved to group {group_name}")
        return moved_item
