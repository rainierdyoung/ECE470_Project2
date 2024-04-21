import requests

def register_user(base_url, username, password, email):
    data =  {"Username":username, "Password":password, "Email":email}
    response = requests.post(f"{base_url}/register", json = data)
    print(response.text)
    return response.json()

def login_user(base_url, username, password):
    data = {"Username":username, "Password":password} #package login credentials into dictionary 
    response = requests.post(f"{base_url}/login", json = data) #sending a POST request to the login server with the credentials
    if response.status_code == 200: #if login is succesful
        return response.json()    
    else:
        return {"success":False, "msg":"Failed to login, status code: " +str(response.status_code)}

def add_item(base_url, seller_id, item_name, item_desc, start_price, start_date, end_date):
    data = {"Seller_ID":seller_id, "Item_Name":item_name, "Item_Desc":item_desc, "Start_Price":start_price, "Start_Date":start_date, "End_Date":end_date}
    response = requests.post(f"{base_url}/add_item", json = data)
    return response.json()


def bid_item(base_url, item_id, bidder_id, bid_amount):
    data = {"Item_ID":item_id,"Bidder_ID":bidder_id,"Bid_Amount":bid_amount}
    response = requests.post(f"{base_url}/bid_item", json=data)
    return response.json

def list_items(base_url):
    response = requests.get(f"{base_url}/items")
    return response.json()

def get_results(base_url, item_id):
    response = requests.get(f"{base_url}/get_results", params={"Item_ID":item_id})
    if response.status_code == 200:
        return response.json()
    else:
        return {"success":False, "msg":"Failed to retrieve results"}

def check_auction(base_url, item_id):
    data = {"Item_ID":item_id}
    response = requests.post(f"{base_url}/check_auction", json = data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            if "seller_msg" in result:
                print(result["seller_msg"])
            else:
                print(result["msg"])
        else:
            print("Auction check failed!", result.get('msg'))
    elif response.status_code == 400:
        print("Auction has not ended, or doesnt exist!", response.status_code)
    else:
        print("Failed to check auction end!", response.status_code)

#print(register_user(base_url, "New_User", "New_Pass", "new@gmail.com"))

#print(login_user(base_url, "New_User", "New_Pass"))

#print(list_items(base_url))

#print(add_item(base_url, "7", "Shirt_2", "a black shirt", "1.50", "2024-03-06 00:00:00", "2024-03-10 00:00:00"))

#print(bid_item(base_url, "1", "7", "2.50"))


def main_client_logic():
    base_url = 'http://127.0.0.1:5000'
    print("Welcome to the Auction Site!")
    role = input("Do you want to be a seller or a bidder? Enter 'Seller' or 'Bidder':").strip().lower()
    action = input("Do you want to register or login? Enter 'Register' or 'Login'").strip().lower()


    if action == "register": #if user chooses to register then register, else, continue to login
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        email = input("Enter your email address: ")
        registration_response = register_user(base_url, username, password, email) #registration response
        print(registration_response)
    
    username = input("Enter your username: ") 
    password = input("Enter your password: ")
    login_response = login_user(base_url, username, password)
    print(login_response)

    if login_response.get("success"): #if login response is succesful and user is logged in
        
        list = input("Would you like to list items? Enter y or n: ").strip().lower()
        if list == "y":
            print("Current Items: ")
            print(list_items(base_url))  

        chck_auct = input("Would you like to check the results of an auction? Enter y or n: ").strip().lower()
        if chck_auct == "y":    
            auction_to_check = input("Enter the id for the item which you would like to check :")
            check_auction(base_url, auction_to_check)
         

        check_results = input("Would you like to view the highest bid for an Item? Enter y or n: ").strip().lower()
        if check_results == "y":
            item_to_fetch = input("Enter the ID for the item which you would like to check :")
            ch_results = get_results(base_url, item_to_fetch)
            print("Auction Results: ")
            print(ch_results)

        if role == "seller": #selling procedure
            item_name = input("Enter the title of item you would like to sell: ")
            item_desc = input("Enter a description for your item: ")
            start_price = input("Enter the starting price for your item: ")
            start_date = input("Enter a start date of auction: YYYY-MM-DD: ")
            end_date = input("Enter a end date for the auction: YYYY-MM-DD: ")
            seller_id = login_response.get("user",{}).get("User_ID")
            add_item_response = add_item(base_url, seller_id, item_name, item_desc, start_price, start_date, end_date)
            print(add_item_response)
        elif role == "bidder": #bidding procedure   
            item_id = input("Which item would you like to bid on? Enter the item ID #: ")
            bid_amount = input("How much would you like to bid?: ")
            bidder_id = login_response.get("user",{}).get("User_ID")
            bid_item_response = bid_item(base_url, item_id, bidder_id, bid_amount)
            print(bid_item_response)
        else:
            print("Invalid role selected!")

    print("The Client will now exit, please restart if you would like to continue using the site.")
        
        

main_client_logic()

