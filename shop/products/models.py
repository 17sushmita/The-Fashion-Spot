from shop import db
from datetime import datetime


class Addproduct(db.Model):
    __seachbale__ = ['name','desc']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)
    discount = db.Column(db.Integer, default=0)
    stock = db.Column(db.Integer, nullable=False)
    colors = db.Column(db.Text, nullable=False)
    desc = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,default=datetime.now)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),nullable=False)
    category = db.relationship('Category',backref=db.backref('categories', lazy=True))

    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'))
    subcategory = db.relationship('Subcategories',backref=db.backref('subcategory', lazy=True))

    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'),nullable=False)
    brand = db.relationship('Brand',backref=db.backref('brands', lazy=True))

    image_1 = db.Column(db.String(150), nullable=False, default='image1.jpg')
    image_2 = db.Column(db.String(150), nullable=False, default='image2.jpg')
    image_3 = db.Column(db.String(150), nullable=False, default='image3.jpg')

    def __repr__(self):
        return '<Post %r>' % self.name


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return '<Brand %r>' % self.name
    

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return '<Catgory %r>' % self.name

class Specs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),nullable=False)
    category = db.relationship('Category',backref=db.backref('cat', lazy=True))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'))
    subcategory = db.relationship('Subcategories',backref=db.backref('subcat', lazy=True))
    name = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return '<Specs %r>' % self.name

class Specsvalues(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id=db.Column(db.Integer,nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('addproduct.id'),nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'))
    spec_id = db.Column(db.Integer, db.ForeignKey('specs.id'),nullable=False)
    specs = db.relationship('Specs',backref=db.backref('specs', lazy=True))
    value = db.Column(db.String(80), unique=False, nullable=False)
    db.UniqueConstraint('product_id','spec_id',name='prod_spec')

    def __repr__(self):
        return '<Specs %r>' % self.value



class Events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp=db.Column(db.DateTime, default=datetime.now, nullable=False)
    #customer_id=db.Column(db.Integer)
    customer_id = db.Column(db.Integer)
    #customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'),nullable=False)
    #customers = db.relationship('Customers',backref=db.backref('users', lazy=True))

    event = db.Column(db.String(50), unique= False)
    product_id=db.Column(db.Integer,nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('addproduct.id'),nullable=False)
    addproduct = db.relationship('Addproduct',backref=db.backref('products', lazy=True))

    transaction_id=db.Column(db.String(20), unique=False)
    

    def __repr__(self):
        return '<Event %r>' % self.id

class Subcategories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),nullable=False)
    category = db.relationship('Category',backref=db.backref('categ', lazy=True))
    name = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return '<Subcategory %r>' % self.name
   




db.create_all()