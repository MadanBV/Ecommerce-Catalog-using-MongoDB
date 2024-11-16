from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['amazon_catalog']
product_collection = db['products'] 
user_collection = db['users']  

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if user_collection.find_one({"email": email}):
            flash("Email already registered!")
            return redirect(url_for('signup'))

        # Hash the password and store user details
        hashed_password = generate_password_hash(password) 
        user_collection.insert_one({'username': username, 'email': email, 'password': hashed_password}) #Insert data
        flash("Signup successful! Please login.")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = user_collection.find_one({"email": email}) #Search emai id
        
        # Verify user and password
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash("Login successful!")
            return redirect(url_for('index'))
        
        flash("Invalid email or password!")
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('login'))

# Home route
@app.route('/')
def index():
    if 'user_id' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    # Fetch filter parameters 
    search = request.args.get('search')
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_stars = request.args.get('min_stars', type=float)
    sort_by = request.args.get('sort_by') 

    products = []
    total_count = 0

    # Build MongoDB query
    query = {}
    if search:
        query['title'] = {'$regex': search, '$options': 'i'}  # Case-insensitive search on title
    if category:
        query['categoryName'] = category
    if min_price is not None:
        query['price'] = {'$gte': min_price}
    if max_price is not None:
        if 'price' in query:
            query['price']['$lte'] = max_price
        else:
            query['price'] = {'$lte': max_price}
    if min_stars is not None:
        query['stars'] = {'$gte': min_stars}

    #Find count 
    total_count = product_collection.count_documents(query)
    
    # Determine sort order
    sort_order = []
    if sort_by == 'price_asc':
        sort_order = [('price', 1)]  # Ascending price
    elif sort_by == 'price_desc':
        sort_order = [('price', -1)]  # Descending price
    elif sort_by == 'reviews_asc':
        sort_order = [('reviews', 1)]  # Ascending reviews
    elif sort_by == 'reviews_desc':
        sort_order = [('reviews', -1)]  # Descending reviews

    # Fetch products with optional sorting
    if total_count > 0:
        cursor = product_collection.find(query).limit(10)
        if sort_order:
            cursor = cursor.sort(sort_order)
        products = list(cursor)

    categories = product_collection.distinct('categoryName')
    
    return render_template('index.html', products=products, total_count=total_count, categories=categories, username=session.get('username'))


# Add product route
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        asin = request.form['asin']
        title = request.form['title']
        category = request.form['categoryName']
        stars = float(request.form['stars'])
        price = float(request.form['price'])

        #Insert data
        product_collection.insert_one({
            'asin': asin, 
            'title': title, 
            'categoryName': category, 
            'stars': stars, 
            'price': price
        })
        flash("Product added successfully!")
        return redirect(url_for('index'))
    
    return render_template('add_product.html')

# Edit product route
@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    product = product_collection.find_one({"_id": ObjectId(product_id)})
    if request.method == 'POST':
        
        title = request.form.get('title', product.get('title'))
        category = request.form.get('category', product.get('categoryName'))
        stars = request.form.get('stars', type=float, default=product.get('stars'))
        price = request.form.get('price', type=float, default=product.get('price'))
        
        # Update the product in MongoDB
        product_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {
                'title': title,
                'categoryName': category,
                'stars': stars,
                'price': price
            }}
        )
        flash("Product updated successfully!")
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)


# Delete product route
@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    #Delete record
    product_collection.delete_one({"_id": ObjectId(product_id)})
    flash("Product deleted successfully!")
    return redirect(url_for('index'))

# Display product route
@app.route('/display_product/<product_id>')
def display_product(product_id):
    if 'user_id' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    product = product_collection.find_one({"_id": ObjectId(product_id)})
    return render_template('display_product.html', product=product)

if __name__ == '__main__':
    app.run(debug=True)
 