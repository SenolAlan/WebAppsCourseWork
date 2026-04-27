'''Script to populate the database with some initial data.
   In reality you would probably create a separate editor or a tool for importing data from elsewhere,
   but for CM1102 we'll just use this script to populate the database.'''

from DynamicWebsite import app, db, VinylsDb

# Bear in mind this script does NOT run the app
# instead we use app.app_context() which Flask provides to allow us to use the app's configuration and extensions
with app.app_context():
    db.create_all()
