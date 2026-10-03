import os, re, secrets
from datetime import datetime
from decimal import Decimal
from functools import wraps
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'falora-dev-secret-change-me')
db_url = os.getenv('DATABASE_URL', '')
if not db_url:
    if os.getenv('VERCEL'):
        db_url = 'sqlite:////tmp/falora.db'
    else:
        db_url = 'sqlite:///falora.db'
if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://','postgresql://',1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), nullable=False)
    email=db.Column(db.String(180), unique=True, nullable=False, index=True); password_hash=db.Column(db.String(255), nullable=False)
    role=db.Column(db.String(30), default='customer'); created_at=db.Column(db.DateTime, default=datetime.utcnow)
class Product(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(180), nullable=False); slug=db.Column(db.String(220), unique=True, nullable=False)
    category=db.Column(db.String(80), nullable=False, index=True); price=db.Column(db.Float, nullable=False); old_price=db.Column(db.Float)
    rating=db.Column(db.Float, default=4.8); reviews=db.Column(db.Integer, default=0); badge=db.Column(db.String(60), default='NEW')
    stock=db.Column(db.Integer, default=0); description=db.Column(db.Text, nullable=False); image=db.Column(db.Text, nullable=False)
    gallery=db.Column(db.Text, default=''); sizes=db.Column(db.String(255), default=''); colors=db.Column(db.String(255), default=''); featured=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
class Order(db.Model):
    id=db.Column(db.Integer, primary_key=True); order_no=db.Column(db.String(40), unique=True, nullable=False); user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_name=db.Column(db.String(120), nullable=False); email=db.Column(db.String(180), nullable=False); address=db.Column(db.Text, nullable=False)
    city=db.Column(db.String(100), nullable=False); postal_code=db.Column(db.String(30), nullable=False); payment=db.Column(db.String(50), nullable=False)
    subtotal=db.Column(db.Float, nullable=False); shipping=db.Column(db.Float, nullable=False); total=db.Column(db.Float, nullable=False)
    status=db.Column(db.String(40), default='Processing'); created_at=db.Column(db.DateTime, default=datetime.utcnow)
class OrderItem(db.Model):
    id=db.Column(db.Integer, primary_key=True); order_id=db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False); product_id=db.Column(db.Integer, nullable=False)
    name=db.Column(db.String(180), nullable=False); price=db.Column(db.Float, nullable=False); quantity=db.Column(db.Integer, nullable=False)

SEEDS=[
('Noir Velvet Handbag','bags',189,239,'BEST SELLER',18,4.9,128,'Sculptural velvet statement bag with polished hardware for elevated everyday and evening edits.','https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=1200&q=88',['Black','Plum'],'XS,S,M','Black,Plum',True),
('Aurelia Gold Watch','watches',329,399,'LIMITED',9,4.8,94,'Minimal dial, luminous details and a refined gold-tone finish for a timeless luxury profile.','https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=1200&q=88',['Gold'],'One Size','Gold',True),
('Luna Silk Heels','shoes',159,199,'NEW DROP',24,4.7,76,'Satin-finish heels with a refined silhouette, made for statement entrances and polished nights out.','https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=1200&q=88',['Ivory','Plum'],'36,37,38,39,40','Ivory,Plum',True),
('Obsidian Signature Shades','accessories',119,149,'TRENDING',31,4.8,63,'Bold oversized frames with a dark editorial finish for an instantly elevated look.','https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=1200&q=88',['Obsidian'],'One Size','Black',True),
('Amethyst Glow Serum','beauty',89,109,'GLOW PICK',42,4.9,211,'A luminous skincare essential presented in a jewel-inspired bottle for a premium night routine.','https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1200&q=88',['Violet'],'One Size','Violet',True),
('Velour Night Fragrance','beauty',145,179,'ICONIC',15,4.9,167,'Dark, sensual fragrance concept with an evening-ready character and premium bottle silhouette.','https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=1200&q=88',['Black'],'50ml,100ml','Black',True),
('Eclipse Leather Sneakers','shoes',139,169,'HOT',28,4.6,52,'Clean leather sneakers with a monochrome profile designed for luxury streetwear styling.','https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=88',['Black','White'],'36,37,38,39,40,41','Black,White',False),
('Royal Mini Tote','bags',209,259,"EDITOR'S PICK",12,4.8,88,'Compact structured tote with polished details and a rich editorial color story.','https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?auto=format&fit=crop&w=1200&q=88',['Plum','Black'],'Mini','Plum,Black',True),
('Celeste Pearl Set','accessories',129,159,'NEW',20,4.8,39,'Pearl-inspired jewelry set with luminous details for refined styling.','https://images.unsplash.com/photo-1611652022419-a9419f74343d?auto=format&fit=crop&w=1200&q=88',['Pearl'],'One Size','Pearl',False),
('Midnight Tailored Blazer','fashion',249,299,'FALORA EDIT',14,4.9,57,'Sharp tailoring with a dramatic midnight silhouette for polished occasions.','https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=1200&q=88',['Black'],'S,M,L,XL','Black',True),
('Nocturne Leather Boots','shoes',219,279,'RUNWAY',11,4.8,44,'Sleek leather boots with a sculpted profile and confident city finish.','https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=1200&q=88',['Black'],'36,37,38,39,40','Black',False),
('Violet Hour Candle','home',69,89,'MOOD',35,4.7,102,'A moody home fragrance accent designed around violet, amber and midnight woods.','https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=1200&q=88',['Violet'],'220g','Violet',False),
]

def slugify(x): return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-')
def product_dict(p):
    gallery=[p.image]+([x for x in p.gallery.split('|') if x] if p.gallery else [])
    return {'id':p.id,'name':p.name,'slug':p.slug,'category':p.category,'price':p.price,'old_price':p.old_price,'rating':p.rating,'reviews':p.reviews,'badge':p.badge,'stock':p.stock,'description':p.description,'image':p.image,'gallery':gallery,'sizes':[x for x in p.sizes.split(',') if x],'colors':[x for x in p.colors.split(',') if x],'featured':p.featured}
def seed():
    if Product.query.count(): return
    for name,cat,price,old,badge,stock,rating,reviews,desc,img,gal,sizes,colors,featured in SEEDS:
        db.session.add(Product(name=name,slug=slugify(name),category=cat,price=price,old_price=old,badge=badge,stock=stock,rating=rating,reviews=reviews,description=desc,image=img,gallery='|'.join(gal),sizes=sizes,colors=colors,featured=featured))
    if not User.query.filter_by(email='admin@falora.test').first(): db.session.add(User(name='Falora Admin',email='admin@falora.test',password_hash=generate_password_hash('Falora123!'),role='admin'))
    db.session.commit()
with app.app_context(): db.create_all(); seed()

def current_user():
    uid=session.get('user_id'); return db.session.get(User,uid) if uid else None
def admin_required(f):
    @wraps(f)
    def wrap(*a,**kw):
        u=current_user()
        if not u or u.role!='admin': return jsonify({'error':'Admin authentication required'}),403
        return f(*a,**kw)
    return wrap

@app.context_processor
def inject(): return {'current_user':current_user()}
@app.get('/')
def home(): return render_template('index.html')
@app.get('/shop')
def shop(): return render_template('shop.html')
@app.get('/product/<int:product_id>')
def product_page(product_id):
    p=db.session.get(Product,product_id)
    if not p: return render_template('404.html'),404
    related=Product.query.filter(Product.category==p.category,Product.id!=p.id).limit(4).all()
    return render_template('product.html',product=product_dict(p),related=[product_dict(x) for x in related])
@app.get('/login')
def login_page(): return render_template('auth.html',mode='login')
@app.get('/register')
def register_page(): return render_template('auth.html',mode='register')
@app.get('/cart')
def cart_page(): return render_template('cart.html')
@app.get('/checkout')
def checkout_page(): return render_template('checkout.html')
@app.get('/orders')
def orders_page(): return render_template('orders.html')
@app.get('/admin')
def admin_page(): return render_template('admin.html')

@app.get('/api/products')
def api_products():
    q=request.args.get('q','').strip(); cat=request.args.get('category','all'); sort=request.args.get('sort','featured');
    query=Product.query
    if q: query=query.filter(Product.name.ilike(f'%{q}%'))
    if cat!='all': query=query.filter_by(category=cat)
    if sort=='price-asc': query=query.order_by(Product.price.asc())
    elif sort=='price-desc': query=query.order_by(Product.price.desc())
    elif sort=='rating': query=query.order_by(Product.rating.desc())
    else: query=query.order_by(Product.featured.desc(),Product.created_at.desc())
    return jsonify([product_dict(x) for x in query.all()])
@app.get('/api/products/<int:pid>')
def api_product(pid):
    p=db.session.get(Product,pid)
    return (jsonify(product_dict(p)),200) if p else (jsonify({'error':'Product not found'}),404)
@app.post('/api/products')
@admin_required
def create_product():
    d=request.get_json() or {}; required=['name','category','price','description','image']
    if any(not d.get(k) for k in required): return jsonify({'error':'Missing required product fields'}),400
    p=Product(name=d['name'],slug=slugify(d['name'])+'-'+secrets.token_hex(2),category=d['category'],price=float(d['price']),old_price=float(d.get('old_price') or d['price']),badge=d.get('badge','NEW'),stock=int(d.get('stock',0)),rating=float(d.get('rating',5)),reviews=int(d.get('reviews',0)),description=d['description'],image=d['image'],gallery='|'.join(d.get('gallery',[])),sizes=','.join(d.get('sizes',[])),colors=','.join(d.get('colors',[])),featured=bool(d.get('featured',False)))
    db.session.add(p); db.session.commit(); return jsonify(product_dict(p)),201
@app.put('/api/products/<int:pid>')
@admin_required
def update_product(pid):
    p=db.session.get(Product,pid); d=request.get_json() or {}
    if not p:return jsonify({'error':'Product not found'}),404
    for k in ['name','category','badge','description','image']:
        if k in d:p.__setattr__(k,d[k])
    for k in ['price','old_price','rating']:
        if k in d:p.__setattr__(k,float(d[k]))
    for k in ['stock','reviews']:
        if k in d:p.__setattr__(k,int(d[k]))
    if 'sizes'in d:p.sizes=','.join(d['sizes'])
    if 'colors'in d:p.colors=','.join(d['colors'])
    if 'gallery'in d:p.gallery='|'.join(d['gallery'])
    if 'featured'in d:p.featured=bool(d['featured'])
    db.session.commit(); return jsonify(product_dict(p))
@app.delete('/api/products/<int:pid>')
@admin_required
def delete_product(pid):
    p=db.session.get(Product,pid)
    if not p:return jsonify({'error':'Product not found'}),404
    db.session.delete(p);db.session.commit();return jsonify({'ok':True})

@app.post('/api/auth/register')
def api_register():
    d=request.get_json() or {}; name=d.get('name','').strip(); email=d.get('email','').strip().lower(); password=d.get('password','')
    if not name or not email or len(password)<6:return jsonify({'error':'Name, valid email and password 6+ characters are required'}),400
    if User.query.filter_by(email=email).first():return jsonify({'error':'Email already registered'}),409
    u=User(name=name,email=email,password_hash=generate_password_hash(password));db.session.add(u);db.session.commit();session['user_id']=u.id
    return jsonify({'user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}),201
@app.post('/api/auth/login')
def api_login():
    d=request.get_json() or {};u=User.query.filter_by(email=d.get('email','').lower()).first()
    if not u or not check_password_hash(u.password_hash,d.get('password','')):return jsonify({'error':'Email or password is incorrect'}),401
    session['user_id']=u.id;return jsonify({'user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}})
@app.post('/api/auth/logout')
def api_logout(): session.clear();return jsonify({'ok':True})
@app.get('/api/auth/me')
def api_me():
    u=current_user();return jsonify({'user':({'id':u.id,'name':u.name,'email':u.email,'role':u.role} if u else None)})

@app.post('/api/orders')
def create_order():
    d=request.get_json() or {}; items=d.get('items',[])
    if not items:return jsonify({'error':'Cart is empty'}),400
    subtotal=0; prepared=[]
    for it in items:
        p=db.session.get(Product,int(it.get('id'))); qty=max(1,int(it.get('quantity',1)))
        if not p or p.stock<qty:return jsonify({'error':f'Product unavailable: {it.get("id")}'}),400
        subtotal+=p.price*qty;prepared.append((p,qty))
    shipping=0 if subtotal>=150 else 12;total=subtotal+shipping
    dflt=current_user(); name=d.get('customer_name') or (dflt.name if dflt else 'Guest Customer'); email=d.get('email') or (dflt.email if dflt else '')
    if not email or not d.get('address') or not d.get('city') or not d.get('postal_code'):return jsonify({'error':'Complete customer and shipping details'}),400
    order=Order(order_no='FLR-'+datetime.utcnow().strftime('%y%m%d')+'-'+secrets.token_hex(3).upper(),user_id=dflt.id if dflt else None,customer_name=name,email=email,address=d['address'],city=d['city'],postal_code=d['postal_code'],payment=d.get('payment','Card'),subtotal=subtotal,shipping=shipping,total=total)
    db.session.add(order);db.session.flush()
    for p,qty in prepared:
        p.stock-=qty;db.session.add(OrderItem(order_id=order.id,product_id=p.id,name=p.name,price=p.price,quantity=qty))
    db.session.commit();return jsonify({'order_no':order.order_no,'total':order.total,'status':order.status}),201
@app.get('/api/orders')
def get_orders():
    u=current_user()
    if not u:return jsonify({'error':'Login required'}),401
    orders=Order.query.filter_by(user_id=u.id).order_by(Order.created_at.desc()).all()
    return jsonify([{'order_no':o.order_no,'total':o.total,'status':o.status,'created_at':o.created_at.isoformat(),'payment':o.payment} for o in orders])

@app.errorhandler(404)
def nf(e):
    if request.path.startswith('/api/'):return jsonify({'error':'Not found'}),404
    return render_template('404.html'),404
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=True)

