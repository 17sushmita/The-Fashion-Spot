from flask import render_template,session, request,redirect,url_for,flash
from shop import app,db,bcrypt
from .forms import RegistrationForm,LoginForm
from .models import Admin
from shop.products.models import Addproduct,Category,Brand,Specs,Subcategories
from functools import wraps


'''
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect(url_for('index'))
        else:
            return f(*args, *kwargs)

    return wrap

'''
def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


def not_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return redirect(url_for('admin'))
        else:
            return f(*args, *kwargs)

    return wrap


def wrappers(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped




@app.route('/admin_out')
def admin_logout():
    if 'admin_logged_in' in session:
        session.clear()
        return redirect(url_for('login'))
    return redirect(url_for('admin'))




@app.route('/admin')
@is_admin_logged_in
def admin():
    products = Addproduct.query.all()
    return render_template('admin/index.html', title='Admin page',products=products,Subcategories=Subcategories)

@app.route('/brands')
@is_admin_logged_in
def brands():
    brands = Brand.query.order_by(Brand.id.desc()).all()
    return render_template('admin/brand.html', title='brands',brands=brands)


@app.route('/categories')
@is_admin_logged_in
def categories():
    categories = Category.query.order_by(Category.id.desc()).all()
    return render_template('admin/brand.html', title='categories',cat='category',categories=categories)

@app.route('/specs')
def specs():
    print('hhkuh')
    categories = Category.query.order_by(Category.id.desc()).all()

    if request.method=='GET':
        getcat=request.args.get('category')
        specs = Specs.query.filter_by(category_id=getcat).all()
        print(specs)
        return render_template('admin/brand.html', title='Specifications',categories= categories,specifications=specs,getcat=getcat,spec='spec')

    return render_template('admin/brand.html', title='Specifications',categories=categories)
@app.route('/sub')
def sub():
    print('sub')
    categories = Category.query.order_by(Category.id.desc()).all()

    if request.method=='GET':
        getcat=request.args.get('category')
        sub = Subcategories.query.filter_by(category_id=getcat).all()
        return render_template('admin/brand.html', title='Subcategories',categories= categories,subcategories=sub,getcat=getcat)

    return render_template('admin/brand.html', title='Subcategories',categories=categories)


@app.route('/register', methods=['GET', 'POST'])
@not_admin_logged_in
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = Admin(name=form.name.data,username=form.username.data, email=form.email.data,
                    password=hash_password)
        db.session.add(user)
        flash(f'welcome {form.name.data} Thanks for registering','success')
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('admin/register.html',title='Register user', form=form)


@app.route('/login', methods=['GET','POST'])
@not_admin_logged_in
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['email'] = form.email.data
            session['admin_logged_in'] = True
            session['admin_uid'] = user.id
            session['admin_name'] = user.name

            flash(f'welcome {form.email.data} you are logedin now','success')
            return redirect(url_for('admin'))
        else:
            flash(f'Wrong email and password', 'success')
            return redirect(url_for('login'))
    return render_template('admin/login.html',title='Login page',form=form)