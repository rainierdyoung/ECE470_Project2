from flask import Flask, request, jsonify
import mysql.connector 
from mysql.connector import Error, pooling
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from smtplib import SMTPException 
import boto3   
from botocore.exceptions import ClientError

app = Flask(__name__) #initialize a new flask application
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()



try: #initialize pool 
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name= 'my_pool',
        pool_size= 5,
        host = 'localhost',
        user = 'root',
        password = 'Pa@sspass19',
        database = 'online_auction'
        )
except Error as e: #if error occurs during connection
    print('Error creating a conneciton pool',e)



mail_settings = {
    "MAIL_SERVER":'smtp.gmail.com',
    "MAIL_PORT":587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": '470auctionsite@gmail.com',
    "MAIL_PASSWORD": 'xcbk qxmy mkoc jyxy'
} 
app.config.update(mail_settings)
mail = Mail(app)



def send_email(RECIPIENT, SUBJECT, BODY_TEXT, BODY_HTML):
                    # Replace sender@example.com with your "From" address.
            # This address must be verified with Amazon SES.
        SENDER = "470 Auction Site <470Auctionsite@gmail.com>"
        #SENDER = "Sender Name <470Auctionsite@gmail.com>" original working


            # Replace recipient@example.com with a "To" address. If your account 
            # is still in the sandbox, this address must be verified.
     

            # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        AWS_REGION = "us-east-2"


    

            # The character encoding for the email.
        CHARSET = "UTF-8"

            # Create a new SES resource and specify a region.
        client = boto3.client('ses',region_name=AWS_REGION)
            # Try to send the email.
        try:
            #Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                #ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.	
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])


def process_auction_end(item_id):
    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True) # fetching bidder information
    try:
        #cursor.execute(""" 
         #           SELECT Bidder_ID, MAX(Bid_Amount) AS Highest_Bid, 
          #          FROM bids 
           #         WHERE Item_ID = %s
            #        GROUP BY Bidder_ID
             #       ORDER BY Highest_Bid DESC
              #      LIMIT 1""",
               #     (item_id,))
        cursor.execute("SELECT Email_Sent FROM items WHERE Item_ID = %s", (item_id,))
        email_sent_info=cursor.fetchone()
        if email_sent_info and email_sent_info['Email_Sent']:
            print('Email already sent for Item_ID: ', item_id)
            return
        query = """ SELECT Bidder_ID, Bid_Amount AS Highest_Bid 
                    FROM bids 
                    WHERE Item_ID = %s
                    ORDER BY Bid_Amount DESC
                    LIMIT 1"""
        print("query: ", query, "item_id :", item_id)
        cursor.execute(query, (item_id,))
        highest_bid = cursor.fetchone()  
        cursor.execute("SELECT Seller_ID FROM items WHERE Item_ID = %s", (item_id,))  #fetching seller information
        item_info = cursor.fetchone()

        if highest_bid:
            cursor.execute('SELECT Email FROM users WHERE User_ID = %s', (highest_bid['Bidder_ID'],))
            winner_info = cursor.fetchone()
            
            if winner_info:
                #print('Winner Email', winner_info)
                BODY_HTML = """<html>
            <head></head>
            <body>
            <h1>Congratualtions, You won the auction!</h1>
            </body>
            </html>
                        """   
                send_email('470Auctionsite@gmail.com', 'Auction Won', 'Congratualtions, You won the auction!', BODY_HTML)

                #send_email(str([winner_info['Email']]), 'Auction Won', 'Congratualtions, You won the auction!', BODY_HTML)


            if item_info:
                cursor.execute('SELECT Email FROM users WHERE User_ID = %s', (item_info['Seller_ID'],))
                seller_info = cursor.fetchone()
                if seller_info:
                    #print('Seller Email', seller_info)
                    BODY_HTML = """<html>
            <head></head>
            <body>
            <h1>Your auction has ended and your item was sold.</h1>
            </body>
            </html>
                        """   
                    #send_email(str([seller_info['Email']]), 'Your Auction has ended', "Your auction has ended and your item was sold.", BODY_HTML)
                    send_email('470Auctionsite@gmail.com', 'Your Auction has ended', "Your auction has ended and your item was sold.", BODY_HTML)
        else:
              if item_info:
                cursor.execute('SELECT Email FROM users WHERE User_ID = %s', (item_info['Seller_ID'],))
                seller_info = cursor.fetchone()
                if seller_info:
                    #print('Seller Email', seller_info)
                    BODY_HTML = """<html>
            <head></head>
            <body>
            <h1>Your auction has ended but no bids were place.</h1>
            </body>
            </html>
                        """   
                    #send_email(str([seller_info['Email']]), 'Your Auction has ended', "Your auction has ended and your item was sold.", BODY_HTML)
                    send_email('470Auctionsite@gmail.com', 'Your Auction has ended', "Your auction has ended but no bids were placed.", BODY_HTML)
        cursor.execute("UPDATE items SET Email_Sent=1 WHERE Item_ID=%s",(item_id,))
        connection.commit()

    except Error as e:
        print('Error while processing auction end',str(e)) 
    finally:
        cursor.close()
        connection.close()


@scheduler.task('interval', id = 'check_auctions', seconds = 10, misfire_grace_time=900)
def check_auctions():
    connection=None
    try:
        connection = create_db_connection()
        if connection is not None:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM items WHERE End_Date <= NOW()")
            auctions = cursor.fetchall()
            for auction in auctions:
                process_auction_end(auction['Item_ID'])
        else:
            print("Failed to connect.") 
    except Error as e:
        print('An error occured: ',e)
    finally:
        cursor.close()
        connection.close()


def create_db_connection(): #create a database connection
    connection =  None #initialize connection variable
    try:
        connection = pool.get_connection()
    except Error as e: #if error occurs during connection
        print('The error occured: ',e)
    return connection



@app.route('/items', methods = ['GET'])
def list_items():
    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(items)

@app.route('/get_results', methods = ['GET'])
def get_results():
    item_id = request.args.get("Item_ID")
    connection = create_db_connection()
    if connection is not None:
        cursor = connection.cursor(dictionary=True)
        get_bid_sql = """SELECT bids.Bid_ID, bids.Item_ID, bids.Bidder_ID, bids.Bid_Amount, bids.Bid_Time, users.Username AS Bidder_Username, items.Seller_ID 
        FROM bids 
        INNER JOIN users ON bids.Bidder_ID = users.User_ID 
        INNER JOIN items ON bids.Item_ID = items.Item_ID
        WHERE bids.Item_ID = %s 
        ORDER BY bids.Bid_Amount DESC 
        LIMIT 1"""
        cursor.execute(get_bid_sql, (item_id,)) #execute sql query to get bid information for given item id
        bid_info = cursor.fetchone() #fetch the highest bid for the item
        if bid_info:
            get_seller_sql = "SELECT Username FROM users WHERE User_ID = %s" #query to get sellers username
            cursor.execute(get_seller_sql, (bid_info['Seller_ID'],)) #executes query with seller id from bid info
            seller_info = cursor.fetchone() #fetch the sellers information
            bid_info['Seller_Username'] = seller_info['Username'] if seller_info else 'Unknown' #add sellers username to bid info or mark as unknown
            cursor.close()
            connection.close()
            return jsonify({"success":True, "result":bid_info}),200
        else:
            cursor.close()
            connection.close()
            return jsonify({"success":False, "msg":"No bids found for this item, or item doesnt exist!"})
    else:
        return jsonify({"success":False, "msg":"Database connection failed!"})
    
          


@app.route('/bid_item', methods = ['POST'])
def bid_item():
    bid_details = request.json #get bid details from json body request
    connection = create_db_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            add_bid_sql = "INSERT INTO bids(Item_ID, Bidder_ID, Bid_Amount, Bid_Time) VALUES (%s, %s, %s, NOW())" #sql query to insert bid
            cursor.execute(add_bid_sql, (bid_details['Item_ID'], bid_details['Bidder_ID'], bid_details['Bid_Amount']))
            connection.commit()
            return jsonify({"success":True, "msg":"Bid placed succesfully!"}),200 #return success message with status code 200
        except Error as e:
            return jsonify({"success":False, "msg":str(e)}),401 #return error message with status code 401
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({"success":False, "msg":"Database connection failed"}),500 #retrun error message with status code 500


@app.route('/check_auction', methods = ['POST'])
def check_auction():
    data = request.json
    item_id = data.get('Item_ID')
    connection = create_db_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""SELECT Item_ID, Seller_ID, Item_Name, 
                           End_Date FROM items WHERE Item_ID = %s AND End_Date < NOW()""", (item_id,))
            auction = cursor.fetchone()
            if auction:
                cursor.execute("""SELECT Bidder_ID, MAX(Bid_Amount) 
                               AS Highest_Bid FROM bids WHERE Item_ID = %s GROUP BY Bidder_ID, Item_ID""", (item_id,))
                highest_bid = cursor.fetchone()
                if highest_bid:
                    seller_msg = f"Your auction for '{auction['Item_Name']}' has ended. Highest bid: {highest_bid['Highest_Bid']}"
                    winner_msg = f"Congratulations! You won the auction for '{auction['Item_Name']}' with a bid of {highest_bid['Highest_Bid']}"
                    return jsonify({"success":True, "seller_msg":seller_msg}),200
                else:
                    return jsonify({"success":True, "msg":"Auction ended, but no bids were placed!"}),200
            else:
                return jsonify({"success":False, "msg":"Auction has not ended, or doesnt exist!"}),400
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({"success":False, "msg":"Database connection failed"}),500

@app.route('/add_item', methods = ['POST'])
def add_item():
    item_details = request.json #get item details from json body of request
    connection = create_db_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            add_item_sql = "INSERT INTO items(Seller_ID, Item_Name, Item_Desc, Start_Price, Start_Date, End_Date) VALUES (%s, %s, %s, %s, %s, %s)" #sql query to insert item
            cursor.execute(add_item_sql, (item_details['Seller_ID'], item_details['Item_Name'], item_details['Item_Desc'], item_details['Start_Price'], item_details['Start_Date'], item_details['End_Date']))
            connection.commit()
            return jsonify({"success":True, "msg":"Item added succesfully!"}),200 #return success message with status code 200
        except Error as e:
            return jsonify({"success":False, "msg":str(e)}),401 #return error message with status code 401
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({"success":False, "msg":"Database connection failed"}),500 #retrun error message with status code 500


@app.route('/register', methods = ['POST']) #defining a route for a user registration with POST method
def register_user(): 
    user_details = request.json #Get the JSON data sent with the request
    connection = create_db_connection()
    cursor = connection.cursor()
    insert_user_sql = "INSERT INTO users(Username, Password, Email, Creation_Date) VALUES (%s, %s, %s, NOW())" #sql query to insert user
    try:
        cursor.execute(insert_user_sql, (user_details['Username'], user_details['Password'], user_details['Email'])) #execute the query with data
        connection.commit() #commit the transaction
        return jsonify({"success":True, "msg":"User registered succesfully!"}),200 #return success message with status code 200
    except Error as e:
        return jsonify({"success":False, "msg":str(e)}),401 #return error message with status code 401
    finally:
        cursor.close()
        connection.close()

@app.route('/login', methods = ['POST']) #defining a route for user login with post method
def login_user():
    login_details = request.json #get login details from json body of request
    connection = create_db_connection() #create a new database connection
    if connection is not None:
        cursor = connection.cursor(dictionary=True)
        find_user_sql = "SELECT * FROM users WHERE Username = %s AND Password = %s" #sql query to find user by username and password
        try:    
            cursor.execute(find_user_sql, (login_details['Username'], login_details['Password'])) #execute query with provided login details
            user = cursor.fetchone() #getting one record from query result
            cursor.fetchall()
            if user: #if user was found
                return jsonify({"success": True, "msg":"Login succesful!", "user":user}),200
            else:
                return jsonify({"success":False, "msg":"Invalid username or password", "user":user}),200                
        except Error as e:
            return jsonify({"success":False, "msg": str(e), "user":user}),401
        finally:
            cursor.close()
            connection.close()
    else:
            return jsonify({"success":False, 'msg':"Database connection failed!"}),500
    

if __name__ == '__main__':
    app.run(debug=True, threaded = True)

