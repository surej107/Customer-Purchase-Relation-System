import sqlite3
import streamlit as st
import pandas as pd


class DatabaseManager:
    def __init__(self, db_name="cps.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

    def initialize(self):
        self.execute_query('''CREATE TABLE IF NOT EXISTS customers (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                email TEXT UNIQUE NOT NULL,
                                phone TEXT NOT NULL,
                                location TEXT,
                                age INTEGER,
                                occupation TEXT,
                                gender TEXT,
                                active INTEGER DEFAULT 1)''')
        self.execute_query('''CREATE TABLE IF NOT EXISTS products (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                price REAL NOT NULL,
                                stock INTEGER NOT NULL,
                                rating REAL,
                                active INTEGER DEFAULT 1)''')
        self.execute_query('''CREATE TABLE IF NOT EXISTS purchases (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                customer_id INTEGER,
                                product_id INTEGER,
                                quantity INTEGER NOT NULL,
                                purchase_date TEXT NOT NULL,
                                FOREIGN KEY(customer_id) REFERENCES customers(id),
                                FOREIGN KEY(product_id) REFERENCES products(id))''')


class CRPMSystem:
    def __init__(self):
        self.db = DatabaseManager()
        self.db.initialize()

    def main(self):
        st.title("Customer-Product Purchase System")
        menu = ["Customer Management", "Product Management", "Customer Purchases", "Analytics and Reports"]
        choice = st.sidebar.selectbox("Options", menu)

        if choice == "Customer Management":
            self.customer_management()
        elif choice == "Product Management":
            self.product_management()
        elif choice == "Customer Purchases":
            self.customer_purchases()
        elif choice == "Analytics and Reports":
            self.analytics_and_reports()

    def customer_management(self):
        option = st.radio("Choose an Option", ["Add Customer", "View Customers", "Update Customer", "Deactivate Customer", "Reactivate Customer"])
        if option == "Add Customer":
            self.add_customer()
        elif option == "View Customers":
            self.view_customers()
        elif option == "Update Customer":
            self.update_customer()
        elif option == "Deactivate Customer":
            self.deactivate_customer()
        elif option == "Reactivate Customer":
            self.reactivate_customer()

    def product_management(self):
        option = st.radio("Choose an Option", ["Add Product", "View Products", "Update Product", "Deactivate Product", "Reactivate Product"])
        if option == "Add Product":
            self.add_product()
        elif option == "View Products":
            self.view_products()
        elif option == "Update Product":
            self.update_product()
        elif option == "Deactivate Product":
            self.deactivate_product()
        elif option == "Reactivate Product":
            self.reactivate_product()

    def customer_purchases(self):
        option = st.radio("Choose an Option", ["Add Purchase", "View Purchase History"])
        if option == "Add Purchase":
            self.add_purchase()
        elif option == "View Purchase History":
            self.view_purchase_history()

    def analytics_and_reports(self):
        sales_report = self.db.fetch_all('''
            SELECT SUM(pp.quantity * p.price) AS total_revenue,
                SUM(pp.quantity) AS total_products_sold
            FROM purchases pp
            JOIN products p ON pp.product_id = p.id
        ''')
        total_revenue, total_products_sold = sales_report[0] if sales_report else (0, 0)
        st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        st.metric("Total Products Sold", total_products_sold)

        stock_data = self.db.fetch_all("SELECT name, stock FROM products")
        if stock_data:
            stock_df = pd.DataFrame(stock_data, columns=["Product Name", "Stock"])
            st.table(stock_df)

        top_customers = self.db.fetch_all('''
            SELECT c.name AS customer_name,
                SUM(pp.quantity * p.price) AS total_spent
            FROM purchases pp
            JOIN customers c ON pp.customer_id = c.id
            JOIN products p ON pp.product_id = p.id
            GROUP BY pp.customer_id
            ORDER BY total_spent DESC
            LIMIT 5
        ''')
        if top_customers:
            top_customers_df = pd.DataFrame(top_customers, columns=["Customer Name", "Total Spent"])
            st.table(top_customers_df)

        product_performance = self.db.fetch_all('''
            SELECT p.name AS product_name,
                SUM(pp.quantity) AS total_sold
            FROM purchases pp
            JOIN products p ON pp.product_id = p.id
            GROUP BY pp.product_id
            ORDER BY total_sold DESC
        ''')
        if product_performance:
            product_df = pd.DataFrame(product_performance, columns=["Product Name", "Total Sold"])
            st.bar_chart(product_df.set_index("Product Name"))

        # Line chart for sales trend by product
        sales_trend = self.db.fetch_all('''
            SELECT p.name AS product_name,
                pp.purchase_date,
                SUM(pp.quantity) AS total_sold
            FROM purchases pp
            JOIN products p ON pp.product_id = p.id
            GROUP BY p.name, pp.purchase_date
            ORDER BY pp.purchase_date ASC
        ''')
        if sales_trend:
            trend_df = pd.DataFrame(sales_trend, columns=["Product Name", "Purchase Date", "Total Sold"])
            trend_df["Purchase Date"] = pd.to_datetime(trend_df["Purchase Date"])
            pivot_trend = trend_df.pivot(index="Purchase Date", columns="Product Name", values="Total Sold").fillna(0)
            st.line_chart(pivot_trend)


    def add_customer(self):
        with st.form("add_customer_form"):
            customer_data = {
                "id": st.number_input("Customer ID", min_value=1, step=1),
                "name": st.text_input("Customer Name"),
                "email": st.text_input("Email"),
                "phone": st.text_input("Phone Number"),
                "location": st.text_input("Location"),
                "age": st.number_input("Age", min_value=0),
                "occupation": st.text_input("Occupation"),
                "gender": st.selectbox("Gender", ["Male", "Female", "Other"]),
            }
            submit = st.form_submit_button("Add Customer")
            if submit:
                try:
                    self.db.execute_query(
                        "INSERT INTO customers (id, name, email, phone, location, age, occupation, gender) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(customer_data.values())
                    )
                    st.success("Customer added successfully!")
                except sqlite3.IntegrityError:
                    st.error("Customer ID or email already exists.")

    def view_customers(self):
        customers = self.db.fetch_all("SELECT * FROM customers WHERE active=1")
        if customers:
            df = pd.DataFrame(customers, columns=["ID", "Name", "Email", "Phone", "Location", "Age", "Occupation", "Gender", "Active"])
            st.table(df)

    def update_customer(self):
        customer_id = st.number_input("Customer ID to Update", min_value=1, step=1)
        with st.form("update_customer_form"):
            customer_data = {
                "name": st.text_input("Updated Name"),
                "email": st.text_input("Updated Email"),
                "phone": st.text_input("Updated Phone"),
                "location": st.text_input("Updated Location"),
                "age": st.number_input("Updated Age", min_value=0),
                "occupation": st.text_input("Updated Occupation"),
                "gender": st.selectbox("Updated Gender", ["Male", "Female", "Other"]),
            }
            submit = st.form_submit_button("Update Customer")
            if submit:
                self.db.execute_query(
                    "UPDATE customers SET name=?, email=?, phone=?, location=?, age=?, occupation=?, gender=? WHERE id=?",
                    (*customer_data.values(), customer_id)
                )
                st.success("Customer updated successfully!")

    def deactivate_customer(self):
        customer_id = st.number_input("Customer ID to Deactivate", min_value=1, step=1)
        if st.button("Deactivate"):
            self.db.execute_query("UPDATE customers SET active=0 WHERE id=?", (customer_id,))
            st.success("Customer deactivated successfully!")

    def reactivate_customer(self):
        customer_id = st.number_input("Customer ID to Reactivate", min_value=1, step=1)
        if st.button("Reactivate"):
            self.db.execute_query("UPDATE customers SET active=1 WHERE id=?", (customer_id,))
            st.success("Customer reactivated successfully!")

    def add_product(self):
        with st.form("add_product_form"):
            product_data = {
                "id": st.number_input("Product ID", min_value=1, step=1),
                "name": st.text_input("Product Name"),
                "price": st.number_input("Price", min_value=0.0, step=0.01),
                "stock": st.number_input("Stock", min_value=0),
                "rating": st.number_input("Rating (0-5)", min_value=0.0, max_value=5.0, step=0.1),
            }
            submit = st.form_submit_button("Add Product")
            if submit:
                try:
                    self.db.execute_query(
                        "INSERT INTO products (id, name, price, stock, rating) VALUES (?, ?, ?, ?, ?)",
                        tuple(product_data.values())
                    )
                    st.success("Product added successfully!")
                except sqlite3.IntegrityError:
                    st.error("Product ID already exists.")

    def view_products(self):
        products = self.db.fetch_all("SELECT * FROM products WHERE active=1")
        if products:
            df = pd.DataFrame(products, columns=["ID", "Name", "Price", "Stock", "Rating", "Active"])
            st.table(df)

    def update_product(self):
        product_id = st.number_input("Product ID to Update", min_value=1, step=1)
        with st.form("update_product_form"):
            product_data = {
                "name": st.text_input("Updated Name"),
                "price": st.number_input("Updated Price", min_value=0.0, step=0.01),
                "stock": st.number_input("Updated Stock", min_value=0),
                "rating": st.number_input("Updated Rating (0-5)", min_value=0.0, max_value=5.0, step=0.1),
            }
            submit = st.form_submit_button("Update Product")
            if submit:
                self.db.execute_query(
                    "UPDATE products SET name=?, price=?, stock=?, rating=? WHERE id=?",
                    (*product_data.values(), product_id)
                )
                st.success("Product updated successfully!")

    def deactivate_product(self):
        product_id = st.number_input("Product ID to Deactivate", min_value=1, step=1)
        if st.button("Deactivate"):
            self.db.execute_query("UPDATE products SET active=0 WHERE id=?", (product_id,))
            st.success("Product deactivated successfully!")

    def reactivate_product(self):
        product_id = st.number_input("Product ID to Reactivate", min_value=1, step=1)
        if st.button("Reactivate"):
            self.db.execute_query("UPDATE products SET active=1 WHERE id=?", (product_id,))
            st.success("Product reactivated successfully!")

    def add_purchase(self):
        with st.form("add_purchase_form"):
            purchase_data = {
                "customer_id": st.number_input("Customer ID", min_value=1, step=1),
                "product_id": st.number_input("Product ID", min_value=1, step=1),
                "quantity": st.number_input("Quantity", min_value=1, step=1),
                "purchase_date": st.date_input("Purchase Date"),
            }
            submit = st.form_submit_button("Add Purchase")
            if submit:
                try:
                    self.db.execute_query(
                        "INSERT INTO purchases (customer_id, product_id, quantity, purchase_date) VALUES (?, ?, ?, ?)",
                        tuple(purchase_data.values())
                    )
                    st.success("Purchase added successfully!")
                except sqlite3.IntegrityError:
                    st.error("Invalid Customer ID or Product ID.")

    def view_purchase_history(self):
        purchases = self.db.fetch_all('''
            SELECT pp.id, c.name AS customer_name, p.name AS product_name, pp.quantity, pp.purchase_date
            FROM purchases pp
            JOIN customers c ON pp.customer_id = c.id
            JOIN products p ON pp.product_id = p.id
        ''')
        if purchases:
            df = pd.DataFrame(purchases, columns=["Purchase ID", "Customer Name", "Product Name", "Quantity", "Purchase Date"])
            st.table(df)


if __name__ == "__main__":
    app = CRPMSystem()
    app.main()
