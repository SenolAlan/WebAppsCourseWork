from flask import Flask, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import *
from wtforms.validators import *
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vinyls.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)

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
    vinyl_stock = db.column(db.Integer)

class VinylForm(FlaskForm):
    vinyl_artist = StringField('Artist Name', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_name = StringField('Vinyl Name', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_genre = StringField('Vinyl Genre', validators = [DataRequired(), Length(min = 3, max = 30)])
    vinyl_year = IntegerField('Vinyl Year', validators = [data_required(), NumberRange(min = 1900, max = 2100)])
    vinyl_image = FileField('Vinyl Image', validators= [FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    vinyl_price = FloatField('Vinyl Price', validators = [NumberRange(min = 1, max = 2000)])
    vinyl_impact = StringField('Vinyl Impact', validators = [DataRequired(), Length(min = 0, max = 5)])
    vinyl_stock = IntegerField('Vinyl Stock', validators = [data_required(), NumberRange(min = 1, max = 100)])
    submit = SubmitField('Submit')

class RemoveVinylForm(FlaskForm):
    remove_id = IntegerField('Vinyl Id to Remove', validators = [DataRequired(), NumberRange(min = 1)])
    submit = SubmitField('Submit')
    
@app.route('/')
def index():
    vinyl = VinylsDb.query.all()
    lastest_vinyls = VinylsDb.query.order_by(VinylsDb.vinyl_id.desc()).limit(5).all()
    most_expensive = VinylsDb.query.order_by(VinylsDb.vinyl_price.desc()).limit(5).all()
    return render_template('index.html', vinyls = vinyl, latest = lastest_vinyls, expensive = most_expensive)

@app.route('/release/<int:id>')
def Vinyl(id):
    vinyl = VinylsDb.query.get_or_404(id)
    
    return render_template('release.html', vinyl = vinyl)

@app.route('/basket')
def basket():
    basket = session.get('basket', {})

    basket_items = []
    total = 0

    for id, quantity in basket.items():
        vinyl = VinylsDb.query.get(int(id))

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

    if id in basket:
        basket[id] += 1
    else:
        basket[id] = 1

    session['basket'] = basket
    session.modified = True

    return redirect('/')

@app.route('/basket/increase/<int:id>', methods=['POST'])
def increase(id):
    basket = session.get('basket', {})
    id = str(id)

    count = VinylsDb.query.filter_by(vinyl_id = id).count()

    if basket[id] <= count:
        basket[id] += 1
    else: 
        basket[id] = basket[id]
    session['basket'] = basket
    session.modified = True




@app.route('/add', methods=['GET', 'POST'])
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
            vinyl_price = form.vinyl_price.data
        )
        db.session.add(newVinyl)
        db.session.commit()
        return redirect('/')
    return render_template('add.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
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
