from ast import Invert
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import Flask, request, jsonify,session
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import jwt,json


















app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'iitm@usha'
# Replace with your SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# jwt = JWTManager(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    status=db.Column(db.String(20))
    cart = db.Column(db.JSON())               

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer)
    rate = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"))
    store_manager_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))
    units = db.Column(db.String(20))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    quantity = db.Column(db.Float)
    amount= db.Column(db.Float)
    status = db.Column(db.String)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']
    role=data['role']
    name=data['name']
    email=data['email']
    if role=='manager':
        status='pending'
    else:
        status='approved'

    if User.query.filter_by(username=username).first():
        return jsonify({'flash_message': 'Username already exists'}), 200
    
    user = User(name=name,username=username, password=password, role=role,status=status,email=email,cart=json.dumps({}))
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    print(data)
    username = data['username']
    password = data['password']
    role=data['role']
    print(role)
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        print(user.role)
        User.query.filter_by(username=username).update({"role": role})
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
# User login endpoint

@app.route('/dele', methods=['POST'])
def dele():
    data = request.get_json()
    print(data)
    username = data['username']
    password = data['password']
    role=data['role']
    print(role)
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    
    
@app.route('/login', methods=['POST'])
def login():
    session["user_id"] = None
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        role=data['role']
        print(username,password,role)
        user1 = User.query.filter_by(username=username, password=password,role=role,status='pending').first()
        if user1:
            return jsonify({"flash_message":"Please wait till admin approves "}),200
        user = User.query.filter_by(username=username, password=password,role=role,status='approved').first()
        print(user)
        if user:
            print("user found")
            expiration = datetime.utcnow() + timedelta(minutes=30)
            # Convert expiration time to timestamp (integer value)
            expiration_timestamp = int(expiration.timestamp())
            # Generate JWT token
            token = jwt.encode({
                'user': username,
                'exp': expiration_timestamp
            }, app.config['SECRET_KEY'], algorithm='HS256')
            session.permanent = True
            session["user_id"]=user.id 
            print(type(token))
            # print(session.get("user_id"))
            cart_list=[]
            if role=="user":
                cart=json.loads(user.cart)
                for i in cart.values():
                    for j in i:
                        cart_list.append(j)
                print(cart_list)
            return jsonify({'token':  token,'role':user.role ,'id':user.id ,'username':user.username,"cart_list":cart_list}),201
        else:
            return jsonify({'flash_message': 'Credentials Mismatch'}), 202
    except Exception as e:
    # Log the error for debugging
        print('Error:', str(e))
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/store_requests', methods=['GET'])
def store_requests():
    store_manager = User.query.filter_by(role='manager', status='pending').all()
    
    if not store_manager:
        return jsonify({'message': 'No requests for Approval are available'}), 201
    print(store_manager)
    # print(type(store_manager))
    final_array=[]
    for i in store_manager:
        newobject = {
            'name':i.name,
            'username':i.username,
            'id':i.id,
        }
        final_array.append(newobject) 
    return jsonify({'storemanagers':final_array}),202

@app.route('/deleteProducts', methods=['GET'])
def deleteProducts():
    
    # print(token)
    product_list = Product.query.filter_by(status="delete").all()
    delete_plist=[]
    for i in product_list:
        category_id =i.category_id
        store_manager=i.store_manager_id
        category = Category.query.get(category_id)
        manager=User.query.get(store_manager)
        print(manager.username)
        obj={"product_id":i.product_id,"product_name":i.product_name,"category_name":category.category_name,"manager_name":manager.username}
        delete_plist.append(obj)
    return jsonify({'deleteProducts':delete_plist})

@app.route('/accept', methods=['POST'])
def accept():
    data = request.get_json()
    id = data['id']
    print(id)
    User.query.filter_by(id=id).update({"status": 'approved'})
    db.session.commit()
    return jsonify({'message': 'Manager approved successfully'}), 201



@app.route('/reject', methods=['POST'])
def reject():
    data = request.get_json()
    id = data['id']
    user = User.query.filter_by(id=id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Manager Rejected successfully'}), 201
    
@app.route('/deleteProduct', methods=['POST'])
def deleteProduct():
    data = request.get_json()
    id = data['id']
    product = Product.query.filter_by(product_id=id).first()
    db.session.delete(product)
    users=User.query.all()
    for i in users:
        if i.role=="user":
            cart = json.loads(i.cart)
            for j in cart.values():
                if id in j:
                    j.remove(id)
            i.cart = json.dumps(cart)            
    db.session.commit()
    return jsonify({'message': 'Product Deleted successfully'}), 201

@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    data = request.get_json()
    categoryName = data['categoryName']
    print(categoryName)
    if Category.query.filter_by(category_name=categoryName).first():
        return jsonify({'message': 'Category already exists'}), 400
    
    category = Category(category_name=categoryName)
    db.session.add(category)
    db.session.commit()

    return jsonify({'message': 'Category Added Succcesfully'}), 201

@app.route("/edit_category", methods=["POST", "GET"])
def edit_category():
    data = request.get_json()
    oldName = data['oldName']
    newName = data['newName']
    check_category = Category.query.filter_by(category_name=oldName).first()
    if check_category is not None:
        check_category.category_name = newName
        db.session.commit()
    else:
        return jsonify({"message":"not ok"}),201

@app.route("/getCategories", methods=["POST", "GET"])
def getCategories():
    list=[]
    #category_list = Category.query.all()
    category_list = Category.query.with_entities(Category.category_id, Category.category_name).all()
    # print(category_list)
    for i in category_list:
        obj={"category_id":i.category_id,"category_name":i.category_name}
        list.append(obj)
    #print(list)
    return jsonify({'categories':list}) 

@app.route('/deleteCategory', methods=['POST'])
def deleteCategory():
    data = request.get_json()
    id = data['id']
    print(id)
    category = Category.query.filter_by(category_id=id).first()
    #category = Category.query.filter_by(category_id=id).with_entities(Category.category_id, Category.category_name).first()
    product = Product.query.filter_by(category_id = id).all()
    for i in product:
        db.session.delete(i) 
    print(category)
    users = User.query.all()
    for i in users:
        if i.role=="user":
            cart = json.loads(i.cart)
            if str(id) in cart.keys():
                cart.pop(str(id))
            cart = json.dumps(cart)
            i.cart=cart
    
    print('Helloworld')
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category Deleted successfully'}), 201
    

  

@app.route('/addProduct',methods=['POST'])
def addProduct():
    data = request.get_json()
    product = Product()
    print(data)
    another_product = Product.query.filter_by(product_name = data["productName"]).first()
    if another_product:
        return jsonify({"flash_message":"product already exits with this name"}),202
    product.product_name = data["productName"]
    product.rate=data["price"]
    product.quantity=data["quantity"]
    product.category_id = data["category"]
    product.units = data["units"]
    store_manager= data['store_manager_id']
    product.status='ok'
    product.store_manager_id = store_manager 
    db.session.add(product)
    db.session.commit()
    return jsonify({'message': 'Product Added successfully'}), 201

@app.route('/editProduct',methods=['POST'])
def editProduct():
    data = request.get_json()
    print(data)
    old_product_name = data["editProductName"]
    product = Product.query.filter_by(product_name=old_product_name).first()
    # print(product.product_name,product.product_id)
    store_manager= data['store_manager_id']
    print(type(store_manager))
    if product:
        if int(store_manager)==product.store_manager_id:
            print("hi")
            product.product_name = data["editNewProductName"]
            product.rate=data["editPrice"]
            product.quantity=data["quantity"]
            product.category_id = data["category"]
            product.units = data["unit"]
            db.session.commit()
            return jsonify({'message': 'Product Edited successfully'}),200
        else:
            return jsonify({'flash_message':"UnAuthorized Access to edit ,Contact admin for more details"}),202
    else:
        return jsonify({"flash_message":'No product Found with this name'}),201
        

@app.route("/getcategories_products",methods=["GET"])
def getcategories_products():
    categories_product=[]
    category_list = Category.query.all()
    product_list=[]
    for i in category_list:
        products = Product.query.filter_by(category_id=i.category_id).all()
        for j in products:
            details={"category_name":i.category_name,"product_name":j.product_name,"price":j.rate,"units":j.units,"Quantity":j.quantity}
            categories_product.append(details)
    print(categories_product)
    return jsonify({"category_products":categories_product})

@app.route('/allproducts',methods=["GET"])
def allproducts():
    product_list=[]
    products = Product.query.all()
    for i in range(len(products)):
        product = {"product_name":products[i].product_name,"price":products[i].rate,"Quantity":products[i].quantity,"units":products[i].units}
        product_list.append(product)
    print(product_list)
    return jsonify({"products":product_list})


@app.route("/add_to_cart",methods=["POST"])
def add_to_cart():
    data=request.get_json()
    p_name=data["product_name"]
    user_id = data["user_id"]
    product = Product.query.filter_by(product_name=p_name).first()
    cat_id = product.category_id
    user = User.query.filter_by(id=user_id).first()
    cart = user.cart
    if cart is None:
        print("Hi")
        cart=json.dumps({})
    cart = json.loads(cart)
    if str(cat_id) in cart.keys():
        print("Ho")
        cart[str(cat_id)].append(product.product_id)
    else:
        print("Hi")
        cart[(str(cat_id))] = [product.product_id]
    cart = json.dumps(cart)
    user.cart = cart 
    db.session.commit()
    return jsonify({"message":"Added to Cart succesfully"})
        
@app.route("/remove_from_cart",methods=["POST"])
def remove_from_cart():
    data=request.get_json()
    p_name=data["product_name"]
    user_id = data["user_id"]
    product = Product.query.filter_by(product_name=p_name).first()
    cat_id = product.category_id
    user = User.query.filter_by(id=user_id).first()
    cart = user.cart
    cart = json.loads(cart)
    print("renove from cart :hello")
    for i in cart.keys():
        print(i)
        for j in cart[i]:
            if int(j) == product.product_id:
                print("Hi")
                cart[i].remove(j)
                break
    cart = json.dumps(cart)
    user.cart = cart 
    db.session.commit()
    return jsonify({"message":"Deleted from Cart succesfully"})
    
@app.route("/getcart",methods=["POST"])
def getcart():
    data=request.get_json()
    user_id = data["user_id"]
    print(user_id)
    user=User.query.get(user_id)
    cart=json.loads(user.cart)
    product_ids=[]
    finalCartList=[]
    for i in cart.values():
        for j in i:
            product_ids+=[int(j)]
    product_ids=list(set(product_ids))
    print(product_ids)
    if product_ids:
        for i in product_ids:
            print(i)
            product = Product.query.filter_by(product_id=i).first()
            print(product)
            category = Category.query.filter_by(category_id = product.category_id).first()
            details={"product_id":product.product_id,"category_name":category.category_name,"product_name":product.product_name,"price":product.rate,"units":product.units,"Quantity":product.quantity}
            finalCartList.append(details)
        print(finalCartList)
        return jsonify({"cartList":finalCartList})
    else:
        return jsonify({"message":"No products in your cart "}),201
    
        
        
                    
    
    
@app.route('/setDeleteProduct',methods=["POST"])
def setDeleteProduct():
    data = request.get_json()
    product_name = data['product_name']
    product = Product.query.filter_by(product_name=product_name).first()
    product.status="delete"
    db.session.commit()
    return jsonify({"message":"Sent to ADMIN for Confirmation to Delete Product"}) ,201
         

@app.route("/filterProducts",methods=["POST"])
def filterProducts():
    categories_product=[]
    data = request.get_json()
    category_id = data['category']
    print(category_id)
    f=1
    print(type(category_id))
    if(type(category_id)==str):
        category_id=int(category_id)
    if category_id==0:
        category_list = Category.query.all()
    else:
        f=0
        category_list=Category.query.filter_by(category_id=category_id).first()
    product_list=[]
    if f!=0:
        for i in category_list:
            print('hi')
            products = Product.query.filter_by(category_id=i.category_id).all()
            for j in products:
                details={"category_name":i.category_name,"product_name":j.product_name,"price":j.rate,"units":j.units,"Quantity":j.quantity}
                categories_product.append(details)
    else:
        products = Product.query.filter_by(category_id=category_list.category_id).all()
        for j in products:
            details={"category_name":category_list.category_name,"product_name":j.product_name,"price":j.rate,"units":j.units,"Quantity":j.quantity}
            categories_product.append(details)
    print(categories_product)
    return jsonify({"category_products":categories_product})


@app.route("/orders",methods=["POST"])
def orders():
    data = request.get_json()
    print(data)
    quantity =data['quantity']
    amount=data['amount']
    user_id=data['user_id']
    print(user_id)
    print(type(quantity),type(amount))
    print(quantity)
    print(amount)
    for key,value in quantity.items():
        order=Order()
        product = Product.query.filter_by(product_id = key).first()
        order.user_id =user_id
        order.product_id = key
        order.quantity = value
        order.price =  product.rate
        order.amount = amount[key]
        order.status = "success"
        Product.query.filter_by(product_id = key).update({"quantity":Product.quantity-value})
        db.session.add(order)
        db.session.commit()
    user = User.query.filter_by(id = user_id)
    user.cart  = json.dumps({}) 
    db.session.commit()
    return jsonify({"message":"ordered succesfully"})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5050)