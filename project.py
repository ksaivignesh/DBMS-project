import streamlit as st
import mysql.connector
from datetime import datetime
import random

# def procedure(connection):
#     cursor = connection.cursor()
#     st.write("hello")
#     cursor.callproc('GetAllCustomers')

#         # Fetch all the results from the procedure
#     results = cursor.fetchall()

#         # Display the results
#     if results:
#         st.write("Customers:")
#         for row in results:
#             st.write(row)

#         # Close the cursor and connection
#     cursor.close()
#     connection.close()



# def triggers():
#     pass
# # Function to add feedback to the database
# def add_feedback_to_database(connection,cust_id):
#         cursor = connection.cursor()
#         feedback_text = '-'
#         feedback_date = '2001-01-01'
#         customer_id = cust_id
#         status_of_problem = '-'
#         query = "INSERT INTO feedback (feedback_id,cust_id, feedback, feedback_date, status_of_problem) VALUES (%s,%s, %s, %s, %s)"
#         cursor.execute(query, (random.randint(1,100),customer_id, feedback_text, feedback_date, status_of_problem))
#         connection.commit()
#         st.success("Feedback added successfully.")
        
        
# Function to display customer dashboard
def display_customer_dashboard(connection, customer_id, cursor):
    st.subheader("Customer Dashboard")

    # Display account details
    query_account = "SELECT * FROM account WHERE cust_id = %s"
    cursor.execute(query_account, (customer_id,))
    row_account = cursor.fetchone()

    # Display electricity bill
    query_invoice = "SELECT * FROM invoice WHERE account_no IN (SELECT account_no FROM account WHERE cust_id = %s)"
    cursor.execute(query_invoice, (customer_id,))
    row_invoice = cursor.fetchone()

    if row_account or row_invoice:
        # Create two columns
        col1, col2 = st.columns(2)

        # Display account details in the first column
        with col1:
            if row_account:
                st.write("Account details:")
                for column, value in row_account.items():
                    st.write(f"{column}: {value}")
            else:
                st.warning("No account details found for the specified customer ID.")

        # Display electricity bill in the second column
        with col2:
            if row_invoice:
                st.write("Electricity Bill:")
                for column, value in row_invoice.items():
                    st.write(f"{column}: {value}")
            else:
                st.warning("No bill found for the specified customer ID.")

    else:
        st.warning("No account details or bill found for the specified customer ID.")

def createprocedureforcustomer(connection, customer_id,cu):
    cursor = connection.cursor()

    # Creating the stored procedure
    query = '''
    CREATE PROCEDURE CalculateNetAmount(in cu float(10,2),OUT netAmountResult FLOAT(10, 2))
    BEGIN
        DECLARE presentReadingParam FLOAT(10, 2);
        DECLARE previousReadingParam FLOAT(10, 2);
        DECLARE consumptionUnitParam FLOAT(10, 2);
        DECLARE fixedChargeParam FLOAT(10, 2);
        DECLARE energyChargeParam FLOAT(10, 2);
        DECLARE taxParam FLOAT(10, 2);
        DECLARE interestParam FLOAT(10, 2);
        DECLARE previousBalanceParam FLOAT(10, 2);
        DECLARE interestPreBalanceParam FLOAT(10, 2);
        DECLARE othersParam FLOAT(10, 2);
        DECLARE creditParam FLOAT(10, 2);
        DECLARE concessionParam FLOAT(10, 2);
        

        SELECT
            present_reading,
            previous_reading,
            consumption_unit,
            fixed_charge,
            energy_charge,
            tax,
            interest,
            previous_balance,
            interest_pre_balance,
            others,
            credit,
            consession
        INTO
            presentReadingParam,
            previousReadingParam,
            consumptionUnitParam,
            fixedChargeParam,
            energyChargeParam,
            taxParam,
            interestParam,
            previousBalanceParam,
            interestPreBalanceParam,
            othersParam,
            creditParam,
            concessionParam
        FROM invoice
        WHERE account_no IN (SELECT account_no FROM account WHERE cust_id = %s);

        IF consumptionUnitParam < 200 THEN
            SET energyChargeParam = 0;
        ELSEIF consumptionUnitParam >= 200 AND consumptionUnitParam < 300 THEN
            SET energyChargeParam = 1.5 * energyChargeParam;
        ELSE
            SET energyChargeParam = 2 * energyChargeParam;
        END IF;

        SET netAmountResult = (
            (cu + energyChargeParam) +
            fixedChargeParam +
            taxParam +
            interestParam +
            previousBalanceParam +
            interestPreBalanceParam +
            othersParam -
            creditParam -
            concessionParam
        );

        UPDATE invoice
        SET net_amount = netAmountResult
        WHERE account_no IN (SELECT account_no FROM account WHERE cust_id = %s);

    END'''
    q1=''' 
        create procedure update_net(IN net_am FLOAT(10, 2),IN cust_id INT)
        begin
        UPDATE invoice
        SET net_amount = net_am
        WHERE account_no IN (SELECT account_no FROM account WHERE cust_id = cust_id);
        end
        '''
    
    try:
        cursor.execute(query,(customer_id,customer_id))
        
        cursor.callproc("CalculateNetAmount",[cu,0])
        cursor.execute("SELECT @netAmountResult")
        net_amount_result = cursor.fetchone()[0]
        cursor.execute(q1)
        cursor.callproc("update_net",[net_amount_result,customer_id])
        st.success("Stored procedure 'CalculateNetAmount' created and executed successfully.")
    except mysql.connector.Error as e:
        pass
        #st.error(f"Error creating/executing stored procedure: {e}")
    finally:
        cursor.close()
        

def executeprocedureforcustomer(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.callproc("CalculateNetAmount")
    # Fetching the results
    # for result in cursor.stored_results():
    #     results = result.fetchall()

    #     # Displaying the results in Streamlit
    # if results:
    #     for row in results:
    #         st.write(row)
    # else:
    #     st.write("No results found.")
    
def customer_login(connection):
    if st.button("go to admin login"):
        st.session_state.page_number = 2
    st.subheader("Customer Login")
    cust_email = st.text_input("Email ID:")
    cust_password = st.text_input("Password:", type="password")

    if st.button("Login"):
        cursor = connection.cursor(dictionary=True)
        query = "SELECT cust_id FROM customer WHERE email_id = %s AND PASSWORD = %s"
        cursor.execute(query, (cust_email, cust_password))
        customer_id = cursor.fetchone()
        if customer_id:
            st.success(f"Customer Login Successful! Welcome, Customer ID: {customer_id['cust_id']}")
            #display_customer_dashboard(connection, customer_id['cust_id'], cursor)
            #createprocedureforcustomer(connection,customer_id['cust_id'])
            #executeprocedureforcustomer(connection)
            display_customer_dashboard(connection,customer_id['cust_id'],cursor)
        else:
            st.warning("Invalid credentials.")
            
            

def admin_login(connection):    
    if st.button("go to customer login"):
        st.session_state.page_number = 1
    st.subheader("Admin Login")
    admin_id = st.text_input("Admin ID:")
    admin_password = st.text_input("Password:", type="password")
    if st.button("Login"):
        cursor = connection.cursor(dictionary=True)
        query = "SELECT admin_id, admin_type FROM admin WHERE admin_id = %s AND PASSWORD = %s"
        cursor.execute(query, (admin_id, admin_password))
        admin = cursor.fetchone()
        if admin:
            if admin['admin_type'] == 'admin':  # Check admin type for granting privileges
                st.success(f"Admin Login Successful! Welcome, Admin ID: {admin['admin_id']}")
                st.session_state.page_number=3
                # Call a function to display admin dashboard passing the connection, admin ID, and cursor
            else:
                st.warning("Not authorized as an admin.")
        else:
            st.warning("Invalid credentials.")

# Function to create a new customer
def create(connection):
    st.subheader("Create Customer")
    cust_id=st.text_input("Customer id")
    cust_name = st.text_input("Customer Name")
    cust_acc_type = st.text_input("Account type")
    cust_address = st.text_input("Address")
    cust_state = st.text_input("State")
    cust_city = st.text_input("City")
    cust_pincode = st.text_input("Pin code")
    cust_email = st.text_input("Email")
    cust_password = st.text_input("Password", type="password")
    cust_status = st.text_input("Status")
    
    if st.button("Add Customer"):
        cursor = connection.cursor()
        #cust_id = random.randint(5, 100)  # Generate a random customer ID
        val = (cust_id, cust_name, cust_acc_type, cust_address, cust_state, cust_city, cust_pincode, cust_email, cust_password, cust_status)
        query = "INSERT INTO customer (cust_id, cust_name, account_type, address, state, city, pincode, email_id, PASSWORD, STATUS) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, val)
        connection.commit()  # Commit changes to the database
        st.success("Customer successfully added")   
        # add_feedback_to_database(connection,cust_id)

def update(connection):
    st.subheader("Update Customer")
    cust_id_to_update = st.text_input("Enter Customer ID to Update")
    column_to_update = st.selectbox("Select Column to Update", ("cust_name", "account_type", "address", "state", "city", "pincode", "email_id", "PASSWORD", "STATUS"))
    new_value = st.text_input(f"Enter New Value for {column_to_update}")

    if st.button("Update"):
        cursor = connection.cursor()
        query = f"UPDATE customer SET {column_to_update} = %s WHERE cust_id = %s"
        val = (new_value, cust_id_to_update)
        cursor.execute(query, val)
        connection.commit()
        st.success("Customer information updated successfully")
        
# Function to delete a customer
def delete(connection):
    st.subheader("Delete Customer")
    cust_id_to_delete = st.number_input("Enter Customer ID to Delete", min_value=1, step=1)

    if st.button("Delete"):
        cursor = connection.cursor()
        query = "DELETE FROM customer WHERE cust_id = %s"
        val = (cust_id_to_delete,)
        cursor.execute(query, val)
        connection.commit()
        st.success("Customer deleted successfully")
        

# Function to execute join query and display results
def join_query(connection):
    st.subheader("Join Query Result Customer table, Account,electricity board")

    cursor = connection.cursor(dictionary=True)

    # Example join query to fetch data from multiple tables
    query = """
        SELECT c.cust_id, c.cust_name, a.account_id, a.account_no, eb.electricityboard_id, eb.electricityboard
        FROM customer c
        INNER JOIN account a ON c.cust_id = a.cust_id
        INNER JOIN electricityboard eb ON a.electricityboard_id = eb.electricityboard_id;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Displaying the results in Streamlit
    if results:
        for row in results:
            st.write(row)
    else:
        st.write("No results found.")



    
    

            

# Function to perform a nested query
def nested_query(connection):
    st.subheader("Nested Query Result of customer table")

    cursor = connection.cursor(dictionary=True)

    # Nested SQL query
    query = '''
    SELECT cust_name, (
        SELECT COUNT(*)
        FROM account
        WHERE account.cust_id = customer.cust_id
    ) AS num_of_accounts
    FROM customer;
    '''

    try:
        cursor.execute(query)
        results = cursor.fetchall()

        # Displaying the results in Streamlit
        if results:
            for row in results:
                st.write(f"Customer Name: {row['cust_name']}, Number of Accounts: {row['num_of_accounts']}")
        else:
            st.write("No results found.")
    except mysql.connector.Error as e:
        st.error(f"Error executing query: {e}")

    finally:
        cursor.close()
  

# Function to perform an aggregated query

# Function to perform an aggregated query
def aggregated_query(connection):
    st.title('Aggregated Query Example')

    st.subheader("Aggregated Query Result")

    cursor = connection.cursor(dictionary=True)

    # Get user input for the aggregate operation
    aggregate_operation = st.text_input("Enter the aggregate function on customer table(e.g., COUNT, SUM, AVG, MAX, MIN):")

    if aggregate_operation:
        # Define the aggregate query based on user input
        query = f'''
        SELECT {aggregate_operation}(1) AS aggregate_result
        FROM customer;
        '''

        try:
            cursor.execute(query)
            result = cursor.fetchone()

            # Displaying the result in Streamlit with a descriptive message
            if result:
                aggregate_result = result['aggregate_result']
                st.write(f"The result of '{aggregate_operation}' operation on customer data is: {aggregate_result}")
            else:
                st.write("No results found.")
        except mysql.connector.Error as e:
            st.error(f"Error executing query: {e}")

        finally:
            cursor.close()
            
            
def create_stored_procedure(connection):
    cursor = connection.cursor()

    # Creating the stored procedure
    query = '''
    CREATE PROCEDURE GetAllCustomers()
    BEGIN
        SELECT * FROM customer;
    END
    '''

    try:
        cursor.execute(query)
        st.success("Stored procedure 'GetAllCustomers' created successfully.")
    except mysql.connector.Error as e:
        st.error(f"Error creating stored procedure: {e}")

    finally:
        cursor.close()


def execute_stored_procedure(connection):
    cursor = connection.cursor(dictionary=True)

    try:
        # Calling the stored procedure
        cursor.callproc("GetAllCustomers")

        # Fetching the results
        for result in cursor.stored_results():
            results = result.fetchall()

        # Displaying the results in Streamlit
        if results:
            for row in results:
                st.write(row)
        else:
            st.write("No results found.")
    except mysql.connector.Error as e:
        st.error(f"Error executing stored procedure: {e}")

    finally:
        cursor.close()





def procedure(connection):
    create_stored_procedure(connection)
    st.subheader("Procedure Query")
    execute_stored_procedure(connection)



def create_trigger(connection):
    cursor = connection.cursor()

    # Creating the trigger
    query = '''
CREATE TRIGGER add_feedback_trigger
AFTER INSERT ON customer
FOR EACH ROW
BEGIN
    DECLARE feedback_text VARCHAR(255);
    DECLARE feedback_date DATE;
    DECLARE customer_id INT;
    DECLARE status_of_problem VARCHAR(50);

    SET feedback_text = 'Awesome';
    SET feedback_date = '2001-01-01';
    SET customer_id = NEW.cust_id;
    SET status_of_problem = 'No problem';

    INSERT INTO feedback (feedback_id, cust_id, feedback, feedback_date, status_of_problem)
    VALUES (RAND() * 100, customer_id, feedback_text, feedback_date, status_of_problem);
    
END;

    '''

    try:
        cursor.execute(query)
        st.success("Trigger 'my_trigger' created successfully.")
    except mysql.connector.Error as e:
        st.error(f"Error creating trigger: {e}")

    finally:
        cursor.close()
        
def triggers(connection):
    st.subheader("Trigger Query")
    create_trigger(connection)
    return
def generate_elecrtic_bill(connection):
    st.subheader("Generate Electric Bill for Customer")
    cust_id=st.text_input("Enter Customer ID:")
    cu=st.number_input("Enter consumption units:")
    #cursor = connection.cursor(dictionary=True)
    
    if st.button("Generate bill"):
        q=''' 
        create procedure update_cu(in cu float(10,2),IN cust_id INT)
        begin
        UPDATE invoice
        SET consumption_unit = cu
        WHERE account_no IN (SELECT account_no FROM account WHERE cust_id = cust_id);
        end
        '''
        cursor = connection.cursor(dictionary=True)
        cursor.execute(q)
        cursor.callproc("update_cu",[cu,cust_id])
        createprocedureforcustomer(connection,cust_id,cu)
        
        display_customer_dashboard(connection,cust_id,cursor)

  

def admin_page(connection):

    st.sidebar.title("options")
    crud_option = st.sidebar.selectbox("Select an operation",["Create Customer","Update Customer","Delete Customer","join query","nested query","aggregated query","procedure","triggers","generate elecrtic bill"])
    if crud_option == "Create Customer":
        create(connection)
    elif crud_option == "Update Customer":
        update(connection)
    elif crud_option == "Delete Customer":
        delete(connection)
    elif crud_option== "join query":
        join_query(connection)
    elif crud_option== "nested query":
        nested_query(connection)
    elif crud_option== "aggregated query":
        aggregated_query(connection)
    elif crud_option== "procedure":
        procedure(connection)
    elif crud_option== "triggers":
        triggers(connection)
    elif crud_option== "generate elecrtic bill":
        generate_elecrtic_bill(connection)
    
    
    


    
    
# Streamlit App
def main():
    st.title("Electricity Billing System")

    # Initialize the connection
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="chintu@1",
        database="dbms_project"
    )
  
    # Initialize session state
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1  # Default to Page One
    # Function for customer login
    # Display content based on current page
    if st.session_state.page_number == 1:
        customer_login(connection)
    elif st.session_state.page_number == 2:
        admin_login(connection)
    elif st.session_state.page_number == 3:
        admin_page(connection)

 
    # Close the connection when the Streamlit app is done
    connection.close()


# Run the Streamlit app
if __name__ == "__main__":
    main()