from flask import render_template,session, request,redirect,url_for,flash,current_app,jsonify
from shop import app,db,photos, search
from .models import Category,Brand,Addproduct,Events,Specs,Specsvalues,Subcategories
from .forms import Addproducts
import secrets
import os
from .recommender import content_based_filtering,Hot_Sellers,Top_Brands,Top_Categories,most_viewed,recommended_items_by_itemviewed,search_query

def brands():
    brands = Brand.query.join(Addproduct, (Brand.id == Addproduct.brand_id)).all()
    return brands

def categories():
    categories = Category.query.join(Addproduct,(Category.id == Addproduct.category_id)).all()
    return categories

@app.route('/')
def home():
    hot_sellers=Hot_Sellers()
    hot_brands=Top_Brands()
    hot_categories=Top_Categories()
    top_products=[]
    top_brands=[]
    top_categories=[]
    
    if 'logged_in' in session and len(most_viewed(session['uid'])[0])>0:
        recommended_items=[]
        for i in recommended_items_by_itemviewed(most_viewed(session['uid'])[0]):
            recommended_items.append(Addproduct.query.get_or_404(i))
    else:
        recommended_items=None

    for i in hot_sellers:
        top_products.append(Addproduct.query.get_or_404(i))
    for i in hot_brands:
        top_brands.append(Brand.query.get_or_404(i))
    for i in hot_categories:
        top_categories.append(Subcategories.query.get_or_404(i))
    lengths=(len(top_products),len(top_categories),len(top_brands))
    return render_template('products/home.html',brands=brands(),categories=categories(),Subcategories=Subcategories,Category=Category,top_products=top_products,top_brands=top_brands,top_categories=top_categories,lengths=lengths,recommended_items=recommended_items)

@app.route('/products')
def products():
    page = request.args.get('page',1, type=int)
    products = Addproduct.query.filter(Addproduct.stock > 0).order_by(Addproduct.id.desc()).paginate(page=page, per_page=8)
    return render_template('products/index.html', products=products,brands=brands(),categories=categories(),Subcategories=Subcategories)

@app.route('/result')
def result():
    searchword = request.args.get('q')
    products_id=search_query(searchword)
    rec=[]
    for p in products_id:
        rec.append(Addproduct.query.get_or_404(int(p)))
    #products = Addproduct.query.msearch(searchword, fields=['name','desc'] , limit=6)
    return render_template('products/result.html',products=rec,brands=brands(),categories=categories(),Subcategories=Subcategories,searchword=searchword)

@app.route('/product/<int:id>')
def single_page(id):
    product = Addproduct.query.get_or_404(id)
    spec_values=Specsvalues.query.filter_by(product_id=id).all()
    specs=[]
    for s in spec_values:
        spec=Specs.query.get_or_404(s.spec_id).name
        specs.append(spec)
    recommendations=content_based_filtering(id).index
    rec=[]
    for p in recommendations:
        if p!=id:
            rec.append(Addproduct.query.get_or_404(p))
        
    
    if 'logged_in' in session:
        event=Events(customer_id=session['uid'],event='view',product_id=product.id)
        db.session.add(event)
        db.session.commit()
    return render_template('products/single_page.html',product=product,brands=brands(),categories=categories(),specs=specs,Subcategories=Subcategories,x=rec)




@app.route('/brand/<int:id>')
def get_brand(id):
    page = request.args.get('page',1, type=int)
    get_brand = Brand.query.filter_by(id=id).first_or_404()
    brand = Addproduct.query.filter_by(brand=get_brand).paginate(page=page, per_page=8)
    return render_template('products/index.html',brand=brand,brands=brands(),categories=categories(),get_brand=get_brand,Subcategories=Subcategories)


@app.route('/categories/<int:id>')
def get_category(id):
    page = request.args.get('page',1, type=int)
    get_cat = Category.query.filter_by(id=id).first_or_404()
    get_cat_prod = Addproduct.query.filter_by(category=get_cat).paginate(page=page, per_page=8)
    return render_template('products/index.html',get_cat_prod=get_cat_prod,brands=brands(),categories=categories(),get_cat=get_cat,Subcategories=Subcategories)

@app.route('/subcategories/<int:id>')
def get_subcategory(id):
    page = request.args.get('page',1, type=int)
    get_sub = Subcategories.query.filter_by(id=id).first_or_404()
    get_sub_prod = Addproduct.query.filter_by(subcategory_id=get_sub.id).paginate(page=page, per_page=8)
    return render_template('products/index.html',get_sub_prod=get_sub_prod,brands=brands(),categories=categories(),get_sub=get_sub,Subcategories=Subcategories)


@app.route('/addbrand',methods=['GET','POST'])
def addbrand():
    if request.method =="POST":
        getbrand = request.form.get('brand')
        brand = Brand(name=getbrand)
        db.session.add(brand)
        flash(f'The brand {getbrand} was added to your database','success')
        db.session.commit()
        return redirect(url_for('addbrand'))
    return render_template('products/addbrand.html', title='Add brand',brands='brands')

@app.route('/updatebrand/<int:id>',methods=['GET','POST'])
def updatebrand(id):
    if 'email' not in session:
        flash('Login first please','danger')
        return redirect(url_for('login'))
    updatebrand = Brand.query.get_or_404(id)
    brand = request.form.get('brand')
    if request.method =="POST":
        updatebrand.name = brand
        flash(f'The brand {updatebrand.name} was changed to {brand}','success')
        db.session.commit()
        return redirect(url_for('brands'))
    brand = updatebrand.name
    return render_template('products/addbrand.html', title='Udate brand',brands='brands',updatebrand=updatebrand)


@app.route('/deletebrand/<int:id>', methods=['GET','POST'])
def deletebrand(id):
    brand = Brand.query.get_or_404(id)
    addproducts = Addproduct.query.filter_by(brand_id=id).all()

    if request.method=="POST":
        for p in addproducts:
            events=Events.query.filter_by(product_id=p.id).all()
            for e in events:
                db.session.delete(e)
            spec_values=Specsvalues.query.filter_by(product_id=p.id).all()
            for sp in spec_values:
                db.session.delete(sp)
            db.session.commit()
            db.session.delete(p)
        db.session.commit()
        db.session.delete(brand)
        flash(f"The brand {brand.name} was deleted from your database","success")
        db.session.commit()
        return redirect(url_for('brands'))
    flash(f"The brand {brand.name} can't be  deleted from your database","warning")
    return redirect(url_for('brands'))

@app.route('/addcat',methods=['GET','POST'])
def addcat():
    if request.method =="POST":
        getcat = request.form.get('category')
        category = Category(name=getcat)
        db.session.add(category)
        flash(f'The Category {getcat} was added to your database','success')
        db.session.commit()
        return redirect(url_for('addcat'))
    return render_template('products/addbrand.html', title='Add category', cat='categories')


@app.route('/updatecat/<int:id>',methods=['GET','POST'])
def updatecat(id):
    if 'email' not in session:
        flash('Login first please','danger')
        return redirect(url_for('login'))
    updatecat = Category.query.get_or_404(id)
    category = request.form.get('category')  
    if request.method =="POST":
        updatecat.name = category
        flash(f'The category {updatecat.name} was changed to {category}','success')
        db.session.commit()
        return redirect(url_for('categories'))
    category = updatecat.name
    return render_template('products/addbrand.html', title='Update cat',updatecat=updatecat,cat='categories')



@app.route('/deletecat/<int:id>', methods=['GET','POST'])
def deletecat(id):
    category = Category.query.get_or_404(id)
    addproducts = Addproduct.query.filter_by(category_id=id).all()
    

    if request.method=="POST":
        for p in addproducts:
            events=Events.query.filter_by(product_id=p.id).all()
            for e in events:
                db.session.delete(e)
        specs=Specs.query.filter_by(category_id=id).all()
        for s in specs:
            spec_values=Specsvalues.query.filter_by(spec_id=s.id).all()
            for sp in spec_values:
                db.session.delete(sp)
            db.session.delete(s)
            sub=Subcategories.query.filter_by(category_id=id).all()
            for s in sub:
                db.session.delete(s)

        
        db.session.commit()
        for prod in addproducts:
            db.session.delete(prod)
        db.session.commit()
    
        db.session.delete(category)
        flash(f"The Category {category.name} was deleted from your database","success")
        db.session.commit()
        return redirect(url_for('categories'))
    flash(f"The Category {category.name} can't be  deleted from your database","warning")
    return redirect(url_for('categories'))



#specs################################


@app.route('/addspecs',methods=['GET','POST'])
def addspecs():
    categories = Category.query.all()
    if request.method =="POST":
        getcat=request.form.get('category')
        getspec = request.form.get('specs')
        spec = Specs(category_id=getcat,name=getspec)
        db.session.add(spec)
        flash(f'The specification {getspec} was added to your database','success')
        db.session.commit()
        return redirect(url_for('addspecs'))
    return render_template('products/addbrand.html', title='Add Specifications',categories=categories,spec='spec')


@app.route('/updatespec/<int:id>',methods=['GET','POST'])
def updatespec(id):
    if 'email' not in session:
        flash('Login first please','danger')
        return redirect(url_for('login'))
    updatespec = Specs.query.get_or_404(id)
    spec = request.form.get('specs')
    if request.method =="POST":
        updatespec.name = spec
        flash(f'The specification {updatespec.name} was changed to {spec}','success')
        db.session.commit()
        return redirect('/specs?category='+str(updatespec.category_id))
    spec = updatespec.name
    return render_template('products/addbrand.html', title='Update Specifications',updatespec=updatespec,getcat=Category.query.get_or_404(updatespec.category_id).name,spec='spec')


@app.route('/deletespec/<int:id>', methods=['GET','POST'])
def deletespec(id):
    spec = Specs.query.get_or_404(id)
    cat=spec.category_id
    spec_values = Specsvalues.query.filter_by(spec_id=id).all()
    if request.method=="POST":
        for spec_v in spec_values:
            db.session.delete(spec_v)
        db.session.commit()
        db.session.delete(spec)
        flash(f"The specification {spec.name} was deleted from your database","success")
        db.session.commit()
        return redirect('/specs?category='+str(cat))
    flash(f"The brand {spec.name} can't be  deleted from your database","warning")
    return redirect(url_for('specs'))

################################################


########subcategories############################

@app.route('/addsub',methods=['GET','POST'])
def addsub():
    categories = Category.query.all()
    if request.method =="POST":
        getcat=request.form.get('category')
        getsub = request.form.get('sub')
        sub = Subcategories(category_id=getcat,name=getsub)
        db.session.add(sub)
        flash(f'The Subcategory {getsub} was added to your database','success')
        db.session.commit()
        return redirect(url_for('addsub'))
    return render_template('products/addbrand.html', title='Add Subcategories',categories=categories)


@app.route('/updatesub/<int:id>',methods=['GET','POST'])
def updatesub(id):
    if 'email' not in session:
        flash('Login first please','danger')
        return redirect(url_for('login'))
    updatesub = Subcategories.query.get_or_404(id)
    sub = request.form.get('sub')
    if request.method =="POST":
        updatesub.name = sub
        flash(f'The Subcategory {updatesub.name} was changed to {sub}','success')
        db.session.commit()
        return redirect(url_for('sub'))
    sub = updatesub.name
    return render_template('products/addbrand.html', title='Update Subcategory',updatesub=updatesub,getcat=Category.query.get_or_404(updatesub.category_id).name)


@app.route('/deletesub/<int:id>', methods=['GET','POST'])
def deletesub(id):
    sub = Subcategories.query.get_or_404(id)
    if request.method=="POST":
        db.session.delete(sub)
        flash(f"The subcategory {sub.name} was deleted from your database","success")
        db.session.commit()
        return redirect(url_for('sub'))
    flash(f"The subcategory {sub.name} can't be  deleted from your database","warning")
    return redirect(url_for('sub'))



@app.route('/sub-options')
def spec_options():
    getcat=request.args.get('category')
    sub = Subcategories.query.filter_by(category_id=getcat).all()
    specs = Specs.query.filter_by(category_id=getcat).all()  
    spec_list=[] 
    for i in specs:    
        spec_list.append({'id':i.id,'name':i.name})  
    sub_list=[] 
    for i in sub:    
        sub_list.append({'id':i.id,'name':i.name})
    return jsonify({'sub_list':sub_list,'spec_list':spec_list})

########################################################

@app.route('/addproduct', methods=['GET','POST'])
def addproduct():
    form = Addproducts(request.form)
    brands = Brand.query.all()
    categories = Category.query.all()
    if request.method=="POST"and 'image_1' in request.files:
        name = form.name.data
        price = form.price.data
        discount = form.discount.data
        stock = form.stock.data
        colors = form.colors.data
        desc = form.description.data
        brand = request.form.get('brand')
        category = request.form.get('category')
        specs = request.form.getlist('specs')
        sub = request.form.get('sub')
        image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
        image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
        image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
        if sub:
            addproduct = Addproduct(name=name,price=price,discount=discount,stock=stock,colors=colors,desc=desc,category_id=category,subcategory_id=sub,brand_id=brand,image_1=image_1,image_2=image_2,image_3=image_3)
        else:
            addproduct = Addproduct(name=name,price=price,discount=discount,stock=stock,colors=colors,desc=desc,category_id=category,brand_id=brand,image_1=image_1,image_2=image_2,image_3=image_3)
        
        
        db.session.add(addproduct)
        db.session.flush()
        for i in specs:
            spec_val=Specsvalues(product_id=addproduct.id,category_id=category,spec_id=i,value='True')
            db.session.add(spec_val)
        flash(f'The product {name} was added in database','success')
        db.session.commit()
        return redirect(url_for('admin'))
    
    return render_template('products/addproduct.html', form=form, title='Add a Product', brands=brands,categories=categories)




@app.route('/updateproduct/<int:id>', methods=['GET','POST'])
def updateproduct(id):
    form = Addproducts(request.form)
    product = Addproduct.query.get_or_404(id)
    brands = Brand.query.all()
    categories = Category.query.all()
    brand = request.form.get('brand')
    category = request.form.get('category')
    subcategories=Subcategories
    sub = request.form.get('sub')

    spec_values= Specsvalues.query.filter_by(product_id=id).all()
    specs= Specs.query.filter_by(category_id=product.category_id).all()
    
    if request.method =="POST":
        product.name = form.name.data 
        product.price = form.price.data
        product.discount = form.discount.data
        product.stock = form.stock.data 
        product.colors = form.colors.data
        product.desc = form.description.data
        product.category_id = category
        product.brand_id = brand
        product.subcategory_id=sub
        for i in spec_values:
            db.session.delete(i)
        db.session.commit()
        sp=request.form.getlist('specs')
        for i in sp:
            spec_val=Specsvalues(product_id=id,category_id=category,spec_id=i,value='True')
            db.session.add(spec_val)

        if request.files.get('image_1'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
                product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
            except:
                product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
        if request.files.get('image_2'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
                product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
            except:
                product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
        if request.files.get('image_3'):
            try:
                os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
                product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
            except:
                product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")

        flash('The product was updated','success')
        db.session.commit()
        return redirect(url_for('admin'))
    form.name.data = product.name
    form.price.data = product.price
    form.discount.data = product.discount
    form.stock.data = product.stock
    form.colors.data = product.colors
    form.description.data = product.desc
    brand = product.brand.name
    category = product.category.name
    
    return render_template('products/addproduct.html', form=form, title='Update Product',getproduct=product, brands=brands,categories=categories,Specsvalues=Specsvalues,Specs=Specs,subcategories=subcategories)


@app.route('/deleteproduct/<int:id>', methods=['POST'])
def deleteproduct(id):
    product = Addproduct.query.get_or_404(id)
    events=Events.query.filter_by(product_id=id).all()
    spec_values=Specsvalues.query.filter_by(product_id=id).all()
    if request.method =="POST":
        try:
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
        except Exception as e:
            print(e)
        for e in events:
            db.session.delete(e)
        for sp in spec_values:
            db.session.delete(sp)
        db.session.delete(product)
        db.session.commit()
        flash(f'The product {product.name} was delete from your record','success')
        return redirect(url_for('admin'))
    flash(f'Can not delete the product','success')
    return redirect(url_for('admin'))