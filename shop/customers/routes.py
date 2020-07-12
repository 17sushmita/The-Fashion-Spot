from flask import render_template,session, request,redirect,url_for,flash,current_app,make_response
from flask_login import login_required, current_user, logout_user, login_user
from shop import app,db,photos, search,bcrypt,login_manager
from .forms import CustomerRegisterForm, CustomerLoginFrom
from .model import Customers,Orders
from shop.products.models import Subcategories
import secrets
import os
import json
import pdfkit
import stripe
from functools import wraps
from shop.products.models import Events

buplishable_key ='pk_test_51H1HnsIq06WWfErE51PplNlOzHcmVp3p6C1yzf6XqWnSDfpQsFoGsRHqWUYKTN0mMVrtgLhRFzKvZgAHVvtwKpXs00HAN0djIl'
stripe.api_key ='sk_test_51H1HnsIq06WWfErEdca5ggnTGUhUghGXvx5V8P9e2hAUlLJhZwSgyld4cNH6BgAfSUki5BKvLNneIgGW6G9D2rF000pMW0H14O'

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('customer/login'))

    return wrap


def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect(url_for('home'))
        else:
            return f(*args, *kwargs)

    return wrap







@app.route('/payment',methods=['POST'])
@is_logged_in
def payment():
    invoice = request.form.get('invoice')
    amount = request.form.get('amount')

    customer = stripe.Customer.create(
      email=request.form['stripeEmail'],
      source=request.form['stripeToken'],
    )
    charge = stripe.Charge.create(
      customer=customer.id,
      description='The Fashion Spot',
      amount=amount,
      currency='inr',
    )
    orders =  Orders.query.filter_by(customer_id = current_user.id,invoice=invoice).order_by(Orders.id.desc()).first()
    orders.status = 'Paid'
    for product_id in orders.orders.keys():
        event=Events(customer_id=current_user.id,event='transaction',product_id=product_id,transaction_id=invoice)
        #print('transaction : ',product,session['uid'],session['s_name'])
        db.session.add(event)
    db.session.commit()
    return redirect(url_for('thanks'))

@app.route('/thanks')
def thanks():
    return render_template('customer/thank.html')


@app.route('/customer/register', methods=['GET','POST'])
@not_logged_in
def customer_register():
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        register = Customers(name=form.name.data, username=form.username.data, email=form.email.data,password=hash_password,country=form.country.data, city=form.city.data,contact=form.contact.data, address=form.address.data, zipcode=form.zipcode.data)
        db.session.add(register)
        flash(f'Welcome {form.name.data} Thank you for registering', 'success')
        db.session.commit()
        return redirect(url_for('customerLogin'))
    return render_template('customer/register.html', form=form)


@app.route('/customer/login', methods=['GET','POST'])
@not_logged_in
def customerLogin():
    form = CustomerLoginFrom()
    if form.validate_on_submit():
        user = Customers.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session['logged_in'] = True
            session['uid'] = user.id
            session['s_name'] = user.name
            flash('You are login now!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        flash('Incorrect email and password','danger')
        return redirect(url_for('customerLogin'))
            
    return render_template('customer/login.html', form=form)


@app.route('/customer/logout')
def customer_logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))

def updateshoppingcart():
    for key, shopping in session['Shoppingcart'].items():
        session.modified = True
        del shopping['image']
        del shopping['colors']
    return updateshoppingcart

@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        updateshoppingcart
        try:
            order = Orders(invoice=invoice,customer_id=customer_id,orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been sent successfully','success')
            return redirect(url_for('orders',invoice=invoice))
        except Exception as e:
            print(e)
            flash('Some thing went wrong while get order', 'danger')
            return redirect(url_for('getCart'))
        


@app.route('/orders/<invoice>')
@login_required
def orders(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Customers.query.filter_by(id=customer_id).first()
        orders = Orders.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(Orders.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount']/100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f" % (1.06 * float(subTotal)))

    else:
        return redirect(url_for('customerLogin'))
    return render_template('customer/order.html', invoice=invoice, tax=tax,subTotal=subTotal,grandTotal=grandTotal,customer=customer,orders=orders,Subcategories=Subcategories)




@app.route('/get_pdf/<invoice>', methods=['POST'])
@login_required
def get_pdf(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        if request.method =="POST":
            customer = Customers.query.filter_by(id=customer_id).first()
            orders = Orders.query.filter_by(customer_id=customer_id, invoice=invoice).order_by(Orders.id.desc()).first()
            for _key, product in orders.orders.items():
                discount = (product['discount']/100) * float(product['price'])
                subTotal += float(product['price']) * int(product['quantity'])
                subTotal -= discount
                tax = ("%.2f" % (.06 * float(subTotal)))
                grandTotal = float("%.2f" % (1.06 * subTotal))

            rendered =  render_template('customer/pdf.html', invoice=invoice, tax=tax,grandTotal=grandTotal,customer=customer,orders=orders)
            pdf = pdfkit.from_string(rendered, False)
            response = make_response(pdf)
            response.headers['content-Type'] ='application/pdf'
            response.headers['content-Disposition'] ='inline; filename='+invoice+'.pdf'
            return response
    return request(url_for('orders'))



