from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import *
from wtforms.validators import *
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    password_hash = db.Column(db.String(64))
    profile_picture = db.Column(db.String(64))
    balance = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def register(username, password, profile_picture):
        user = User(username = username)
        user.set_password(password)
        user.profile_picture = profile_picture
        user.balance = 0
        db.session.add(user)
        db.session.commit()
        return user

    def __repr__(self):
        return '<User {0}>'.format(self.username)

class VinylsDb(db.Model):
    __tablename__ = 'VinylsDb'
    vinyl_id = db.Column(db.Integer, primary_key=True)
    vinyl_artist = db.Column(db.String(32))
    vinyl_name = db.Column(db.String(16))
    vinyl_genre = db.Column(db.String(32))
    vinyl_year = db.Column(db.Integer)
    vinyl_image = db.Column(db.String(255))
    vinyl_price = db.Column(db.Float, nullable=True)
    vinyl_impact = db.Column(db.String(32))
    vinyl_stock = db.Column(db.Integer)
    vinyl_owner = db.Column(db.Integer)
    tracks = db.relationship('Track', backref='vinyl')

class VinylForm(FlaskForm):
    vinyl_artist = StringField('Artist Name', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_name = StringField('Vinyl Name', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_genre = StringField('Vinyl Genre', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_year = IntegerField('Vinyl Year', validators = [data_required(), NumberRange(min = 1900, max = 2100)])
    vinyl_image = FileField('Vinyl Image', validators= [DataRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    vinyl_price = FloatField('Vinyl Price', validators = [DataRequired(), NumberRange(min = 1, max = 2000)])
    vinyl_impact = StringField('Vinyl Impact', validators = [DataRequired(), Length(min = 0, max = 5)])
    vinyl_stock = IntegerField('Vinyl Stock', validators = [data_required(), NumberRange(min = 0, max = 100)])
    submit = SubmitField('Submit')

class RemoveVinylForm(FlaskForm):
    remove_id = IntegerField('Vinyl Id to Remove', validators = [DataRequired(), NumberRange(min = 1)])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 16)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 16)])
    password = PasswordField('Password', validators=[DataRequired()])
    profile_picture = FileField('Profile Picture', validators= [FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')

class Track(db.Model):
    __tablename__ = 'Track'
    id = db.Column(db.Integer, primary_key=True)
    track_name = db.Column(db.String(100), nullable=False)
    track_length = db.Column(db.String(10), nullable=False)  # e.g. "3:45"
    vinyl_id = db.Column(db.Integer, db.ForeignKey('VinylsDb.vinyl_id'), nullable=False)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash("Incorrect details")
            return redirect(url_for('login'))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form = form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username = form.username.data).first()
        if existing_user:
            return redirect(url_for('login'))
        profile_file = form.profile_picture.data
        profile_filename = None
        if profile_file:
            profile_filename = profile_file.filename
            profile_file.save(os.path.join('static/uploads/profile_pictures', profile_filename))
            user = User.register(form.username.data, form.password.data, profile_filename)
        else:
            user = User.register(form.username.data, form.password.data, 'Profile.png')
        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html', form = form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/protected')
@login_required
def protected():
    return render_template('protected.html')

@app.route('/profile')
@login_required
def profile():
    total_vinyls = VinylsDb.query.filter(VinylsDb.vinyl_owner == current_user.id).count()

    vinyl = VinylsDb.query.filter(VinylsDb.vinyl_owner == current_user.id)
    return render_template('profile.html', total_vinyls = total_vinyls, vinyl = vinyl)
    
@app.route('/', methods=['GET', 'POST'])
def index():
    vinyl = VinylsDb.query.all()
    lastest_vinyls = VinylsDb.query.order_by(VinylsDb.vinyl_id.desc()).limit(5).all()
    most_expensive = VinylsDb.query.order_by(VinylsDb.vinyl_price.desc()).limit(5).all()
    return render_template('index.html', vinyls = vinyl, latest = lastest_vinyls, expensive = most_expensive)

@app.route('/search')
def search():
    query = request.args.get("q", "")

    if query:
        results = VinylsDb.query.filter(db.or_(VinylsDb.vinyl_artist.ilike(f"%{query}%"), VinylsDb.vinyl_name.ilike(f"%{query}%"))).limit(15).all()
        return [{"img": v.vinyl_image, "id": v.vinyl_id, "name": v.vinyl_name, "artist": v.vinyl_artist, "impact": v.vinyl_impact, "id": v.vinyl_id} for v in results]
    
@app.route('/orderedSort')
def orderedSort():
    query = request.args.get("q", " ")
    order = request.args.get("order", "")
    selection = request.args.get("selection", "")

    results = VinylsDb.query.all()
    if query or order or selection:
        columns = {
            "price": VinylsDb.vinyl_price,
            "date": VinylsDb.vinyl_year,
            "name": VinylsDb.vinyl_artist,
            "impact": VinylsDb.vinyl_impact
        }
        column = columns.get(selection)
        base_query = results = VinylsDb.query.filter(db.or_(VinylsDb.vinyl_artist.ilike(f"%{query}%"), VinylsDb.vinyl_name.ilike(f"%{query}%")))

        if column:
            order = getattr(column, order)()
            base_query = base_query.order_by(order)

        results = base_query.all()
    return [{"img": v.vinyl_image, "id": v.vinyl_id, "name": v.vinyl_name, "artist": v.vinyl_artist, "impact": v.vinyl_impact, "id": v.vinyl_id, "price": v.vinyl_price} for v in results]

@app.route('/release/<int:id>')
def Vinyl(id):
    vinyl = VinylsDb.query.get_or_404(id)
    vinyl_owner = User.query.get(vinyl.vinyl_owner)
    return render_template('release.html', vinyl = vinyl, user = vinyl_owner)

@app.route('/basket')
def basket():
    basket = session.get('basket', {})

    basket_items = []
    total = 0

    for id, quantity in basket.items():
        vinyl = db.session.get(VinylsDb, int(id))

        if vinyl:
            subtotal = (vinyl.vinyl_price or 0) * quantity
            total += subtotal

            basket_items.append({
                "vinyl": vinyl,
                "quantity": quantity,
                "subtotal": subtotal
            })

    return render_template('basket.html', basket_items=basket_items, total=total)

@app.route('/basket/add/<int:id>')
def add_to_basket(id):
    basket = session.get('basket', {})
    id = str(id)
    vinyl = db.session.get(VinylsDb, int(id))

    if id in basket:
        if basket[id] < vinyl.vinyl_stock:
            basket[id] += 1
    else:
        basket[id] = 1

    session['basket'] = basket
    session.modified = True

    return redirect(request.referrer)

@app.route('/basket/increase/<int:id>', methods=['POST'])
def increase(id):
    basket = session.get('basket', {})
    id = str(id)
    vinyl = db.session.get(VinylsDb, int(id))

    if basket[id] < vinyl.vinyl_stock:
        basket[id] += 1
    elif basket[id] >= vinyl.vinyl_stock:
        basket[id] = vinyl.vinyl_stock
    session['basket'] = basket
    session.modified = True

    return redirect('/')

@app.route('/basket/decrease/<int:id>', methods=['POST'])
def decrease(id):
    basket = session.get('basket', {})
    id = str(id)
    vinyl = db.session.get(VinylsDb, int(id))

    if id in basket:
        if basket[id] <= 1:
            basket.pop(id)
        else:
            basket[id] -= 1

    session['basket'] = basket
    return redirect('/')
        
@app.route('/basket/remove/<int:id>', methods=['POST'])
def remove(id):
    basket = session.get('basket', {})
    id = str(id)
    vinyl = db.session.get(VinylsDb, int(id))

    if id in basket:
            basket.pop(id)
            
    session['basket'] = basket
    return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def AddVinyl():
    form = VinylForm()
    if form.validate_on_submit():
        image_file = form.vinyl_image.data
        image_filename = None
        if image_file:
            image_filename = image_file.filename
            image_file.save(os.path.join('static/uploads', image_filename))
        newVinyl = VinylsDb(
            vinyl_artist = form.vinyl_artist.data,
            vinyl_name = form.vinyl_name.data,
            vinyl_genre = form.vinyl_genre.data,
            vinyl_year = form.vinyl_year.data,
            vinyl_image = image_filename,
            vinyl_price = form.vinyl_price.data,
            vinyl_stock = form.vinyl_stock.data,
            vinyl_owner = current_user.id
        )
        db.session.add(newVinyl)
        db.session.commit()
        return redirect('/')
    return render_template('add.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def EditVinyl(id):
    vinyl = VinylsDb.query.get_or_404(id)
    form = VinylForm(obj = vinyl)
    if form.validate_on_submit():
        vinyl.vinyl_artist = form.vinyl_artist.data
        vinyl.vinyl_name = form.vinyl_name.data
        vinyl.vinyl_genre = form.vinyl_genre.data
        vinyl.vinyl_year = form.vinyl_year.data
        image_file = form.vinyl_image.data
        vinyl.vinyl_price = form.vinyl_price.data
        if image_file:
            image_filename = image_file.filename
            image_file.save(os.path.join('static/uploads', image_filename))
            vinyl.vinyl_image = image_filename
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', form = form, vinyl = vinyl)

@app.route('/remove', methods=['GET', 'POST'])
def RemoveVinyl():
    form = RemoveVinylForm()
    if form.validate_on_submit():
        VinylsDb.query.filter_by(vinyl_id = form.remove_id.data).delete()
        db.session.commit()
        return redirect('/')
    return render_template('remove.html', form=form)


if __name__ == '__main__':
    app.run(debug=True,port=5050)
