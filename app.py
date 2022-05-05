import os
import sys

from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from os import environ
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
print('This is error output', file=sys.stderr)


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
        return redirect(url_for('/main'))
# ---------------------------------------------
# login account


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
    return redirect(url_for('get_register'))
# ---------------------------------------------
# vendor account


@app.route('/vendor', methods=['GET'])
def get_vendor():
    currentuser = conn.execute(text(f"select id from currentuser")).all()[0][0]
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    products = conn.execute(text(f"select * from products natural join colors natural join images where vendor_id = {currentuser}")).all()
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
    products = conn.execute(text(f"select * from products natural join colors natural join images where vendor_id = {currentuser}")).all()
    return redirect(url_for('get_vendor', products=products))
# ---------------------------------------------
# admin account


@app.route('/admin', methods=['GET'])
def get_admin():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    allproducts = conn.execute(text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, "
                                    f"price, category, imageURL, color from products natural join images natural "
                                    f"join colors join users where users.id = products.vendor_id")).all()
    return render_template('admin.html', allproducts=allproducts, curr=curr)


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
    allproducts = conn.execute(text(f"select pid, vendor_id, username, title, description, warranty_pd, nOfItems, "
                                    f"price, category, imageURL, color from products natural join images natural "
                                    f"join colors join users where users.id = products.vendor_id")).all()
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
    name = conn.execute(text(f"select username, vendor_id, products.pid, title, description, warranty_pd, nOfItems, price,"
                      f" category, color, imageURL from users inner join products natural join colors natural join"
                      f" images on users.id = products.vendor_id where title like '%{nsearch}%'")).all()
    print(name, file=sys.stderr)
    print('This is error output2', file=sys.stderr)
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
    name = conn.execute(text(f"select username, vendor_id, products.pid, title, description, warranty_pd, nOfItems, price,"
                          f" category, color, imageURL from users inner join products natural join colors natural join"
                          f" images on users.id = products.vendor_id where description like '%{name}%'")).all()
    print(name, file=sys.stderr)
    print('This is error output3', file=sys.stderr)
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
    name = conn.execute(text(f"select username, vendor_id, products.pid, title, description, warranty_pd, nOfItems, price,"
                          f" category, color, imageURL from users inner join products natural join colors natural join"
                          f" images on users.id = products.vendor_id where username like '%{name}%'")).all()
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
# customer/main account


@app.route('/main', methods=['GET'])
def get_main():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    nsearch = request.args.get('nsearch')
    name = conn.execute(text(f"select username, vendor_id, products.pid, title, description, warranty_pd, nOfItems, price,"
             f" category, color, imageURL from users inner join products natural join colors natural join"
             f" images on users.id = products.vendor_id where title like '%{nsearch}%'")).all()
    allproducts = conn.execute(text(f"select * from products natural join images")).all()
    return render_template('main.html', allproducts=allproducts, curr=curr, name=name)


@app.route('/main', methods=['POST'])
def post_main():
    curr = conn.execute(text(f"select username from currentuser")).all()[0][0]
    allproducts = conn.execute(text(f"select * from products natural join images")).all()
    return render_template('main.html', allproducts=allproducts, curr=curr)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')