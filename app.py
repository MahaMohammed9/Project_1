#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
# type: ignore
import os
import json
import sys
# from starter_code.config import SQLALCHEMY_DATABASE_URI
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Venue, Artist, Show    

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
db.init_app(app)
migrate=Migrate(app,db)


# ---------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format,locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
 venues = Venue.query.all()
 locals = []

 places = Venue.query.distinct(Venue.city, Venue.state).all()

 for place in places:
    locals.append({
        'city': place.city,
        'state': place.state,
        'venues': [{
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
        } for venue in venues if
            venue.city == place.city and venue.state == place.state]
    })
 return render_template('pages/venues.html', areas=locals)

#---

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')

  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response=[]

  for x in result:
    response.append({
      "id":x.id,
      "name":x.name
    })
  response={
        "count":len(result),
        "data":response
      }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

#---

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  if not venue:
    return render_template('errors/404.html')

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for sh in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id": sh.artist_id,
      "artist_name": sh.artist.name,
      "artist_image_link":sh.artist.image_link,
      "start_time": sh.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for sh in past_shows_query:
    past_shows.append({
      "artist_id": sh.artist_id,
      "artist_name": sh.artist.name,
      "artist_image_link": sh.artist.image_link,
      "start_time": sh.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False

  form = VenueForm()

  try:
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = ",".join(form.genres.data)
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website = form.website_link.data
    seeking_talent = True if 'seeking_talent' in form else False
    seeking_description = form.seeking_description.data

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()

    flash('Venue' + request.form['name'] + ' was successfully listed!!')
  except:
    error=False

    flash('There is an error. Venue ' + request.form['name']+ 'could not be listed!!')
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()    
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  if not error:
    flash(f'Venue {venue_id} was successfully deleted.')
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data= Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response=[]

  for x in result:
    response.append({
      "id":  x.id,
      "name":x.name
    })

  response={
        "count":len(result),
        "data":response
      }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_query = db.session.query(Artist).get(artist_id)

  if not artist_query:
    return render_template('errors/404.html')

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for sh in upcoming_shows_query:
    upcoming_shows.append({
      "venue_id": sh.venue_id,
      "venue_name": sh.venue.name,
      "venue_image_link": sh.venue.image_link,
      "start_time": sh.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time <datetime.now()).all()
  past_shows = []

  for sh in past_shows_query:
    past_shows.append({
      "venue_id": sh.venue_id,
      "venue_name": sh.venue.name,
      "venue_image_link": sh.venue.image_link,
      "start_time": sh.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  

  data = {
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": artist_query.genres,
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link
        
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  artist = Artist.query.get(artist_id)

  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('There is an error.Artist could not be changed!!')
  if not error:
  
    flash('Artist was successfully updated!!')
  return redirect(url_for('show_artist', artist_id=artist_id))

#-----

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue:
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  error=False
  up_venue=Venue.query.get(venue_id)

  try:

    up_venue.name=request.form.get('name')
    up_venue.city=request.form.get('city')
    up_venue.state=request.form.get('state')
    up_venue.address=request.form.get('address')
    up_venue.phone=request.form.get('phone')
    up_venue.genres = request.form.getlist('genres')
    up_venue.website_link= request.form.get('website_link')
    up_venue.image_link=request.form.get('image_link') 
    up_venue.facebook_link=request.form.get('facebook_link')
    up_venue.seeking_description=request.form.get('seeking_description')

    db.session.commit()  

  except:
    error=True
    flash('There is an error. Venue could not be edit!!')
    db.session.rollback()
  finally:
    db.session.close()
    flash("The venue has been updates")
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  ---------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  form = ArtistForm()

  try:
    name = form.name.data
    city = form.city.data
    phone = form.phone.data
    state = form.state.data
    genres = ",".join(form.genres.data)
    website = form.website_link.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    seeking_venue = True if 'seeking_venue' in form else False
    seeking_description = form.seeking_description.data

    artist = Artist(name=name, city=city, phone=phone, state=state, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('There is an error. Artist' + request.form['name']+ ' could not be listed!!')
  if not error:
    flash('Artist ' + request.form['name'] + 'was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows_query = db.session.query(Show).join(Artist).join(Venue).all()

  data = []
  for sh in shows_query:
    data.append({
      "venue_id": sh.venue_id,
      "venue_name": sh.venue.name,
      "artist_id": sh.artist_id,
      "artist_name": sh.artist.name,
      "artist_image_link": sh.artist.image_link,
      "start_time": sh.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False

  form = ShowForm()

  try:
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    print(request.form)

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!!')
  except:
    error = True

    flash('There is an error. Show could not be listed!!', 'error ')
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''