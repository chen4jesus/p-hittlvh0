from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.contact import Message
from app.extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('pages/home.html')

@main_bp.route('/about')
def about():
    return render_template('pages/about.html')

@main_bp.route('/ministry')
def ministry():
    return render_template('pages/ministry.html')

@main_bp.route('/resources')
def resources():
    return render_template('pages/resources.html')

@main_bp.route('/tithing')
def tithing():
    return render_template('pages/tithing.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message_text = request.form.get('message')
        
        if name and email and message_text:
            new_message = Message(
                name=name,
                email=email,
                phone=phone,
                message=message_text
            )
            db.session.add(new_message)
            db.session.commit()
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('main.contact'))
        else:
            flash('Please fill in all required fields.', 'error')
            
    return render_template('pages/contact.html')
