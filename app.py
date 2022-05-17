import os
import sys

import flask
from flask import Flask, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import date
from sqlalchemy import text, create_engine
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect
from sys import stderr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ['MYSQL_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = SQLAlchemy(app)
engine = create_engine(os.environ['MYSQL_URI'], echo=True)
conn = engine.connect()
# ---------------------------------------------
# landing page


@app.route('/', methods=['GET'])
def get_index():
    return render_template('landing.html')


@app.route('/', methods=['POST'])
def post_index():
    return render_template('landing.html')
# ---------------------------------------------
# register account


@app.route('/register', methods=['GET'])
def get_register():
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def post_register():
    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    hash_password = generate_password_hash(request.form['psw'])
    usernames = conn.execute(text(f"select * from users where username = '{username}'")).all()
    emails = conn.execute(text(f"select email from users where email = '{email}'")).all()
    if len(usernames) > 0:
        duplicate_name = "This username already exists, please pick another one."
        return render_template('login.html', duplicate_name=duplicate_name)
    elif len(emails) > 0:
        duplicate_email = "This email already exists, please pick another one."
        return render_template('login.html', duplicate_email=duplicate_email)
    else:
        conn.execute(text(f"insert into users (username, first_name, last_name, email, password) "
                          f"values('{username}', '{firstname}', '{lastname}', '{email}', '{hash_password}')"))
        conn.execute(text(f"update currentuser set id = (select id from users where username = '{username}'), "
                          f"username = '{username}', type = (select type from users where username = '{username}')"))
        return redirect(url_for('get_main'))
# ---------------------------------------------
# login account


@app.route('/login', methods=['GET'])
def get_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def post_login():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    username = request.form['username']
    password = request.form['psw']
    credentials = conn.execute(text(f"select password from users where username = '{username}' or email = '{username}'")).all()[0][0]
    type = conn.execute(text(f"select type from users where username = '{username}' or email = '{username}'")).all()[0][0]
    if check_password_hash(credentials, password):
        username = conn.execute(text(f"select username from users where username = '{username}' or email = '{username}'")).all()[0][0]
        conn.execute(text(f"update currentuser set id = (select id from users where username = '{username}'), "
                          f"username = '{username}', type = (select type from users where username = '{username}')"))
        if type == 'a':
            return redirect(url_for('get_admin'))
        elif type == 'v':
            return redirect(url_for('get_vendor'))
        else:
            return redirect(url_for('get_main'))
    else:
        incorrect = "Please input a correct password"
        return render_template('login.html', incorrect=incorrect, curr=curr)
# ---------------------------------------------
# logout account


@app.route('/logout', methods=['POST'])
def post_logout():
    conn.execute(text(f"update currentuser set id = null, username = null, type = null"))
    return redirect(url_for('get_login'))
# ---------------------------------------------
# vendor account


@app.route('/vendor', methods=['GET'])
def get_vendor():
    currentuser = conn.execute(text(f"select id from currentuser")).all()[0][0]
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    products = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users on users.id = products.vendor_id where vendor_id = "
             f"{currentuser}")).all()
    return render_template('vendor.html', products=products, curr=curr)


@app.route('/vendor', methods=['POST'])
def post_vendor():
    currentuser = conn.execute(text(f"select id from currentuser")).all()[0][0]
    title = request.form['title']
    description = request.form['description']
    imgurl = request.form['imgurl']
    warranty = request.form['warranty']
    category = request.form['category']
    color = request.form['color']
    numinv = request.form['numinv']
    price = request.form['price']
    conn.execute(text(f"insert into products (vendor_id, title, description, warranty_pd, nOfItems, price, category) "
                      f"values('{currentuser}', '{title}', '{description}', {warranty}, {numinv}, {price}, '{category}')"))
    pid = conn.execute(text(f"select max(pid) from products")).all()[0][0]
    conn.execute(text(f"insert into colors (pid, color) values({pid}, '{color}')"))
    conn.execute(text(f"insert into images (pid, imageURL) values({pid}, '{imgurl}')"))
    conn.execute(text(f"insert into discounts(pid, discount_amt, end_date) values ({pid}, 0, null)"))
    products = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users on users.id = products.vendor_id where vendor_id = "
             f"{currentuser}")).all()
    return redirect(url_for('get_vendor', products=products))
# ---------------------------------------------
# admin account


@app.route('/admin', methods=['GET'])
def get_admin():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    if curr == "admin":
        allproducts = conn.execute(
            text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                 f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                 f"natural join images natural join colors join users where users.id = products.vendor_id")).all()
        return render_template('admin.html', allproducts=allproducts, curr=curr)
    else:
        return redirect(url_for('get_login'))


@app.route('/admin', methods=['POST'])
def post_admin():
    title = request.form['title']
    description = request.form['description']
    imgurl = request.form['imgurl']
    warranty = request.form['warranty']
    category = request.form['category']
    color = request.form['color']
    numinv = request.form['numinv']
    price = request.form['price']
    vendorid = request.form['vendorid']
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    conn.execute(text(f"insert into products (vendor_id, title, description, warranty_pd, nOfItems, price, category) "
                      f"values('{vendorid}', '{title}', '{description}', {warranty}, {numinv}, {price}, '{category}')"))
    pid = conn.execute(text(f"select max(pid) from products")).all()[0][0]
    conn.execute(text(f"insert into colors (pid, color) values({pid}, '{color}')"))
    conn.execute(text(f"insert into images (pid, imageURL) values({pid}, '{imgurl}')"))
    conn.execute(text(f"insert into discounts(pid, discount_amt, end_date) values ({pid}, 0, null)"))
    allproducts = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users where users.id = products.vendor_id")).all()
    return redirect(url_for('get_admin', allproducts=allproducts, curr=curr))
# ---------------------------------------------
# delete account


@app.route('/delete', methods=['GET'])
def get_delete():
    return redirect(url_for('get_admin'))


@app.route('/delete', methods=['POST'])
def post_delete():
    productid = request.form['productid']
    conn.execute(text(f"delete from images where pid = {productid}"))
    conn.execute(text(f"delete from colors where pid = {productid}"))
    conn.execute(text(f"delete from products where pid = {productid}"))
    conn.execute(text(f"delete from discounts where pid = {productid}"))
    return redirect(url_for('get_admin'))
# ---------------------------------------------
# edit account


@app.route('/edit', methods=['GET'])
def get_edit():
    return redirect(url_for('get_admin'))


@app.route('/edit', methods=['POST'])
def post_edit():
    title = request.form['title']
    description = request.form['description']
    imgurl = request.form['imgurl']
    warranty = request.form['warranty']
    category = request.form['category']
    color = request.form['color']
    numinv = request.form['numinv']
    price = request.form['price']
    pid = request.form['pid']
    if title == "":
        result = conn.execute(text(f"select title from products where pid = {pid}")).all()[0][2]
        title = result[0][2]
        title = f"'{title}'"
    else:
        title = f"'{title}'"
    if description == "":
        result = conn.execute(text(f"select * from products where pid = {pid}")).all()
        description = result[0][3]
        description = f"'{description}'"
    else:
        description = f"'{description}'"
    if imgurl == "":
        result = conn.execute(text(f"select * from images where pid = {pid}")).all()
        imgurl = result[0][1]
        imgurl = f"'{imgurl}'"
    else:
        imgurl = f"'{imgurl}'"
    if warranty == "":
        result = conn.execute(text(f"select * from products where pid = {pid}")).all()
        warranty = result[0][4]
        warranty = f"'{warranty}'"
    else:
        warranty = f"'{warranty}'"
    if category == "":
        result = conn.execute(text(f"select * from products where pid = {pid}")).all()
        category = result[0][7]
        category = f"'{category}'"
    else:
        category = f"'{category}'"
    if color == "":
        result = conn.execute(text(f"select * from colors where pid = {pid}")).all()
        color = result[0][1]
        color = f"'{color}'"
    else:
        color = f"'{color}'"
    if numinv == "":
        result = conn.execute(text(f"select * from products where pid = {pid}")).all()
        numinv = result[0][5]
        numinv = f"'{numinv}'"
    else:
        numinv = f"'{numinv}'"
    if price == "":
        result = conn.execute(text(f"select * from products where pid = {pid}")).all()
        price = result[0][6]
        price = f"'{price}'"
    else:
        price = f"'{price}'"
    conn.execute(text(f"update products SET title = {title}, description = {description}, warranty_pd = {warranty}, "
                      f"category = {category}, nOfItems = {numinv}, price = {price} WHERE pid = {pid}"))
    conn.execute(text(f"update colors set color = {color} where pid = {pid}"))
    conn.execute(text(f"update images set imageURL = {imgurl} where pid = {pid}"))
    return redirect(url_for('get_admin'))
# ---------------------------------------------
# search


@app.route('/search', methods=['GET'])
def get_search_name():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currtype = conn.execute(text(f"select type from currentuser")).all()[0][0]
    nsearch = request.args.get('nsearch')
    name = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users on users.id = products.vendor_id where title "
             f"like '%{nsearch}%'")).all()

    if currtype == 'a':
        return render_template('admin.html', name=name, curr=curr)
    elif currtype == 'v':
        return render_template('vendor.html', name=name, curr=curr)
    else:
        return render_template('main.html', name=name, curr=curr)


@app.route('/dsearch', methods=['GET'])
def get_search_admin_desc():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currtype = conn.execute(text(f"select type from currentuser")).all()[0][0]
    name = request.args.get('dsearch')
    name = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users on users.id = products.vendor_id where description "
             f"like '%{name}%'")).all()
    if currtype == 'a':
        return render_template('admin.html', name=name, curr=curr)
    elif currtype == 'v':
        return render_template('vendor.html', name=name, curr=curr)
    else:
        return render_template('main.html', name=name, curr=curr)


@app.route('/vsearch', methods=['GET'])
def get_search_admin_username():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currtype = conn.execute(text(f"select type from currentuser")).all()[0][0]
    name = request.args.get('vsearch')
    name = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users on users.id = products.vendor_id where username "
             f"like '%{name}%'")).all()
    if currtype == 'a':
        return render_template('admin.html', name=name, curr=curr)
    elif currtype == 'v':
        return render_template('vendor.html', name=name, curr=curr)
    else:
        return render_template('main.html', name=name, curr=curr)


@app.route('/search', methods=['POST'])
def post_search_admin():
    return render_template('admin.html')
# ---------------------------------------------
# discount


@app.route('/discount', methods=['GET'])
def get_discount():
    return render_template('admin.html')


@app.route('/discount', methods=['POST'])
def post_discount():
    dpid = request.form['dpid']
    discount = request.form['discount']
    end_date = request.form['end_date']
    allproducts = conn.execute(text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, "
                                    f"price, category, imageURL, color from products natural join images natural "
                                    f"join colors join users where users.id = products.vendor_id")).all()
    if discount != 'none':
        conn.execute(text(f"update discounts set discount_amt = {discount}, end_date = '{end_date}' where pid = {dpid}"))
    return render_template('admin.html', allproducts=allproducts)
# ---------------------------------------------
# status of order


@app.route('/status', methods=['GET'])
def get_status():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currid = conn.execute(text(f"select id from currentuser")).all()[0][0]
    pending_order = conn.execute(
        text(f"select products.pid, users.id, vendor_id, orders.oid, username, title, description, warranty_pd, "
             f"nOfItems, price, category, imageURL, color, discount_amt, (round((((100/discount_amt)*"
             f"(discount_amt/100)) - discount_amt) * 100)) as disc_percent, end_date, orders.date, "
             f"(round(price*discount_amt)) as disc_price, listOfItems.price_paid, status from products natural join "
             f"discounts natural join images natural join colors join listOfItems using(pid) join orders using (oid) "
             f"join users using (id) where vendor_id = {currid} and status = 'pending'")).all()
    confirmed_orders = conn.execute(
        text(f"select products.pid, users.id, vendor_id, orders.oid, username, title, description, warranty_pd, "
             f"nOfItems, price, category, imageURL, color, discount_amt, (round((((100/discount_amt)*"
             f"(discount_amt/100)) - discount_amt) * 100)) as disc_percent, end_date, orders.date, "
             f"(round(price*discount_amt)) as disc_price, listOfItems.price_paid, status from products natural join "
             f"discounts natural join images natural join colors join listOfItems using(pid) join orders using (oid) "
             f"join users using (id) where vendor_id = {currid} and status <> 'pending'")).all()
    return render_template('receivedOrders.html', pending_order=pending_order, confirmed_orders=confirmed_orders, curr=curr)


@app.route('/status', methods=['POST'])
def post_status():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currid = conn.execute(text(f"select id from currentuser")).all()[0][0]
    changestatus = request.form['changestatus']
    oid = request.form['oid']
    pending_order = conn.execute(
        text(f"select products.pid, users.id, vendor_id, orders.oid, username, title, description, warranty_pd, "
             f"nOfItems, price, category, imageURL, color, discount_amt, (round((((100/discount_amt)*"
             f"(discount_amt/100)) - discount_amt) * 100)) as disc_percent, end_date, orders.date, "
             f"(round(price*discount_amt)) as disc_price, listOfItems.price_paid, status from products natural join "
             f"discounts natural join images natural join colors join listOfItems using(pid) join orders using (oid) "
             f"join users using (id) where vendor_id = {currid} and status = 'pending'")).all()
    conn.execute(text(f"update orders set status = '{changestatus}' where oid = {oid}"))
    return render_template('receivedOrders.html', pending_order=pending_order, curr=curr)
# -------------------------------------------
# customer/main account


@app.route('/main', methods=['GET'])
def get_main():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    currid = conn.execute(text(f"select id from currentuser")).all()[0][0]
    nsearch = request.args.get('nsearch')
    complaint = conn.execute(text(f"select * from complaints where username = '{curr}'")).all()
    name = conn.execute(
        text(f"select username, vendor_id, products.pid, title, description, warranty_pd, nOfItems, "
                             f"price, category, color, imageURL from users inner join products natural join colors "
                             f"natural join images on users.id = products.vendor_id where title like "
                             f"'%{nsearch}%'")).all()
    cart = conn.execute(
        text(f"select pid, cart_id, title, price, discount_amt, (price*discount_amt) as disc_price, item_num from products "
             f"natural join discounts natural join cart where cart_id = {currid}")).all()
    allproducts = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users where users.id = products.vendor_id")).all()
    return render_template('main.html', allproducts=allproducts, curr=curr, name=name, cart=cart, complaint=complaint)


@app.route('/main', methods=['POST'])
def post_main():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    allproducts = conn.execute(
        text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
             f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
             f"natural join images natural join colors join users where users.id = products.vendor_id")).all()
    return render_template('main.html', allproducts=allproducts, curr=curr)
# ---------------------------------------------
# filter


@app.route('/filter', methods=['GET'])
def get_filter():
    return render_template('main.html')


@app.route('/filter', methods=['POST'])
def post_filter():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    catfilter = request.form['catfilter']
    colorfilter = request.form['colorfilter']
    availfilter = request.form['availfilter']
    if catfilter != "none" and colorfilter == "none" and availfilter == "none":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}'")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter != "none" and colorfilter != "none" and availfilter == "none":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}' and color = '{colorfilter}'")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter != "none" and colorfilter == "none" and availfilter == "inStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}' and nOfItems > 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter != "none" and colorfilter == "none" and availfilter == "outStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}' and nOfItems = 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter != "none" and colorfilter != "none" and availfilter == "inStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}' and color = '{colorfilter}' and nOfItems > 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter != "none" and colorfilter != "none" and availfilter == "outStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where category = "
                f"'{catfilter}' and color = '{colorfilter}' and nOfItems = 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter == "none" and colorfilter != "none" and availfilter == "none":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where color = "
                f"'{colorfilter}'")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter == "none" and colorfilter != "none" and availfilter == "inStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where color = "
                f"'{colorfilter}' and nOfItems > 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter == "none" and colorfilter != "none" and availfilter == "outStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where color = "
                f"'{colorfilter}' and nOfItems = 0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter == "none" and colorfilter == "none" and availfilter == "inStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where nOfItems > "
                f"0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    elif catfilter == "none" and colorfilter == "none" and availfilter == "outStock":
        filter = conn.execute(
            text(
                f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, price, category, imageURL, "
                f"color, discount_amt, end_date, (price*discount_amt) as disc_price from products natural join discounts "
                f"natural join images natural join colors join users on users.id = products.vendor_id where nOfItems = "
                f"0")).all()
        return render_template('main.html', filter=filter, curr=curr)
    else:
        return redirect(url_for('post_main'))
# ---------------------------------------------
# cart


@app.route('/cart', methods=['POST'])
def post_cart():
    cpid = request.form['cpid']
    curr = conn.execute(text(f"select id from currentuser")).all()[0][0]
    conn.execute(text(f"insert into cart (cart_id, pid) values ({curr}, {cpid})"))
    cart = conn.execute(
        text(f"select pid, cart_id, title, price, discount_amt, (price*discount_amt) as disc_price, item_num from "
             f"products natural join discounts natural join cart where cart_id = {curr}")).all()
    return redirect(url_for('get_main', cart=cart, curr=curr))
# ---------------------------------------------
# remove item from cart


@app.route('/removecart', methods=['POST'])
def post_removecart():
    item_num = request.form['removecart']
    conn.execute(text(f"delete from cart where item_num = {item_num}"))
    return redirect(url_for('get_main'))


# ---------------------------------------------
# checkout


@app.route('/checkout', methods=['POST'])
def post_checkout():
    curr = conn.execute(text(f"select id from currentuser")).all()[0][0]
    orders = conn.execute(
        text(
            f"select products.pid, cart_id, title, price, discount_amt, (round(price*discount_amt)) as disc_price "
            f"from products natural join discounts inner join cart on cart.pid = products.pid where cart_id = {curr}")).all()
    conn.execute(text(f"insert into orders(id) values({curr})"))
    for i in orders:
        pid = i[0]
        cart_id = i[1]
        title = i[2]
        price = i[3]
        discount_amt = i[4]
        disc_price = i[5]
        price_paid = 0
        if disc_price == 0:
            price_paid = price
        elif disc_price > 0:
            price_paid = disc_price
        oid = conn.execute(text(f"select max(oid) from orders")).all()[0][0]
        conn.execute(text(f"insert into listOfItems(oid, pid, price_paid) values({oid}, {pid}, {price_paid})"))
        conn.execute(text(f"update products set nOfItems = nOfItems - 1 where pid = {pid}"))
        conn.execute(text(f"delete from cart where cart_id = {cart_id}"))
    return redirect(url_for('get_placedOrder'))
# ---------------------------------------------
# placed order page


@app.route('/placedOrder', methods=['GET'])
def get_placedOrder():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    cart_id = conn.execute(text(f"select id from currentuser")).all()[0][0]
    placed_order = conn.execute(
        text(
            f"select products.pid, users.id, vendor_id, orders.oid, username, title, description, warranty_pd, "
            f"nOfItems, price, category, imageURL, color, discount_amt, end_date, orders.date, "
            f"(round(price*discount_amt)) as disc_price, listOfItems.price_paid from products natural join discounts "
            f"natural join images natural join colors join listOfItems using(pid) join orders using (oid) join users "
            f"using (id) where id = {cart_id} order by oid desc")).all()
    for p in placed_order:
        title = p.title
        car_review = conn.execute(
            text(f"select description, rating, title from reviews where id = {cart_id}")).all()
        return render_template('placedOrder.html', placed_order=placed_order, curr=curr, car_review=car_review)


@app.route('/placedOrder', methods=['POST'])
def post_placedOrder():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    cart_id = conn.execute(text(f"select id from currentuser")).all()[0][0]
    title = request.form['title']
    placed_order = conn.execute(
        text(
            f"select products.pid, users.id, vendor_id, orders.oid, username, title, description, warranty_pd, "
            f"nOfItems, price, category, imageURL, color, discount_amt, end_date, orders.date, "
            f"(round(price*discount_amt)) as disc_price, listOfItems.price_paid from products natural join discounts "
            f"natural join images natural join colors join listOfItems using(pid) join orders using (oid) join users "
            f"using (id) where id = {cart_id} order by oid desc")).all()
    return render_template('placedOrder.html', placed_order=placed_order, curr=curr)
# ---------------------------------------------
# reviews


@app.route('/review', methods=['POST'])
def post_review():
    currid = conn.execute(text(f"select id from currentuser")).all()[0][0]
    rating = request.form['rating']
    reviewtext = request.form['reviewtext']
    title = request.form['title']
    conn.execute(text(f"insert into reviews (id, title, rating, description) values ({currid}, '{title}', {rating}, '{reviewtext}')"))
    return redirect(url_for('get_placedOrder'))


@app.route('/reviewpage', methods=['GET'])
def get_reviewpage():
    allreviews = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id")).all()
    return render_template('reviewpage.html', allreviews=allreviews)


@app.route('/reviewpage', methods=['POST'])
def post_reviewpage():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    ratingreview = request.form['ratingreview']
    timereview = request.form['timereview']
    if timereview == 'none' and ratingreview == 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    elif timereview == "old" and ratingreview == 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id order by date asc")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    elif timereview == "new" and ratingreview == 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id order by date desc")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    elif timereview == "old" and ratingreview != 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id where "
                                         f"rating = {ratingreview} order by date desc")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    elif timereview == "new" and ratingreview != 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id where "
                                         f"rating = {ratingreview} order by date asc")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    elif timereview == "none" and ratingreview != 'none':
        reviewfilter = conn.execute(text(f"select * from users inner join reviews on users.id = reviews.id where "
                                         f"rating = {ratingreview}")).all()
        return render_template('reviewpage.html', reviewfilter=reviewfilter, curr=curr)
    else:
        return redirect(url_for('get_reviewpage'))
# ---------------------------------------------
# returns/complaints


@app.route('/returns', methods=['GET'])
def get_returns():
    return render_template('returns.html')


@app.route('/returns', methods=['POST'])
def post_returns():
    title = request.form['return_title']
    return_desc = request.form['return_desc']
    return_demand = request.form['return_demand']
    username = request.form['username']
    usernames = conn.execute(text(f"select * from users where username = '{username}'")).all()
    titles = conn.execute(text(f"select * from products where title = '{title}'")).all()
    bought = conn.execute(text(f"select users.id, username, orders.oid, title from users join orders on users.id = "
                               f"orders.id join listOfItems on orders.oid = listOfItems.oid join products on "
                               f"listOfItems.pid = products.pid where username = '{username}' and title = '{title}'")).all()
    if len(usernames) == 0:
        notuser = "You must be a previous customer to file a complaint. This username does not exist."
        return render_template('returns.html', notuser=notuser)
    elif len(titles) == 0:
        notours = "This is not one of our products."
        return render_template('returns.html', notours=notours)
    elif len(bought) == 0:
        notyours = "You can only return products that you have purchased."
        return render_template('returns.html', notyours=notyours)
    else:
        conn.execute(
            text(f"insert into complaints (username, title, description, demand) values ('{username}', '{title}', "
                 f"'{return_desc}', '{return_demand}')"))
        thanks = "Thank you for your feedback."
        return render_template('returns.html', thanks=thanks)
# ---------------------------------------------
# returns/complaints


@app.route('/returnrequests', methods=['GET'])
def get_returnrequests():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    requests = conn.execute(text(f"select * from complaints where status = 'pending'")).all()
    return render_template('returnrequests.html', requests=requests, curr=curr)


@app.route('/returnrequests', methods=['POST'])
def post_returnrequests():
    requests = conn.execute(text(f"select * from complaints where status = 'pending'")).all()
    change_req_status = request.form['change_req_status']
    cid = request.form['cid']
    conn.execute(text(f"update complaints set status = '{change_req_status}' where cid = {cid}"))
    return redirect(url_for('get_returnrequests', requests=requests))
# ---------------------------------------------
# message/chats


@app.route('/chat', methods=['GET'])
def get_chat():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    vendors = conn.execute(text(f"select * from users where type = 'v'")).all()
    bought = conn.execute(text(f"select users.id, username, orders.oid, title from users join orders on users.id = "
                               f"orders.id join listOfItems on orders.oid = listOfItems.oid join products on "
                               f"listOfItems.pid = products.pid where username = '{curr}'")).all()
    return render_template('chat.html', curr=curr, vendors=vendors, bought=bought)


@app.route('/chat', methods=['POST'])
def post_chat():
    vendors = conn.execute(text(f"select * from users where type = 'v'")).all()
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    bought = conn.execute(text(f"select users.id, username, orders.oid, title from users join orders on users.id = "
                               f"orders.id join listOfItems on orders.oid = listOfItems.oid join products on "
                               f"listOfItems.pid = products.pid where username = '{curr}'")).all()
    demand = request.form['chat_demand']
    message = request.form['message']
    user_to = request.form['vid']
    title = request.form['tid']
    vendor_id = conn.execute(
        text(f"select pid, vendor_id, username, title from products join users on products.vendor_id = users.id where "
             f"username = '{user_to}' and title = '{title}'")).all()
    if len(vendor_id) == 0:
        notright = "This product is not sold by this vendor."
        return render_template('chat.html', notright=notright, bought=bought, vendors=vendors)
    else:
        conn.execute(text(f"insert into messages (title, demand) values ('{title}', '{demand}')"))
        mid = conn.execute(text(f"select max(mid) from messages")).all()[0][0]
        conn.execute(text(f"insert into messages_chats (mid, user_from, user_to, text) values ({mid}, '{curr}', '{user_to}',"
                          f" '{message}')"))
        return redirect(url_for('get_chatroom'))
# ---------------------------------------------
# chatroom


@app.route('/chatroom', methods=['GET'])
def get_chatroom():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    mid = conn.execute(text(f"select max(mid) from messages_chats")).all()[0][0]
    user_to = conn.execute(text(f"select max(user_to) from messages_chats")).all()[0][0]
    startchat = conn.execute(text(f"select * from messages_chats where mid = {mid} and user_to = '{user_to}' order by date"))
    return render_template('chatroom.html', curr=curr, startchat=startchat)


@app.route('/chatroom', methods=['POST'])
def post_chatroom():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    mid = conn.execute(text(f"select max(mid) from messages_chats")).all()[0][0]
    user_to = conn.execute(text(f"select max(user_to) from messages_chats")).all()[0][0]
    message = request.form['message']
    conn.execute(
        text(f"insert into messages_chats (mid, user_from, user_to, text) values ({mid}, '{curr}', '{user_to}',"
             f" '{message}')"))
    startchat = conn.execute(
        text(f"select * from messages_chats where mid = {mid} and user_to = '{user_to}' order by date"))
    return render_template('chatroom.html', curr=curr, startchat=startchat)
# ---------------------------------------------
# all chatrooms


@app.route('/alluserchats', methods=['GET'])
def get_alluserchats():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    allchats = conn.execute(text(f"select * from messages natural join messages_chats where user_from = '{curr}' or "
                                 f"user_to = '{curr}'")).all()
    mid = request.args.get('mid')
    allchatspost = conn.execute(text(f"select * from messages_chats where mid = {mid} order by date")).all()
    print('test test test test', allchats, file=sys.stderr)
    print('test test test test', allchatspost, file=sys.stderr)
    print('test test test test', mid, file=sys.stderr)
    return render_template('alluserchats.html', curr=curr, allchats=allchats, allchatspost=allchatspost)


@app.route('/alluserchats', methods=['POST'])
def post_alluserchats():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    allchats = conn.execute(
        text(f"select * from messages natural join messages_chats where user_from = '{curr}' or "
             f"user_to = '{curr}'")).all()
    mid = request.form['mid']
    message = request.form['message']
    user_to = request.form['user_to']
    conn.execute(
        text(f"insert into messages_chats (mid, user_from, user_to, text) values ({mid}, '{curr}', '{user_to}',"
             f" '{message}')"))
    allchatspost = conn.execute(text(f"select * from messages_chats where mid = {mid} order by date")).all()
    return render_template('alluserchats.html', curr=curr, allchatspost=allchatspost, allchats=allchats)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
